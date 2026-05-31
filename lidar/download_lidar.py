#!/usr/bin/env python3
"""
Download LIDAR LAZ tiles from WA DNR's LIDAR portal for Ellensburg Golf Club.

Uses the WA DNR ArcGIS REST API to query the tile index for the
Kittitas County 2011 FEMA LIDAR project, then downloads the LAZ files.
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlencode

try:
    import requests
except ImportError:
    print("ERROR: 'requests' package required. Install with: pip install requests")
    sys.exit(1)

LOG = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# WA DNR LIDAR Portal constants
# ---------------------------------------------------------------------------
# The WA DNR LIDAR portal exposes an ArcGIS MapServer.  The tile-index
# layer lists every LAZ tile with its bounding geometry and a download URL.
# Layer IDs can shift when DNR republishes; the script tries the well-known
# ones and falls back to a discovery step.

BASE_URL = "https://lidarportal.dnr.wa.gov/arcgis/rest/services"
# Primary service path — DNR has reorganized this a few times.
SERVICE_PATHS = [
    "Lidar/LidarTileIndex/MapServer",
    "Lidar/Tiles/MapServer",
    "Lidar_Downloads/MapServer",
]

# Default bounding box for Ellensburg Golf Club with ~500 m buffer
# Coordinates in WGS 84 (lon, lat)
DEFAULT_BBOX = {
    "xmin": -120.6400,
    "ymin":  47.0130,
    "xmax": -120.6180,
    "ymax":  47.0260,
}

# Project name substring used to filter tiles to the correct collection
PROJECT_FILTER = "Kittitas"

# How many features to request per page (ArcGIS default max is usually 1000)
PAGE_SIZE = 100

# Download retry / throttle
MAX_RETRIES = 3
RETRY_DELAY = 5        # seconds
CHUNK_SIZE  = 1 << 20  # 1 MiB


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_query_url(service_url: str, layer_id: int) -> str:
    return f"{service_url}/{layer_id}/query"


def _discover_layers(service_url: str) -> list[dict]:
    """Return the list of layer dicts from the MapServer."""
    url = f"{service_url}?f=json"
    LOG.debug("Discovering layers at %s", url)
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("layers", [])


def _find_tile_layer(service_url: str) -> int | None:
    """Heuristic: pick the first layer whose name looks like a tile index."""
    layers = _discover_layers(service_url)
    keywords = ["tile", "index", "laz", "lidar", "download"]
    for layer in layers:
        name_lower = layer.get("name", "").lower()
        if any(k in name_lower for k in keywords):
            LOG.info("Using layer %s – '%s'", layer["id"], layer["name"])
            return layer["id"]
    # Fallback: just use layer 0
    if layers:
        LOG.warning("No obvious tile layer found; falling back to layer 0 ('%s')", layers[0].get("name"))
        return layers[0]["id"]
    return None


def _resolve_service(session: requests.Session) -> tuple[str, int] | None:
    """Try known service paths and return (service_url, layer_id) or None."""
    for path in SERVICE_PATHS:
        service_url = f"{BASE_URL}/{path}"
        try:
            layer_id = _find_tile_layer(service_url)
            if layer_id is not None:
                return service_url, layer_id
        except Exception as exc:
            LOG.debug("Service path %s failed: %s", path, exc)
    return None


def query_tiles(
    service_url: str,
    layer_id: int,
    bbox: dict,
    project_filter: str | None = None,
    session: requests.Session | None = None,
) -> list[dict]:
    """
    Query the ArcGIS tile-index layer and return a list of feature dicts.

    Each feature is expected to have attributes including a download URL
    and a geometry envelope.
    """
    session = session or requests.Session()
    query_url = _build_query_url(service_url, layer_id)

    # Build a spatial query using an envelope in WGS 84
    geometry = json.dumps({
        "xmin": bbox["xmin"],
        "ymin": bbox["ymin"],
        "xmax": bbox["xmax"],
        "ymax": bbox["ymax"],
        "spatialReference": {"wkid": 4326},
    })

    where_clause = "1=1"
    if project_filter:
        # Try common field names for project name
        where_clause = (
            f"Project LIKE '%{project_filter}%' OR "
            f"ProjectName LIKE '%{project_filter}%' OR "
            f"Name LIKE '%{project_filter}%' OR "
            f"project_name LIKE '%{project_filter}%' OR "
            f"PROJECT LIKE '%{project_filter}%'"
        )

    all_features: list[dict] = []
    offset = 0

    while True:
        params = {
            "where": where_clause,
            "geometry": geometry,
            "geometryType": "esriGeometryEnvelope",
            "spatialRel": "esriSpatialRelIntersects",
            "inSR": 4326,
            "outFields": "*",
            "returnGeometry": "true",
            "f": "json",
            "resultOffset": offset,
            "resultRecordCount": PAGE_SIZE,
        }

        LOG.debug("Querying %s  offset=%d", query_url, offset)
        resp = session.get(query_url, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        if "error" in data:
            err = data["error"]
            code = err.get("code", "?")
            msg  = err.get("message", str(err))
            # If the WHERE clause failed (unknown field), retry without it
            if code == 400 and where_clause != "1=1":
                LOG.warning("Project filter failed (%s); retrying without filter", msg)
                where_clause = "1=1"
                offset = 0
                all_features.clear()
                continue
            raise RuntimeError(f"ArcGIS query error {code}: {msg}")

        features = data.get("features", [])
        all_features.extend(features)
        LOG.info("Fetched %d features (total so far: %d)", len(features), len(all_features))

        if len(features) < PAGE_SIZE:
            break
        offset += PAGE_SIZE

    return all_features


def _extract_download_url(feature: dict) -> str | None:
    """Pull the LAZ download URL from a feature's attributes."""
    attrs = feature.get("attributes", {})
    # DNR uses various field names for the download link
    for key in ("DownloadURL", "Download_URL", "download_url", "URL", "url",
                "LAS_URL", "LAZ_URL", "laz_url", "FileURL", "file_url",
                "DOWNLOAD", "download", "Link", "link"):
        val = attrs.get(key)
        if val and isinstance(val, str) and ("http" in val or val.startswith("//")):
            return val
    return None


def _extract_tile_name(feature: dict) -> str:
    """Derive a human-readable tile name from a feature."""
    attrs = feature.get("attributes", {})
    for key in ("TileName", "Tile_Name", "tile_name", "Name", "name",
                "FileName", "FILENAME", "filename", "OBJECTID", "FID"):
        val = attrs.get(key)
        if val is not None:
            return str(val)
    return "unknown_tile"


def download_file(url: str, dest: Path, session: requests.Session | None = None) -> bool:
    """Download *url* to *dest* with retries.  Returns True on success."""
    session = session or requests.Session()

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            LOG.info("Downloading %s  (attempt %d/%d)", url, attempt, MAX_RETRIES)
            resp = session.get(url, stream=True, timeout=120)
            resp.raise_for_status()

            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0

            with open(dest, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
                    fh.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded / total * 100
                        print(f"\r  {downloaded / 1e6:.1f} / {total / 1e6:.1f} MB  ({pct:.0f}%)", end="", flush=True)
                    else:
                        print(f"\r  {downloaded / 1e6:.1f} MB", end="", flush=True)
            print()  # newline after progress
            LOG.info("Saved %s (%d bytes)", dest, downloaded)
            return True

        except (requests.RequestException, IOError) as exc:
            LOG.warning("Attempt %d failed: %s", attempt, exc)
            if dest.exists():
                dest.unlink()
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)

    LOG.error("Failed to download %s after %d attempts", url, MAX_RETRIES)
    return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download LIDAR LAZ tiles from WA DNR for Ellensburg Golf Club."
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "data" / "laz",
        help="Directory to save LAZ files (default: ./data/laz)",
    )
    parser.add_argument(
        "--bbox",
        type=float,
        nargs=4,
        metavar=("XMIN", "YMIN", "XMAX", "YMAX"),
        default=None,
        help="Bounding box in WGS 84 (lon_min lat_min lon_max lat_max). "
             "Default: Ellensburg GC area with buffer.",
    )
    parser.add_argument(
        "--project-filter",
        default=PROJECT_FILTER,
        help="Substring to filter tiles by project name (default: %(default)s)",
    )
    parser.add_argument(
        "--no-project-filter",
        action="store_true",
        help="Disable project-name filtering (use spatial query only)",
    )
    parser.add_argument(
        "--service-url",
        default=None,
        help="Override the ArcGIS MapServer service URL",
    )
    parser.add_argument(
        "--layer-id",
        type=int,
        default=None,
        help="Override the layer ID within the MapServer",
    )
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="List available tiles without downloading",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Alias for --list-only",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (-v for INFO, -vv for DEBUG)",
    )

    args = parser.parse_args()

    # Logging setup
    level = logging.WARNING
    if args.verbose >= 2:
        level = logging.DEBUG
    elif args.verbose >= 1:
        level = logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    )

    list_only = args.list_only or args.dry_run

    bbox = dict(DEFAULT_BBOX)
    if args.bbox:
        bbox = {
            "xmin": args.bbox[0],
            "ymin": args.bbox[1],
            "xmax": args.bbox[2],
            "ymax": args.bbox[3],
        }

    project_filter = None if args.no_project_filter else args.project_filter

    session = requests.Session()
    session.headers.update({"User-Agent": "ellensburg-gc-lidar-downloader/1.0"})

    # Resolve service endpoint
    if args.service_url and args.layer_id is not None:
        service_url = args.service_url
        layer_id = args.layer_id
    else:
        print("Discovering WA DNR LIDAR tile-index service...")
        result = _resolve_service(session)
        if result is None:
            LOG.error(
                "Could not locate a tile-index service at %s. "
                "You may need to specify --service-url and --layer-id manually. "
                "Visit https://lidarportal.dnr.wa.gov to find the current endpoint.",
                BASE_URL,
            )
            return 1
        service_url, layer_id = result
        # Allow CLI overrides
        if args.service_url:
            service_url = args.service_url
        if args.layer_id is not None:
            layer_id = args.layer_id

    print(f"Service : {service_url}")
    print(f"Layer   : {layer_id}")
    print(f"Bbox    : {bbox}")
    print(f"Project : {project_filter or '(none)'}")
    print()

    # Query tile index
    print("Querying tile index...")
    features = query_tiles(service_url, layer_id, bbox, project_filter, session)

    if not features:
        print("No tiles found for the given area / project. Try:")
        print("  - Expanding the bounding box")
        print("  - Using --no-project-filter")
        print("  - Checking https://lidarportal.dnr.wa.gov manually")
        return 1

    print(f"Found {len(features)} tile(s).\n")

    # Build download list
    tiles: list[dict] = []
    for feat in features:
        url = _extract_download_url(feat)
        name = _extract_tile_name(feat)
        tiles.append({"name": name, "url": url, "attributes": feat.get("attributes", {})})

    # Display tile info
    for i, tile in enumerate(tiles, 1):
        url_display = tile["url"] or "(no URL found)"
        print(f"  [{i}] {tile['name']}  —  {url_display}")

    if list_only:
        print("\n(list-only mode; not downloading)")
        # Dump attributes of first tile for debugging
        if args.verbose and tiles:
            print("\nSample tile attributes:")
            for k, v in tiles[0]["attributes"].items():
                print(f"  {k}: {v}")
        return 0

    # Download
    args.output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nDownloading to {args.output_dir} ...\n")

    successes = 0
    failures  = 0
    skipped   = 0

    for i, tile in enumerate(tiles, 1):
        url = tile["url"]
        if not url:
            LOG.warning("Tile '%s' has no download URL — skipping", tile["name"])
            skipped += 1
            continue

        # Derive filename from URL or tile name
        filename = url.rsplit("/", 1)[-1]
        if not filename.lower().endswith((".laz", ".las", ".zip")):
            filename = f"{tile['name']}.laz"
        dest = args.output_dir / filename

        if dest.exists():
            LOG.info("Already exists: %s — skipping", dest)
            print(f"  [{i}/{len(tiles)}] {filename}  — already exists, skipping")
            skipped += 1
            continue

        print(f"  [{i}/{len(tiles)}] {filename}")
        ok = download_file(url, dest, session)
        if ok:
            successes += 1
        else:
            failures += 1

    print(f"\nDone: {successes} downloaded, {skipped} skipped, {failures} failed.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
