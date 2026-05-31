# Ellensburg Golf Club — GS Pro Course Build

Build the [Ellensburg Golf Club](https://www.ellensburggolf.com/) as a playable course in [GS Pro](https://gsprogolf.com/) golf simulator.

**Course:** 9 holes · Par 35 · 3,075 yards · Ellensburg, Washington  
**Location:** 3231 Thorp Hwy S, Ellensburg, WA 98926  
**Coordinates:** 47.0193°N, 120.6294°W  
**Elevation:** 1,510–1,545 ft  

A semi-arid Central Washington course along the Yakima River, framed by Ponderosa pines and the legendary Kittitas Valley wind.

---

## Pipeline

```
WA DNR LIDAR → PDAL → DEM → Heightmap → Blender/OPCD → Unity → GreenKeeper → GS Pro
     ↑                                        ↑
  GPS field data → GPX → SVG splines → Inkscape → OPCD
```

## Project Structure

```
ellensburg-gc-gspro/
├── README.md                          ← You are here
├── setup.sh                           ← One-command setup (macOS)
├── requirements.txt                   ← Python dependencies
├── LICENSE                            ← MIT
│
├── lidar/                             ← LIDAR → DEM → Heightmap pipeline
│   ├── download_lidar.py              ← Download LAZ tiles from WA DNR
│   ├── pdal_pipeline.json             ← PDAL config: LAZ → ground DEM
│   ├── process_dem.py                 ← Clip, smooth, generate heightmap PNG
│   ├── course_boundary.geojson        ← Course boundary polygon
│   └── Makefile                       ← make download → make dem → make heightmap
│
├── gps/                               ← GPS track → SVG spline converter
│   ├── gpx_to_svg.py                  ← GPX → Inkscape SVG with OPCD layers
│   ├── samples/                       ← Example GPX files
│   │   ├── sample_fairway.gpx
│   │   └── sample_green.gpx
│   └── README.md                      ← GPS collection & converter docs
│
├── course_data/                       ← Course specification files
│   ├── greenkeeper_v4.json            ← GreenKeeper V4 config (all 9 holes)
│   ├── holes.md                       ← Hole-by-hole spec (confirmed vs estimated)
│   └── environment.json               ← Weather, wind, lighting, turf settings
│
├── svg/                               ← Course routing maps
│   ├── course_map.svg                 ← Full 9-hole overview
│   └── holes/                         ← Individual hole detail views
│       ├── hole_01.svg … hole_09.svg
│
├── blender/                           ← Blender/OPCD helper scripts
│   ├── import_dem.py                  ← Import heightmap as terrain mesh
│   ├── materials.py                   ← PBR material templates (18 surfaces)
│   ├── vegetation.json                ← 102 estimated tree positions + species
│   └── README.md                      ← Blender workflow guide
│
├── guides/                            ← Field guides for data collection
│   ├── data_collection.md             ← On-course GPS/photo guide
│   ├── polycam_guide.md               ← LIDAR scanning greens with Polycam
│   └── templates/
│       └── hole_survey_template.md    ← Per-hole data recording template
│
└── checklist/
    └── build_checklist.md             ← Full build checklist with time estimates
```

## Quick Start

### 1. Install dependencies

```bash
chmod +x setup.sh
./setup.sh
source .venv/bin/activate
```

**Prerequisites:** Homebrew, Python 3.9+, and these applications (installed separately):
- [QGIS](https://qgis.org/) — GIS data inspection
- [Inkscape](https://inkscape.org/) — SVG editing for OPCD
- [Blender 3.6+](https://www.blender.org/) — 3D terrain modeling
- [Unity](https://unity.com/) — Game engine (via OPCD export)
- [GS Pro](https://gsprogolf.com/) — Golf simulator

### 2. Download and process LIDAR

```bash
cd lidar
make all     # Downloads tiles, builds DEM, generates heightmap
```

Or step by step:
```bash
make download    # Fetch LAZ tiles from WA DNR
make dem         # Process LAZ → DEM via PDAL
make heightmap   # Clip to course boundary, generate 4096x4096 heightmap
```

### 3. Collect on-course GPS data

Follow [guides/data_collection.md](guides/data_collection.md) to walk the course with a GPS app, then convert tracks to SVG:

```bash
python gps/gpx_to_svg.py --input my_tracks/ --output course_features.svg
```

### 4. Build in Blender/OPCD

Open Blender, run the import script:
```
File → Import → Heightmap DEM (from this project)
```

See [blender/README.md](blender/README.md) for the full workflow.

### 5. Configure in GreenKeeper

Load `course_data/greenkeeper_v4.json` into GreenKeeper V4 and adjust pin positions, tee markers, and scorecards.

## Current Data Status

| Data Point | Status |
|---|---|
| Course location & layout | ✅ Confirmed |
| Hole pars & yardages | ✅ Confirmed |
| Scorecard totals | ✅ Confirmed |
| LIDAR terrain data | ✅ Available (WA DNR) |
| Hole routing/directions | ⚠️ Estimated from satellite |
| Green shapes & contours | ❌ Needs field collection |
| Bunker positions | ⚠️ Estimated |
| Tree positions | ⚠️ Estimated from satellite |
| Pin positions | ❌ Needs field collection |
| OB line positions | ⚠️ Estimated |
| Cart path routing | ⚠️ Estimated |

## Estimated Build Time

| Phase | Hours |
|---|---|
| Data Collection (GPS, Polycam, photos) | 8–12 |
| Terrain Processing (LIDAR pipeline) | 4–8 |
| Inkscape Course Design | 8–15 |
| Blender/OPCD Modeling | 15–25 |
| Unity Integration | 5–10 |
| GreenKeeper Configuration | 3–5 |
| Testing & Publishing | 5–10 |
| **Total** | **48–85** |

See [checklist/build_checklist.md](checklist/build_checklist.md) for the full step-by-step breakdown.

## Contributing

This is a community project. Contributions welcome — especially if you play at Ellensburg GC and can help with field data collection.

**Most needed:**
- GPS tracks of fairway edges, green perimeters, bunker edges
- Polycam/LIDAR scans of green contours
- Photos from each tee box and approach
- Accurate pin position data
- Yardage marker verification

## License

MIT — see [LICENSE](LICENSE).
