# CLAUDE_NEXT_STEPS.md

> **Audience:** Claude (Code or Cowork) resuming work on this project with Tony.
> **Last updated:** 2026-05-31 (updated after first Claude Code session)
> **Created by:** Claude (Cowork session, Opus)

---

## 1. Project Context

This repo contains the full build toolkit for creating **Ellensburg Golf Club** (Ellensburg, WA) as a playable course in **GS Pro** golf simulator. Ellensburg GC is a real 9-hole, par-35 course at 3231 Thorp Hwy S, Ellensburg, WA 98926. Tony (the repo owner) plays here and wants to build it for his home simulator.

The project was scaffolded in a single Cowork session. Every script is functional Python with real error handling and argparse — not pseudocode. But this is the starting point, not the finish line. The actual course build requires on-course data collection, manual 3D modeling work, and iteration across multiple software tools.

**End goal:** A published GS Pro course that Tony and the community can play on their simulators.

**Pipeline (no shortcuts exist):**
```
WA DNR LIDAR → PDAL → DEM → Heightmap
                                 ↓
GPS field data → GPX → SVG  →  Inkscape → Blender/OPCD → Unity → GreenKeeper → GS Pro
                                 ↑
                          Polycam green scans
```

---

## 2. Current State

**Repo is live at https://github.com/tonyswartz/ellensburg-gc-gspro**

### What's built:

| Component | Directory | Key Files | Status |
|---|---|---|---|
| LIDAR pipeline | `lidar/` | `download_lidar.py`, `process_dem.py`, `pdal_pipeline.json`, `Makefile`, `course_boundary.geojson` | Scripts complete, untested against live WA DNR API |
| GPS→SVG converter | `gps/` | `gpx_to_svg.py`, `samples/sample_fairway.gpx`, `samples/sample_green.gpx` | Converter tested with sample files, produces valid Inkscape SVG |
| Course data | `course_data/` | `greenkeeper_v4.json`, `holes.md`, `environment.json` | All 9 holes spec'd; most positions are [ESTIMATED] |
| SVG maps | `svg/` | `course_map.svg`, `holes/hole_01.svg` through `hole_09.svg` | Schematic routing diagrams, not GPS-accurate |
| Blender scripts | `blender/` | `import_dem.py`, `materials.py`, `vegetation.json` | 18 PBR materials, 102 estimated tree positions |
| Guides | `guides/` | `data_collection.md`, `polycam_guide.md`, `templates/hole_survey_template.md` | Ready for Tony to print and take to the course |
| Build checklist | `checklist/` | `build_checklist.md` | 7 phases, 200+ checkboxes, 48-85 hour estimate |
| Project root | `.` | `README.md`, `setup.sh`, `requirements.txt`, `.gitignore`, `LICENSE` | Setup script for macOS/Homebrew |

### Status after first Claude Code session (2026-05-31):

- [x] GitHub pushed — https://github.com/tonyswartz/ellensburg-gc-gspro
- [x] Virtual environment created at `.venv/`; scipy, shapely, pyproj, tqdm installed
- [x] GPS converter tested — all three test runs passed
- [x] `download_lidar.py` rewritten to use USGS TNM API (WA DNR ArcGIS endpoint is dead)
- [x] 2019 LiDAR tiles queried — 6 tiles, 486 MB total from `WA_EasternCascades_2019_B19`
- [ ] PDAL + GDAL — install in progress via `brew install pdal gdal`
- [ ] LiDAR tiles — download triggered, completing in background (~486 MB)
- [ ] rasterio, fiona — need to install after brew completes (depend on GDAL)
- [ ] DEM and heightmap — not yet generated
- [ ] On-course GPS data — not collected
- [ ] Polycam green scans — not done
- [ ] Blender/OPCD modeling — not started
- [ ] Unity scene — not started
- [ ] GreenKeeper testing — not started
- [ ] GreenKeeper JSON and vegetation positions — estimated, not ground-truthed

---

## 3. Immediate Next Steps (Priority Order)

### Step 1: Push to GitHub — DONE
Repo is live at https://github.com/tonyswartz/ellensburg-gc-gspro

### Step 2: Install prerequisites
PDAL + GDAL are being installed via `brew install pdal gdal` (this can take 20-30 min).
After brew finishes, install the remaining Python packages:
```bash
cd ~/Projects/ellensburg-gc-gspro
.venv/bin/pip install rasterio fiona GDAL
```

### Step 3: Run the LIDAR pipeline

**Download tiles** — 2019 Eastern Cascades data is already downloading (~486 MB).
To run it manually if needed:
```bash
cd lidar
python3 download_lidar.py                 # 2019 data (preferred, ~486 MB)
python3 download_lidar.py --dataset 2011  # legacy 2011 FEMA data (~238 MB)
python3 download_lidar.py --list-only     # just list tiles without downloading
```

**NOTE:** The WA DNR ArcGIS API is no longer functional. `download_lidar.py` has been
rewritten to use the USGS National Map (TNM) API. Two datasets cover the course area:
- `WA_EasternCascades_2019_B19` — 6 tiles, 486 MB, 2019 survey (recommended)
- `WA_KITTITASCOUNTY_2011` — 4 tiles, 238 MB, original FEMA survey

**Build DEM + heightmap** — after tiles download and brew finishes:
```bash
cd lidar
make dem         # PDAL: LAZ → ground-classified DEM (GeoTIFF)
make heightmap   # clips to course boundary, generates 4096×4096 PNG
```
Or `make all` once tiles exist.

**Expected output:** `lidar/data/ellensburg_gc_heightmap_4096.png` (16-bit grayscale)
and `lidar/data/ellensburg_gc_heightmap_meta.json` with elevation range + scale factors.

### Step 4: Test the GPS converter
```bash
cd gps
python gpx_to_svg.py samples/sample_fairway.gpx -o test_fairway.svg
python gpx_to_svg.py samples/sample_green.gpx -o test_green.svg
python gpx_to_svg.py samples/ -o test_batch.svg
```
Open the output SVGs in Inkscape to verify the layers are structured correctly for OPCD.

### Step 5: Test Blender import
Open Blender, go to Scripting workspace, and run `blender/import_dem.py`. It will prompt for the heightmap PNG and metadata JSON from Step 3. Verify the terrain mesh looks correct.

### Step 6: Collect on-course data
This is the bottleneck. Everything after this step depends on real field data. See Section 4 below.

---

## 4. On-Course Data Collection

Tony needs to play or walk a round with:

- **iPhone with GPS Tracks app** (by Dmitry Vakhtin) — records continuous GPS tracks at 1-second intervals. Name each track using the convention: `H1_fairway_left`, `H1_fairway_right`, `H1_green_edge`, `H1_bunker_1`, etc.
- **Polycam** (requires iPhone Pro with LiDAR sensor) — scan each green surface for contour data. This is the highest-value data for realistic gameplay.
- **Camera** — photograph every tee box view, approach angle, green, bunker, and hazard. The checklist in `guides/data_collection.md` has a per-hole photo list.
- **The survey template** — print 9 copies of `guides/templates/hole_survey_template.md` and fill in during the round.

**Full protocol:** `guides/data_collection.md`
**Polycam instructions:** `guides/polycam_guide.md`
**Estimated time:** 3-4 hours for GPS + photos, additional 1-2 hours for Polycam green scans.

After collection, export all GPX files from the GPS app and run them through `gps/gpx_to_svg.py` to generate the Inkscape SVG layer input for OPCD.

---

## 5. What Needs Human Verification

The `course_data/holes.md` file tags every data point as [CONFIRMED] or [ESTIMATED]. Here are the critical [ESTIMATED] items Tony needs to ground-truth:

### High Priority (affects playability)
- **Tee box GPS positions** — All holes except Hole 1 blue tee are estimated. Walk each tee box and record corners.
- **Green shapes and contours** — Every green is estimated as a generic oval. Walk the perimeter with GPS and scan with Polycam.
- **Bunker locations and shapes** — Positions are approximate from satellite. Walk each bunker edge.
- **Hole 7 elevation profile** — The 12-15 ft blind approach is the most interesting terrain feature on the course. Needs careful elevation mapping to get right.
- **Pin positions** — 4 estimated pin positions per green. Note where the actual cup sheets put them.

### Medium Priority (affects realism)
- **Yakima River bank edge** — The river is OB on Hole 4 and frames the south/east boundary. The exact bank position matters for OB placement.
- **Tree positions** — 102 trees in `blender/vegetation.json` are estimated from satellite. The species (Ponderosa pine, cottonwood, willow) are correct for the area but individual positions need verification.
- **Fairway widths** — Estimated at 30-45 yards across holes. Walk both edges to get actual widths.
- **Cart path routing** — Estimated. Walk or note the actual path.
- **Irrigation pond (Hole 6)** — Size and exact position estimated.

### Lower Priority (affects polish)
- **White tee positions** — All estimated as ~15-20 yard offsets from blue tees.
- **Yardage marker positions** — 150/200/250 markers.
- **OB fence/stake lines** — Holes 1, 4, 9.
- **Clubhouse and structures** — Approximate location only.

---

## 6. Key Files to Know About

When resuming work, start here:

| File | What It Is | When You Need It |
|---|---|---|
| `course_data/greenkeeper_v4.json` | GreenKeeper V4 config with all 9 holes, tees, pins, hazards, OB. This is what GS Pro ultimately consumes. | Updating course data after field collection |
| `course_data/holes.md` | Hole-by-hole spec with [CONFIRMED]/[ESTIMATED] tags and per-hole data collection checklists. | Planning what data to collect, tracking what's been verified |
| `course_data/environment.json` | Wind, weather, lighting, turf, ambient sound settings calibrated for Kittitas Valley. | Configuring GS Pro environment |
| `lidar/Makefile` | Orchestrates the full LIDAR→DEM→heightmap pipeline. | Running terrain processing |
| `lidar/download_lidar.py` | Downloads LAZ tiles from WA DNR. The API endpoint may need updating if WA DNR changes their portal. | First step of terrain pipeline |
| `lidar/process_dem.py` | Clips DEM to course boundary, fills voids, generates 16-bit heightmap PNG + metadata JSON. | After PDAL generates the raw DEM |
| `gps/gpx_to_svg.py` | Converts GPS tracks to Inkscape SVG with OPCD-compatible layers and Bezier splines. | After on-course GPS data collection |
| `blender/import_dem.py` | Imports heightmap into Blender as terrain mesh with correct scale. Registers as File→Import menu item. | Starting 3D modeling phase |
| `blender/materials.py` | Creates 18 PBR materials for course surfaces. Registers as Object menu item. | After terrain mesh is imported |
| `blender/vegetation.json` | 102 tree positions with species, height, canopy diameter. | Placing vegetation in Blender |
| `checklist/build_checklist.md` | Master checklist: 7 phases, 200+ items, time estimates, file cross-references. | Tracking overall progress |
| `guides/data_collection.md` | Field protocol for GPS data collection during a round. | Before going to the course |
| `guides/templates/hole_survey_template.md` | Per-hole recording template. Print 9 copies. | During on-course collection |
| `lidar/course_boundary.geojson` | Polygon boundary for clipping. 17-vertex polygon around course with ~500m buffer. | May need refinement after seeing LIDAR data |

---

## 7. Architecture Decisions

**Why this pipeline?** GS Pro courses are built using OPCD (Open Platform Course Designer), which is a Blender-to-Unity pipeline. There is no way to skip steps — you cannot go directly from LIDAR data to a playable GS Pro course. Each tool handles a specific part:

- **PDAL/GDAL** — Point cloud processing and raster generation. The raw LIDAR has millions of points across ground, vegetation, and structures. PDAL filters to ground returns and creates a DEM. GDAL clips and resamples.
- **QGIS** — Visual inspection and validation of the DEM and course boundary. Not automated but essential for catching errors.
- **Inkscape** — Course feature boundaries (fairways, greens, bunkers, etc.) are drawn as SVG paths on named layers. OPCD reads these layers. The `gps/gpx_to_svg.py` converter generates the initial SVG from GPS data, but manual refinement in Inkscape is always needed.
- **Blender + OPCD** — The terrain mesh (from heightmap) and feature boundaries (from SVG) come together here. This is where most of the manual work happens: sculpting greens, placing vegetation, building structures, setting up materials.
- **Unity** — OPCD exports the Blender scene to a Unity project. Colliders, physics, gameplay triggers, and camera rails are set up here.
- **GreenKeeper** — GS Pro's course configuration tool. Hole routing, pin positions, tee positions, scorecards, and environment settings are configured here using the data in `course_data/greenkeeper_v4.json`.

**CRS choices:** LIDAR is in EPSG:2856 (WA State Plane South, US feet). The PDAL pipeline reprojects to EPSG:32610 (UTM Zone 10N, meters) for consistent metric processing. GPS data is WGS84 (EPSG:4326). The converter handles all projections internally.

**Heightmap format:** 16-bit grayscale PNG at 4096x4096 pixels. This gives ~0.15m/pixel resolution for a course-sized area. The metadata JSON stores the elevation range so Blender can correctly scale the displacement.

**Vegetation approach:** Tree positions are in WGS84 lat/lon in `blender/vegetation.json`. The Blender import script would need to convert these to the scene's local coordinate system. The positions are estimated — after field verification, update the JSON and re-import.

---

## 8. Known Issues and Gotchas

- **WA DNR API is dead:** The original `download_lidar.py` used WA DNR's ArcGIS REST tile-index service, which no longer exposes a queryable tile index. The script has been rewritten to use the USGS National Map (TNM) API at `tnmaccess.nationalmap.gov`. The USGS has both the 2011 Kittitas FEMA data and a newer 2019 Eastern Cascades survey — use the 2019 data.
- **PDAL pipeline JSON:** The `pdal_pipeline.json` uses hardcoded input/output paths. The Makefile handles this, but if running PDAL manually, update the paths.
- **Blender version:** `import_dem.py` and `materials.py` are compatible with Blender 3.x and 4.x (they handle the renamed Principled BSDF inputs). If something breaks on a newer Blender version, check the shader input names first.
- **GPS accuracy:** Consumer phone GPS is ±3-5 meters. The `gpx_to_svg.py` converter applies Ramer-Douglas-Peucker simplification and Catmull-Rom smoothing to handle noise, but green edges and bunker edges will still need manual refinement in Inkscape.
- **Course boundary GeoJSON:** The polygon in `lidar/course_boundary.geojson` is approximate. If the LIDAR download grabs too much or too little area, adjust the boundary coordinates.
- **The SVG maps** in `svg/` are schematic routing diagrams, not GPS-accurate overlays. They're useful for visualization but should not be used as OPCD input. The actual OPCD SVGs will come from the GPS converter output, refined in Inkscape.
