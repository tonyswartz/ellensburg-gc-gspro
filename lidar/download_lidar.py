#!/usr/bin/env python3
"""
Download LIDAR LAZ tiles from USGS National Map for Ellensburg Golf Club.

Uses the USGS TNM (The National Map) Access API to query and download
LiDAR Point Cloud (LAZ) tiles covering the Ellensburg GC area.

Two USGS datasets cover this area:
  - WA_EasternCascades_2019_B19  (2019, ~1 pt/m², preferred)
  - WA_KITTITASCOUNTY_2011       (2011 FEMA, legacy)

The script defaults to the 2019 dataset. Use --dataset 2011 for legacy data
or --dataset all to download both.

USGS TNM API docs: https://tnmaccess.nationalmap.gov/api/v1/docs
"""

import argparse
import json
import logging
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
# Constants
# ---------------------------------------------------------------------------

TNM_API_URL = "https://tnmaccess.nationalmap.gov/api/v1/products"

# Dataset identifiers as they appear in tile titles
DATASET_KEYS = {
    "2019": "WA_EasternCascades_2019_B19",
    "2011": "WA_KITTITASCOUNTY_2011",
}

# Default bounding box for Ellensburg GC with ~500 m buffer (WGS 84, lon/lat)
DEFAULT_BBOX = {
    "xmin": -120.6400,
    "ymin":  47.0130,
    "xmax": -120.6180,
    "ymax":  47.0260,
}

# Download settings
MAX_RETRIES = 3
RETRY_DELAY = 5         # seconds
CHUNK_SIZE  = 1 << 20  # 1 MiB


# ---------------------------------------------------------------------------
# USGS TNM query
# ---------------------------------------------------------------------------

def query_tnm(bbox: dict, session: requests.Session) -> list[dict]:
    """Query USGS TNM API for LiDAR Point Cloud tiles intersecting bbox.

    Returns a list of item dicts as returned by the API.
    """
    params = {
        "datasets": "Lidar Point Cloud (LPC)",
        "bbox": f"{bbox['xmin']},{bbox['ymin']},{bbox['xmax']},{bbox['ymax']}",
        "outputFormat": "JSON",
        "max": 100,
    }
    url = f"{TNM_API_URL}?{urlencode(params)}"
    LOG.debug("TNM query: %s", url)

    resp = session.get(url, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    items = data.get("items", [])
    LOG.info("TNM returned %d tile(s)", len(items))
    return items


def filter_by_dataset(items: list[dict], dataset: str) -> list[dict]:
    """Filter tile items to only those matching the requested dataset."""
    if dataset == "all":
        return items
    key = DATASET_KEYS.get(dataset)
    if key is None:
        LOG.warning("Unknown dataset key '%s'; returning all tiles", dataset)
        return items
    return [it for it in items if key in it.get("title", "")]


# ---------------------------------------------------------------------------
# Download helpers
# ---------------------------------------------------------------------------

def download_file(url: str, dest: Path, session: requests.Session) -> bool:
    """Download url to dest with retries. Returns True on success."""
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
                        print(
                            f"\r  {downloaded / 1e6:.1f} / {total / 1e6:.1f} MB"
                            f"  ({pct:.0f}%)",
                            end="",
                            flush=True,
                        )
                    else:
                        print(f"\r  {downloaded / 1e6:.1f} MB", end="", flush=True)

            print()
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
        description=(
            "Download LIDAR LAZ tiles from USGS National Map for Ellensburg Golf Club."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Datasets available for the Ellensburg GC area:
  2019  WA_EasternCascades_2019_B19  (~6 tiles, preferred — newer/denser)
  2011  WA_KITTITASCOUNTY_2011       (~4 tiles, legacy 2011 FEMA survey)
  all   Download both datasets

Examples:
  %(prog)s                         # download 2019 tiles (default)
  %(prog)s --dataset 2011          # download 2011 FEMA tiles
  %(prog)s --dataset all           # download everything
  %(prog)s --list-only -v          # list tiles without downloading
  %(prog)s --bbox -120.65 47.01 -120.61 47.03
""",
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "data" / "laz",
        help="Directory to save LAZ files (default: ./data/laz)",
    )
    parser.add_argument(
        "--dataset",
        choices=["2019", "2011", "all"],
        default="2019",
        help="Which USGS dataset to download (default: 2019)",
    )
    parser.add_argument(
        "--bbox",
        type=float,
        nargs=4,
        metavar=("XMIN", "YMIN", "XMAX", "YMAX"),
        default=None,
        help=(
            "Bounding box in WGS 84 (lon_min lat_min lon_max lat_max). "
            "Default: Ellensburg GC area with ~500 m buffer."
        ),
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

    # Logging
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
        xmin, ymin, xmax, ymax = args.bbox
        bbox = {"xmin": xmin, "ymin": ymin, "xmax": xmax, "ymax": ymax}

    session = requests.Session()
    session.headers.update({"User-Agent": "ellensburg-gc-lidar-downloader/2.0"})

    print("Querying USGS National Map for LiDAR tiles...")
    print(f"  Bbox    : {bbox['xmin']}, {bbox['ymin']}, {bbox['xmax']}, {bbox['ymax']}")
    print(f"  Dataset : {args.dataset}")
    print()

    all_items = query_tnm(bbox, session)
    items = filter_by_dataset(all_items, args.dataset)

    if not items:
        print(f"No tiles found for dataset='{args.dataset}' in the given area.")
        print("All items returned by TNM:")
        for it in all_items:
            print(f"  {it.get('title', '?')}")
        print("\nTry --dataset all or expand the bounding box.")
        return 1

    total_mb = sum(it.get("sizeInBytes", 0) for it in items) / 1e6
    print(f"Found {len(items)} tile(s)  ({total_mb:.0f} MB total)\n")

    for i, item in enumerate(items, 1):
        title = item.get("title", "?")
        url   = item.get("downloadURL", "")
        size  = item.get("sizeInBytes", 0)
        pub   = item.get("publicationDate", "?")
        print(f"  [{i}] {title}")
        print(f"       {size / 1e6:.1f} MB  published {pub}")
        print(f"       {url}")

    if list_only:
        print("\n(list-only mode; not downloading)")
        return 0

    # Download
    args.output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nDownloading to: {args.output_dir}\n")

    successes = failures = skipped = 0

    for i, item in enumerate(items, 1):
        url = item.get("downloadURL", "")
        if not url:
            LOG.warning("Item '%s' has no downloadURL — skipping", item.get("title"))
            skipped += 1
            continue

        filename = url.rsplit("/", 1)[-1]
        if not filename.lower().endswith((".laz", ".las")):
            filename = item.get("title", f"tile_{i}").replace(" ", "_") + ".laz"
        dest = args.output_dir / filename

        if dest.exists():
            existing_size = dest.stat().st_size
            expected_size = item.get("sizeInBytes", 0)
            if expected_size and abs(existing_size - expected_size) < 1024:
                print(f"  [{i}/{len(items)}] {filename}  — already complete, skipping")
                skipped += 1
                continue
            else:
                LOG.warning(
                    "Existing file size mismatch (%d vs %d bytes) — re-downloading",
                    existing_size,
                    expected_size,
                )

        print(f"  [{i}/{len(items)}] {filename}  ({item.get('sizeInBytes', 0) / 1e6:.1f} MB)")
        ok = download_file(url, dest, session)
        if ok:
            successes += 1
        else:
            failures += 1

    print(f"\nDone: {successes} downloaded, {skipped} skipped, {failures} failed.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
