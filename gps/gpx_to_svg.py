#!/usr/bin/env python3
"""
gpx_to_svg.py — Convert GPS tracks (GPX) to Inkscape SVG spline paths for OPCD.

Converts GPX track segments and waypoints into smooth cubic Bezier spline paths
organized into named layers compatible with the Open Platform Course Designer (OPCD)
for GS Pro golf simulator course building.

Usage:
    python gpx_to_svg.py input.gpx -o course.svg
    python gpx_to_svg.py ./gpx_folder/ -o course.svg --scale 5.0
    python gpx_to_svg.py track.gpx -o out.svg --feature-type fairway-left --hole 3
"""

import argparse
import glob
import logging
import math
import os
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# UTM Zone 10N parameters (EPSG:32610) — covers Ellensburg, WA
UTM_ZONE = 10
UTM_FALSE_EASTING = 500000.0
UTM_FALSE_NORTHING = 0.0
UTM_SCALE_FACTOR = 0.9996
UTM_A = 6378137.0  # WGS84 semi-major axis
UTM_F = 1 / 298.257223563  # WGS84 flattening
UTM_E2 = 2 * UTM_F - UTM_F ** 2  # eccentricity squared

# Default course center (Ellensburg Golf Club)
DEFAULT_CENTER_LAT = 47.0193
DEFAULT_CENTER_LON = -120.6294

# SVG canvas
SVG_CANVAS_SIZE = 2000

# OPCD feature types → layer name, stroke color, stroke width
FEATURE_CONFIG = {
    "fairway-left":  {"layer": "Fairway",  "color": "#4CAF50", "width": 2.0},
    "fairway-right": {"layer": "Fairway",  "color": "#4CAF50", "width": 2.0},
    "green-edge":    {"layer": "Green",    "color": "#2E7D32", "width": 2.0},
    "bunker-edge":   {"layer": "Bunker",   "color": "#D2B48C", "width": 2.0},
    "tee-box":       {"layer": "Tee",      "color": "#1565C0", "width": 2.0},
    "cart-path":     {"layer": "CartPath", "color": "#9E9E9E", "width": 1.5},
    "ob-line":       {"layer": "OB",       "color": "#F44336", "width": 2.5},
    "water-edge":    {"layer": "Water",    "color": "#1E88E5", "width": 2.0},
    "tree-line":     {"layer": "Trees",    "color": "#1B5E20", "width": 1.5},
    "rough-edge":    {"layer": "Rough",    "color": "#7CB342", "width": 1.5},
}

# All known OPCD layer names (in render order, bottom to top)
OPCD_LAYERS = [
    "Rough", "Fairway", "Green", "Bunker", "Tee",
    "CartPath", "Water", "Trees", "OB",
]

GPX_NS = "http://www.topografix.com/GPX/1/1"
GPX_NS_10 = "http://www.topografix.com/GPX/1/0"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Point:
    x: float
    y: float


@dataclass
class GpxTrackSegment:
    name: str
    points: List[Point] = field(default_factory=list)
    feature_type: Optional[str] = None
    hole: Optional[int] = None


@dataclass
class GpxWaypoint:
    name: str
    point: Point
    description: str = ""


# ---------------------------------------------------------------------------
# UTM projection (pure Python, no external deps)
# ---------------------------------------------------------------------------

def _latlon_to_utm(lat_deg: float, lon_deg: float) -> Tuple[float, float]:
    """Convert WGS84 lat/lon (degrees) to UTM Zone 10N easting/northing (meters)."""
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    lon0 = math.radians((UTM_ZONE - 1) * 6 - 180 + 3)  # central meridian

    e2 = UTM_E2
    e_prime2 = e2 / (1 - e2)
    a = UTM_A
    k0 = UTM_SCALE_FACTOR

    sin_lat = math.sin(lat)
    cos_lat = math.cos(lat)
    tan_lat = math.tan(lat)

    N = a / math.sqrt(1 - e2 * sin_lat ** 2)
    T = tan_lat ** 2
    C = e_prime2 * cos_lat ** 2
    A = cos_lat * (lon - lon0)

    # Meridional arc
    M = a * (
        (1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256) * lat
        - (3 * e2 / 8 + 3 * e2 ** 2 / 32 + 45 * e2 ** 3 / 1024) * math.sin(2 * lat)
        + (15 * e2 ** 2 / 256 + 45 * e2 ** 3 / 1024) * math.sin(4 * lat)
        - (35 * e2 ** 3 / 3072) * math.sin(6 * lat)
    )

    easting = UTM_FALSE_EASTING + k0 * N * (
        A
        + (1 - T + C) * A ** 3 / 6
        + (5 - 18 * T + T ** 2 + 72 * C - 58 * e_prime2) * A ** 5 / 120
    )

    northing = UTM_FALSE_NORTHING + k0 * (
        M
        + N * tan_lat * (
            A ** 2 / 2
            + (5 - T + 9 * C + 4 * C ** 2) * A ** 4 / 24
            + (61 - 58 * T + T ** 2 + 600 * C - 330 * e_prime2) * A ** 6 / 720
        )
    )

    return easting, northing


# ---------------------------------------------------------------------------
# Ramer-Douglas-Peucker simplification
# ---------------------------------------------------------------------------

def _perpendicular_distance(pt: Point, line_start: Point, line_end: Point) -> float:
    dx = line_end.x - line_start.x
    dy = line_end.y - line_start.y
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        return math.hypot(pt.x - line_start.x, pt.y - line_start.y)
    t = max(0, min(1, ((pt.x - line_start.x) * dx + (pt.y - line_start.y) * dy) / length_sq))
    proj_x = line_start.x + t * dx
    proj_y = line_start.y + t * dy
    return math.hypot(pt.x - proj_x, pt.y - proj_y)


def simplify_rdp(points: List[Point], epsilon: float) -> List[Point]:
    """Ramer-Douglas-Peucker point simplification."""
    if len(points) < 3 or epsilon <= 0:
        return points

    max_dist = 0.0
    max_idx = 0
    for i in range(1, len(points) - 1):
        d = _perpendicular_distance(points[i], points[0], points[-1])
        if d > max_dist:
            max_dist = d
            max_idx = i

    if max_dist > epsilon:
        left = simplify_rdp(points[: max_idx + 1], epsilon)
        right = simplify_rdp(points[max_idx:], epsilon)
        return left[:-1] + right
    else:
        return [points[0], points[-1]]


# ---------------------------------------------------------------------------
# Catmull-Rom → Cubic Bezier conversion
# ---------------------------------------------------------------------------

def _catmull_rom_to_bezier(
    p0: Point, p1: Point, p2: Point, p3: Point, alpha: float = 0.5
) -> Tuple[Point, Point, Point, Point]:
    """Convert four Catmull-Rom control points to a cubic Bezier segment (p1→p2).

    alpha=0.5 gives centripetal parameterisation (less cusps than uniform).
    Returns (start, cp1, cp2, end) for the Bezier.
    """
    def _t(ti: float, pi: Point, pj: Point) -> float:
        dx = pj.x - pi.x
        dy = pj.y - pi.y
        return ((dx * dx + dy * dy) ** 0.5) ** alpha + ti

    t0 = 0.0
    t1 = _t(t0, p0, p1)
    t2 = _t(t1, p1, p2)
    t3 = _t(t2, p2, p3)

    # Avoid division by zero on coincident points
    if t1 == t0 or t2 == t1 or t3 == t2 or t2 == t0 or t3 == t1:
        # Degenerate — just use linear interpolation
        cp1 = Point(
            p1.x + (p2.x - p1.x) / 3,
            p1.y + (p2.y - p1.y) / 3,
        )
        cp2 = Point(
            p2.x - (p2.x - p1.x) / 3,
            p2.y - (p2.y - p1.y) / 3,
        )
        return (p1, cp1, cp2, p2)

    # Tangent at p1
    d1x = (p1.x - p0.x) / (t1 - t0) - (p2.x - p0.x) / (t2 - t0) + (p2.x - p1.x) / (t2 - t1)
    d1y = (p1.y - p0.y) / (t1 - t0) - (p2.y - p0.y) / (t2 - t0) + (p2.y - p1.y) / (t2 - t1)

    # Tangent at p2
    d2x = (p2.x - p1.x) / (t2 - t1) - (p3.x - p1.x) / (t3 - t1) + (p3.x - p2.x) / (t3 - t2)
    d2y = (p2.y - p1.y) / (t2 - t1) - (p3.y - p1.y) / (t3 - t1) + (p3.y - p2.y) / (t3 - t2)

    seg_len = t2 - t1
    cp1 = Point(p1.x + d1x * seg_len / 3, p1.y + d1y * seg_len / 3)
    cp2 = Point(p2.x - d2x * seg_len / 3, p2.y - d2y * seg_len / 3)

    return (p1, cp1, cp2, p2)


def points_to_bezier_path(points: List[Point]) -> str:
    """Convert a list of points into an SVG cubic Bezier path string (M ... C ...)."""
    if len(points) < 2:
        if len(points) == 1:
            return f"M {points[0].x:.2f},{points[0].y:.2f}"
        return ""

    if len(points) == 2:
        return (
            f"M {points[0].x:.2f},{points[0].y:.2f} "
            f"L {points[1].x:.2f},{points[1].y:.2f}"
        )

    # Build padded list for Catmull-Rom (mirror first/last)
    padded = [points[0]] + points + [points[-1]]

    parts = [f"M {points[0].x:.2f},{points[0].y:.2f}"]
    for i in range(len(points) - 1):
        p0 = padded[i]
        p1 = padded[i + 1]
        p2 = padded[i + 2]
        p3 = padded[i + 3]
        _, cp1, cp2, end = _catmull_rom_to_bezier(p0, p1, p2, p3)
        parts.append(
            f"C {cp1.x:.2f},{cp1.y:.2f} {cp2.x:.2f},{cp2.y:.2f} {end.x:.2f},{end.y:.2f}"
        )

    return " ".join(parts)


# ---------------------------------------------------------------------------
# GPX parsing
# ---------------------------------------------------------------------------

def _detect_gpx_namespace(root: ET.Element) -> str:
    """Return the GPX namespace URI from the root element tag."""
    tag = root.tag
    if tag.startswith("{"):
        return tag[1 : tag.index("}")]
    return ""


def parse_gpx(
    filepath: str,
    center_easting: float,
    center_northing: float,
    scale: float,
    canvas: float,
    feature_type_override: Optional[str] = None,
    hole_override: Optional[int] = None,
) -> Tuple[List[GpxTrackSegment], List[GpxWaypoint]]:
    """Parse a GPX file into track segments and waypoints, projected to SVG coords."""
    logger.info("Parsing GPX file: %s", filepath)

    tree = ET.parse(filepath)
    root = tree.getroot()
    ns = _detect_gpx_namespace(root)
    nsmap = {"g": ns} if ns else {}

    def _find(el: ET.Element, tag: str):
        if ns:
            return el.findall(f"g:{tag}", nsmap)
        return el.findall(tag)

    def _find1(el: ET.Element, tag: str):
        if ns:
            return el.find(f"g:{tag}", nsmap)
        return el.find(tag)

    def _project(lat: float, lon: float) -> Point:
        e, n = _latlon_to_utm(lat, lon)
        # Translate so course center is at canvas center, then scale
        x = (e - center_easting) * scale + canvas / 2
        y = canvas / 2 - (n - center_northing) * scale  # flip Y for SVG
        return Point(x, y)

    segments: List[GpxTrackSegment] = []
    waypoints: List[GpxWaypoint] = []

    # Parse tracks
    for trk in _find(root, "trk"):
        name_el = _find1(trk, "name")
        track_name = name_el.text.strip() if name_el is not None and name_el.text else "unnamed"
        logger.debug("  Track: %s", track_name)

        # Determine feature type and hole from track name or overrides
        feat_type, hole_num = _parse_feature_name(track_name)
        if feature_type_override:
            feat_type = feature_type_override
        if hole_override is not None:
            hole_num = hole_override

        for trkseg in _find(trk, "trkseg"):
            pts: List[Point] = []
            for trkpt in _find(trkseg, "trkpt"):
                lat = float(trkpt.get("lat", "0"))
                lon = float(trkpt.get("lon", "0"))
                pts.append(_project(lat, lon))

            if pts:
                seg = GpxTrackSegment(
                    name=track_name,
                    points=pts,
                    feature_type=feat_type,
                    hole=hole_num,
                )
                segments.append(seg)
                logger.debug("    Segment with %d points, feature=%s, hole=%s",
                             len(pts), feat_type, hole_num)

    # Parse waypoints
    for wpt in _find(root, "wpt"):
        lat = float(wpt.get("lat", "0"))
        lon = float(wpt.get("lon", "0"))
        name_el = _find1(wpt, "name")
        desc_el = _find1(wpt, "desc")
        wpt_name = name_el.text.strip() if name_el is not None and name_el.text else "waypoint"
        wpt_desc = desc_el.text.strip() if desc_el is not None and desc_el.text else ""
        waypoints.append(GpxWaypoint(
            name=wpt_name,
            point=_project(lat, lon),
            description=wpt_desc,
        ))

    logger.info("  Found %d track segments, %d waypoints", len(segments), len(waypoints))
    return segments, waypoints


def _parse_feature_name(name: str) -> Tuple[Optional[str], Optional[int]]:
    """Extract feature type and hole number from a track name like 'fairway-left-3'."""
    name = name.strip().lower()

    # Try matching known feature types
    best_match = None
    best_len = 0
    for ft in FEATURE_CONFIG:
        if name.startswith(ft) and len(ft) > best_len:
            best_match = ft
            best_len = len(ft)

    hole_num = None
    if best_match:
        remainder = name[best_len:].strip("-_ ")
        if remainder.isdigit():
            hole_num = int(remainder)
    else:
        # Try to extract trailing number anyway
        parts = name.rsplit("-", 1)
        if len(parts) == 2 and parts[1].isdigit():
            hole_num = int(parts[1])

    return best_match, hole_num


# ---------------------------------------------------------------------------
# SVG generation
# ---------------------------------------------------------------------------

INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"
SODIPODI_NS = "http://sodipodi.sourceforge.net/DTD/sodipodi-0.0.dtd"
SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"


def _build_svg(
    segments: List[GpxTrackSegment],
    waypoints: List[GpxWaypoint],
    canvas: float,
    simplify_tolerance: float,
    smooth: bool,
) -> str:
    """Build an Inkscape-compatible SVG string from parsed GPX data."""

    # Organise segments by OPCD layer, then by hole
    layer_data: dict = {}  # layer_name → list of (segment, config)
    for seg in segments:
        cfg = FEATURE_CONFIG.get(seg.feature_type or "", None)
        if cfg is None:
            # Default to Rough layer for unknown types
            cfg = {"layer": "Rough", "color": "#7CB342", "width": 1.5}
            logger.warning("Unknown feature type '%s' for track '%s'; defaulting to Rough layer",
                           seg.feature_type, seg.name)
        layer_name = cfg["layer"]
        layer_data.setdefault(layer_name, []).append((seg, cfg))

    # Start building SVG
    lines: List[str] = []
    lines.append('<?xml version="1.0" encoding="UTF-8" standalone="no"?>')
    lines.append(
        f'<svg\n'
        f'   xmlns="{SVG_NS}"\n'
        f'   xmlns:inkscape="{INKSCAPE_NS}"\n'
        f'   xmlns:sodipodi="{SODIPODI_NS}"\n'
        f'   xmlns:xlink="{XLINK_NS}"\n'
        f'   width="{canvas:.0f}"\n'
        f'   height="{canvas:.0f}"\n'
        f'   viewBox="0 0 {canvas:.0f} {canvas:.0f}"\n'
        f'   id="svg_root"\n'
        f'   version="1.1">'
    )

    # Sodipodi namedview (Inkscape canvas metadata)
    lines.append(
        f'  <sodipodi:namedview\n'
        f'     id="namedview1"\n'
        f'     pagecolor="#ffffff"\n'
        f'     bordercolor="#000000"\n'
        f'     borderopacity="0.25"\n'
        f'     inkscape:showpageshadow="2"\n'
        f'     inkscape:pageopacity="0.0"\n'
        f'     inkscape:deskcolor="#d1d1d1"\n'
        f'     inkscape:document-units="px"\n'
        f'     inkscape:zoom="0.5"\n'
        f'     inkscape:cx="{canvas / 2:.0f}"\n'
        f'     inkscape:cy="{canvas / 2:.0f}" />'
    )

    # Defs (empty, but Inkscape expects it)
    lines.append('  <defs id="defs1" />')

    # Create layers in OPCD order
    layer_id_counter = 1
    for layer_name in OPCD_LAYERS:
        visible = "true" if layer_name in layer_data else "true"
        lines.append(
            f'  <g\n'
            f'     inkscape:groupmode="layer"\n'
            f'     id="layer{layer_id_counter}"\n'
            f'     inkscape:label="{layer_name}"\n'
            f'     style="display:inline">'
        )

        if layer_name in layer_data:
            # Group by hole number
            hole_groups: dict = {}  # hole_num → list of (seg, cfg)
            for seg, cfg in layer_data[layer_name]:
                h = seg.hole if seg.hole is not None else 0
                hole_groups.setdefault(h, []).append((seg, cfg))

            for hole_num in sorted(hole_groups.keys()):
                hole_label = f"Hole {hole_num}" if hole_num > 0 else "General"
                lines.append(
                    f'    <g id="{layer_name.lower()}_hole{hole_num}" '
                    f'inkscape:label="{hole_label}">'
                )

                for seg, cfg in hole_groups[hole_num]:
                    pts = seg.points

                    # Simplify
                    if simplify_tolerance > 0 and len(pts) > 3:
                        original_count = len(pts)
                        pts = simplify_rdp(pts, simplify_tolerance)
                        logger.debug("    Simplified '%s': %d → %d points",
                                     seg.name, original_count, len(pts))

                    # Build path
                    if smooth and len(pts) >= 3:
                        path_d = points_to_bezier_path(pts)
                    else:
                        # Polyline fallback
                        parts = [f"M {pts[0].x:.2f},{pts[0].y:.2f}"]
                        for p in pts[1:]:
                            parts.append(f"L {p.x:.2f},{p.y:.2f}")
                        path_d = " ".join(parts)

                    color = cfg["color"]
                    width = cfg["width"]
                    safe_id = seg.name.replace(" ", "_").replace("/", "_")
                    lines.append(
                        f'      <path\n'
                        f'         id="path_{safe_id}"\n'
                        f'         inkscape:label="{seg.name}"\n'
                        f'         style="fill:none;stroke:{color};stroke-width:{width};'
                        f'stroke-linecap:round;stroke-linejoin:round;stroke-opacity:1"\n'
                        f'         d="{path_d}" />'
                    )

                lines.append('    </g>')

        lines.append('  </g>')
        layer_id_counter += 1

    # Waypoints layer
    if waypoints:
        lines.append(
            f'  <g\n'
            f'     inkscape:groupmode="layer"\n'
            f'     id="layer{layer_id_counter}"\n'
            f'     inkscape:label="Waypoints"\n'
            f'     style="display:inline">'
        )
        for wpt in waypoints:
            safe_id = wpt.name.replace(" ", "_").replace("/", "_")
            lines.append(
                f'    <circle\n'
                f'       id="wpt_{safe_id}"\n'
                f'       inkscape:label="{wpt.name}"\n'
                f'       cx="{wpt.point.x:.2f}"\n'
                f'       cy="{wpt.point.y:.2f}"\n'
                f'       r="5"\n'
                f'       style="fill:#FF5722;stroke:#BF360C;stroke-width:1" />'
            )
            # Label
            lines.append(
                f'    <text\n'
                f'       x="{wpt.point.x + 8:.2f}"\n'
                f'       y="{wpt.point.y + 4:.2f}"\n'
                f'       style="font-size:10px;fill:#BF360C;font-family:sans-serif">'
                f'{wpt.name}</text>'
            )
        lines.append('  </g>')

    lines.append('</svg>')
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Convert GPX tracks to Inkscape SVG spline paths for OPCD.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s fairway_h1.gpx -o hole1.svg
  %(prog)s ./gpx_files/ -o course.svg --scale 5.0 --simplify-tolerance 0.5
  %(prog)s track.gpx -o out.svg --feature-type green-edge --hole 3
  %(prog)s walk.gpx -o out.svg --no-smooth

Feature types (use in GPX track names or --feature-type):
  fairway-left, fairway-right, green-edge, bunker-edge, tee-box,
  cart-path, ob-line, water-edge, tree-line, rough-edge
  
Track naming convention:  <feature-type>-<hole-number>
  e.g. "fairway-left-1", "green-edge-5", "bunker-edge-3"
""",
    )

    parser.add_argument(
        "input",
        help="GPX file or directory of GPX files to convert",
    )
    parser.add_argument(
        "-o", "--output",
        default="course.svg",
        help="Output SVG file path (default: course.svg)",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=2.0,
        help="Scale factor: SVG units per meter (default: 2.0)",
    )
    parser.add_argument(
        "--simplify-tolerance",
        type=float,
        default=0.3,
        help="RDP simplification tolerance in SVG units (default: 0.3; 0 to disable)",
    )
    parser.add_argument(
        "--smooth",
        dest="smooth",
        action="store_true",
        default=True,
        help="Generate smooth Catmull-Rom Bezier splines (default: enabled)",
    )
    parser.add_argument(
        "--no-smooth",
        dest="smooth",
        action="store_false",
        help="Use polylines instead of smooth splines",
    )
    parser.add_argument(
        "--feature-type",
        choices=list(FEATURE_CONFIG.keys()),
        default=None,
        help="Override feature type for all tracks in input (otherwise inferred from track name)",
    )
    parser.add_argument(
        "--hole",
        type=int,
        default=None,
        help="Override hole number for all tracks in input",
    )
    parser.add_argument(
        "--canvas-size",
        type=float,
        default=SVG_CANVAS_SIZE,
        help=f"SVG canvas width and height in units (default: {SVG_CANVAS_SIZE})",
    )
    parser.add_argument(
        "--center-lat",
        type=float,
        default=DEFAULT_CENTER_LAT,
        help=f"Course center latitude (default: {DEFAULT_CENTER_LAT})",
    )
    parser.add_argument(
        "--center-lon",
        type=float,
        default=DEFAULT_CENTER_LON,
        help=f"Course center longitude (default: {DEFAULT_CENTER_LON})",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    # Project course center
    center_e, center_n = _latlon_to_utm(args.center_lat, args.center_lon)
    logger.info("Course center UTM: E=%.1f  N=%.1f", center_e, center_n)

    # Collect GPX files
    input_path = Path(args.input)
    gpx_files: List[str] = []
    if input_path.is_dir():
        gpx_files = sorted(glob.glob(str(input_path / "*.gpx")))
        if not gpx_files:
            logger.error("No .gpx files found in directory: %s", input_path)
            sys.exit(1)
        logger.info("Found %d GPX files in %s", len(gpx_files), input_path)
    elif input_path.is_file():
        gpx_files = [str(input_path)]
    else:
        logger.error("Input path does not exist: %s", input_path)
        sys.exit(1)

    # Parse all GPX files
    all_segments: List[GpxTrackSegment] = []
    all_waypoints: List[GpxWaypoint] = []

    for gpx_file in gpx_files:
        try:
            segs, wpts = parse_gpx(
                gpx_file,
                center_easting=center_e,
                center_northing=center_n,
                scale=args.scale,
                canvas=args.canvas_size,
                feature_type_override=args.feature_type,
                hole_override=args.hole,
            )
            all_segments.extend(segs)
            all_waypoints.extend(wpts)
        except ET.ParseError as exc:
            logger.error("Failed to parse %s: %s", gpx_file, exc)
        except Exception as exc:
            logger.error("Error processing %s: %s", gpx_file, exc)

    if not all_segments and not all_waypoints:
        logger.error("No data found in any input file.")
        sys.exit(1)

    logger.info("Total: %d track segments, %d waypoints", len(all_segments), len(all_waypoints))

    # Build SVG
    svg_content = _build_svg(
        all_segments,
        all_waypoints,
        canvas=args.canvas_size,
        simplify_tolerance=args.simplify_tolerance,
        smooth=args.smooth,
    )

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg_content, encoding="utf-8")
    logger.info("SVG written to %s", output_path)
    logger.info("Canvas: %.0f x %.0f units, scale: %.1f units/meter",
                args.canvas_size, args.canvas_size, args.scale)


if __name__ == "__main__":
    main()
