#!/usr/bin/env python3
"""
Process a raw DEM GeoTIFF into a 16-bit heightmap PNG for OPCD/Blender import.

Steps:
  1. Clip to course boundary (GeoJSON polygon)
  2. Fill NoData voids
  3. Smooth (light Gaussian — maintained turf, not raw terrain)
  4. Rescale elevations to 16-bit (0–65535)
  5. Export heightmap PNG + metadata JSON
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np

try:
    import rasterio
    from rasterio.mask import mask as rio_mask
    from rasterio.enums import Resampling
    from rasterio.transform import from_bounds
    from rasterio.warp import calculate_default_transform, reproject
except ImportError:
    print("ERROR: 'rasterio' package required. Install with: pip install rasterio")
    sys.exit(1)

try:
    from scipy.ndimage import gaussian_filter, uniform_filter
    from scipy.interpolate import NearestNDInterpolator
except ImportError:
    print("ERROR: 'scipy' package required. Install with: pip install scipy")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("ERROR: 'Pillow' package required. Install with: pip install Pillow")
    sys.exit(1)

try:
    import fiona
except ImportError:
    fiona = None  # We can fall back to json-based loading

LOG = logging.getLogger(__name__)

DEFAULT_BOUNDARY = Path(__file__).resolve().parent / "course_boundary.geojson"
DEFAULT_INPUT    = Path(__file__).resolve().parent / "data" / "dem_raw.tif"
DEFAULT_OUT_DIR  = Path(__file__).resolve().parent / "data"


# ---------------------------------------------------------------------------
# GeoJSON loading
# ---------------------------------------------------------------------------

def load_geojson_geometry(geojson_path: Path) -> list[dict]:
    """Load geometries from a GeoJSON file, returning a list of GeoJSON geometry dicts."""
    with open(geojson_path) as fh:
        gj = json.load(fh)

    geometries = []
    if gj.get("type") == "FeatureCollection":
        for feat in gj["features"]:
            geometries.append(feat["geometry"])
    elif gj.get("type") == "Feature":
        geometries.append(gj["geometry"])
    elif gj.get("type") in ("Polygon", "MultiPolygon"):
        geometries.append(gj)
    else:
        raise ValueError(f"Unsupported GeoJSON type: {gj.get('type')}")

    if not geometries:
        raise ValueError(f"No geometries found in {geojson_path}")

    return geometries


# ---------------------------------------------------------------------------
# Core processing
# ---------------------------------------------------------------------------

def fill_nodata(arr: np.ndarray, nodata: float) -> np.ndarray:
    """Fill NoData pixels using nearest-neighbor interpolation."""
    mask = np.isnan(arr) if np.isnan(nodata) else (arr == nodata)
    valid_count = np.count_nonzero(~mask)

    if valid_count == 0:
        raise ValueError("Entire raster is NoData — nothing to interpolate")

    if not np.any(mask):
        LOG.info("No NoData pixels to fill")
        return arr

    nodata_count = np.count_nonzero(mask)
    LOG.info("Filling %d NoData pixels (%.1f%% of raster)",
             nodata_count, nodata_count / arr.size * 100)

    # For small void counts, use scipy NearestNDInterpolator
    # For large rasters this is memory-hungry; fall back to iterative fill
    if arr.size < 50_000_000:  # ~50 Mpx
        rows, cols = np.where(~mask)
        values = arr[~mask]
        interp = NearestNDInterpolator(list(zip(rows, cols)), values)
        void_rows, void_cols = np.where(mask)
        arr[mask] = interp(void_rows, void_cols)
    else:
        # Iterative morphological fill: replace each NoData with mean of neighbors
        filled = arr.copy()
        for iteration in range(50):
            shifted = uniform_filter(np.where(mask, 0, filled), size=3)
            count   = uniform_filter((~mask).astype(float), size=3)
            update  = mask & (count > 0)
            filled[update] = shifted[update] / count[update]
            mask = mask & ~update
            if not np.any(mask):
                break
        arr = filled

    return arr


def smooth_dem(arr: np.ndarray, sigma: float = 1.0) -> np.ndarray:
    """Apply Gaussian smoothing.  sigma is in pixels."""
    LOG.info("Smoothing with Gaussian sigma=%.1f", sigma)
    return gaussian_filter(arr, sigma=sigma)


def rescale_to_uint16(arr: np.ndarray) -> tuple[np.ndarray, float, float]:
    """
    Linearly rescale array values to uint16 range [0, 65535].
    Returns (scaled_array, elev_min, elev_max).
    """
    elev_min = float(np.nanmin(arr))
    elev_max = float(np.nanmax(arr))
    elev_range = elev_max - elev_min

    LOG.info("Elevation range: %.2f – %.2f  (span %.2f)", elev_min, elev_max, elev_range)

    if elev_range < 1e-6:
        LOG.warning("Elevation range is near-zero; outputting flat heightmap")
        return np.zeros(arr.shape, dtype=np.uint16), elev_min, elev_max

    normalized = (arr - elev_min) / elev_range
    scaled = (normalized * 65535).clip(0, 65535).astype(np.uint16)
    return scaled, elev_min, elev_max


def clip_to_boundary(
    src_path: Path,
    geometries: list[dict],
    dst_path: Path,
) -> None:
    """Clip a raster to the given geometries, write to dst_path."""
    with rasterio.open(src_path) as src:
        # Reproject geometries if needed — assumes GeoJSON is WGS 84
        from rasterio.warp import transform_geom
        reprojected_geoms = []
        for geom in geometries:
            reprojected_geoms.append(
                transform_geom("EPSG:4326", src.crs, geom)
            )

        out_image, out_transform = rio_mask(
            src,
            reprojected_geoms,
            crop=True,
            filled=True,
            nodata=src.nodata if src.nodata is not None else -9999,
        )

        out_meta = src.meta.copy()
        out_meta.update({
            "driver": "GTiff",
            "height": out_image.shape[1],
            "width":  out_image.shape[2],
            "transform": out_transform,
            "compress": "lzw",
        })

        with rasterio.open(dst_path, "w", **out_meta) as dst:
            dst.write(out_image)

    LOG.info("Clipped raster saved to %s", dst_path)


def generate_heightmap(
    src_path: Path,
    out_png: Path,
    out_tif: Path,
    out_meta_json: Path,
    resolution: int = 4096,
    sigma: float = 1.0,
) -> None:
    """Read a clipped DEM, process it, and write heightmap + metadata."""
    with rasterio.open(src_path) as src:
        data = src.read(1)
        nodata = src.nodata if src.nodata is not None else -9999
        src_crs = src.crs
        src_bounds = src.bounds
        src_transform = src.transform
        src_res = src.res

    LOG.info("Input raster: %d x %d, CRS=%s", data.shape[1], data.shape[0], src_crs)
    LOG.info("Bounds: %s", src_bounds)

    # 1. Fill NoData
    data = fill_nodata(data, nodata)

    # 2. Smooth
    if sigma > 0:
        data = smooth_dem(data, sigma=sigma)

    # 3. Resample to target resolution
    LOG.info("Resampling to %d x %d", resolution, resolution)
    # Use bilinear resampling
    try:
        from skimage.transform import resize as sk_resize
        data_resized = sk_resize(
            data,
            (resolution, resolution),
            order=1,           # bilinear
            preserve_range=True,
            anti_aliasing=True,
        ).astype(np.float32)
    except ImportError:
        # Fallback: use scipy zoom
        from scipy.ndimage import zoom as scipy_zoom
        zoom_y = resolution / data.shape[0]
        zoom_x = resolution / data.shape[1]
        data_resized = scipy_zoom(data, (zoom_y, zoom_x), order=1).astype(np.float32)

    # 4. Rescale to 16-bit
    heightmap, elev_min, elev_max = rescale_to_uint16(data_resized)

    # 5. Save heightmap PNG (16-bit grayscale)
    LOG.info("Saving heightmap PNG: %s", out_png)
    img = Image.fromarray(heightmap)  # uint16 -> 16-bit grayscale PNG
    img.save(str(out_png))

    # 6. Save processed DEM as GeoTIFF (float32, properly georeferenced)
    new_transform = from_bounds(
        src_bounds.left, src_bounds.bottom,
        src_bounds.right, src_bounds.top,
        resolution, resolution,
    )
    out_tif_meta = {
        "driver": "GTiff",
        "dtype": "float32",
        "count": 1,
        "height": resolution,
        "width": resolution,
        "crs": src_crs,
        "transform": new_transform,
        "nodata": None,
        "compress": "lzw",
    }
    with rasterio.open(out_tif, "w", **out_tif_meta) as dst:
        dst.write(data_resized, 1)
    LOG.info("Saved processed DEM GeoTIFF: %s", out_tif)

    # 7. Save metadata JSON
    # Compute real-world dimensions
    width_m  = src_bounds.right - src_bounds.left
    height_m = src_bounds.top   - src_bounds.bottom

    metadata = {
        "source_file": str(src_path),
        "heightmap_png": str(out_png),
        "processed_tif": str(out_tif),
        "heightmap_resolution": resolution,
        "elevation_min_m": round(elev_min, 3),
        "elevation_max_m": round(elev_max, 3),
        "elevation_range_m": round(elev_max - elev_min, 3),
        "scale_factor": round(65535.0 / max(elev_max - elev_min, 1e-6), 6),
        "units_per_gray_level_m": round(max(elev_max - elev_min, 1e-6) / 65535.0, 8),
        "crs": str(src_crs),
        "bounds": {
            "left":   round(src_bounds.left, 6),
            "bottom": round(src_bounds.bottom, 6),
            "right":  round(src_bounds.right, 6),
            "top":    round(src_bounds.top, 6),
        },
        "real_world_width_m":  round(width_m, 2),
        "real_world_height_m": round(height_m, 2),
        "pixel_size_m": round(width_m / resolution, 4),
        "smoothing_sigma_px": sigma,
        "notes": (
            "Heightmap is 16-bit grayscale PNG. Gray value 0 = elevation_min_m, "
            "65535 = elevation_max_m. For Blender/OPCD import, set the displacement "
            "scale to elevation_range_m and position the mesh using the bounds."
        ),
    }

    with open(out_meta_json, "w") as fh:
        json.dump(metadata, fh, indent=2)
    LOG.info("Saved metadata: %s", out_meta_json)

    print(f"\nHeightmap generated successfully:")
    print(f"  PNG:      {out_png}")
    print(f"  GeoTIFF:  {out_tif}")
    print(f"  Metadata: {out_meta_json}")
    print(f"  Resolution:  {resolution} x {resolution}")
    print(f"  Elevation:   {elev_min:.2f} – {elev_max:.2f} m  (range {elev_max - elev_min:.2f} m)")
    print(f"  World size:  {width_m:.1f} x {height_m:.1f} m")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Process a raw DEM into a 16-bit heightmap for OPCD/Blender.",
    )
    parser.add_argument(
        "-i", "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="Input DEM GeoTIFF (default: %(default)s)",
    )
    parser.add_argument(
        "-b", "--boundary",
        type=Path,
        default=DEFAULT_BOUNDARY,
        help="Course boundary GeoJSON (default: %(default)s)",
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="Output directory (default: %(default)s)",
    )
    parser.add_argument(
        "-r", "--resolution",
        type=int,
        default=4096,
        choices=[1024, 2048, 4096, 8192],
        help="Heightmap resolution in pixels (default: 4096)",
    )
    parser.add_argument(
        "--sigma",
        type=float,
        default=1.0,
        help="Gaussian smoothing sigma in pixels (default: 1.0, set 0 to disable)",
    )
    parser.add_argument(
        "--skip-clip",
        action="store_true",
        help="Skip clipping to boundary (use full input raster)",
    )
    parser.add_argument(
        "--prefix",
        default="ellensburg_gc",
        help="Output filename prefix (default: %(default)s)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="count",
        default=0,
        help="Increase verbosity",
    )

    args = parser.parse_args()

    level = logging.WARNING
    if args.verbose >= 2:
        level = logging.DEBUG
    elif args.verbose >= 1:
        level = logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    )

    # Validate inputs
    if not args.input.exists():
        LOG.error("Input DEM not found: %s", args.input)
        print(f"ERROR: Input DEM not found: {args.input}")
        print("Run 'make dem' first to generate the raw DEM from LIDAR data.")
        return 1

    if not args.skip_clip and not args.boundary.exists():
        LOG.error("Boundary GeoJSON not found: %s", args.boundary)
        print(f"ERROR: Boundary GeoJSON not found: {args.boundary}")
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)

    clipped_tif = args.output_dir / f"{args.prefix}_dem_clipped.tif"
    out_png     = args.output_dir / f"{args.prefix}_heightmap_{args.resolution}.png"
    out_tif     = args.output_dir / f"{args.prefix}_dem_processed.tif"
    out_json    = args.output_dir / f"{args.prefix}_heightmap_meta.json"

    # Step 1: Clip (or use input directly)
    if args.skip_clip:
        processing_input = args.input
        print("Skipping boundary clip.")
    else:
        print(f"Clipping to boundary: {args.boundary}")
        geometries = load_geojson_geometry(args.boundary)
        clip_to_boundary(args.input, geometries, clipped_tif)
        processing_input = clipped_tif

    # Step 2-5: Process and generate heightmap
    print(f"Processing DEM -> heightmap ({args.resolution}x{args.resolution})...")
    generate_heightmap(
        src_path=processing_input,
        out_png=out_png,
        out_tif=out_tif,
        out_meta_json=out_json,
        resolution=args.resolution,
        sigma=args.sigma,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
