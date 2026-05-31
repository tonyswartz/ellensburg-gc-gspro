# Ellensburg Golf Club — GS Pro Course Build Checklist

**Course:** Ellensburg Golf Club, Ellensburg WA
**Holes:** 9, Par 35, 3,075 yards
**Pipeline:** LIDAR + GPS + Polycam → QGIS → Inkscape → Blender (OPCD) → Unity → GreenKeeper → Publish

**Total estimated time: 48-85 hours across all phases**

---

## Phase 1: Data Collection (8-12 hours)

Everything starts with good data. No amount of modeling skill can fix missing or inaccurate source data.

### 1.1 LIDAR Data Acquisition (1-2 hours)

- [ ] Download LIDAR point cloud from WA DNR LIDAR Portal
  - URL: https://lidarportal.dnr.wa.gov/
  - Area: Kittitas County, Ellensburg area
  - Center: 47.0193N, 120.6294W
  - Download tiles covering the full course + 200m buffer
  - Format: LAS or LAZ
  - Save to: `lidar/raw/`
- [ ] Verify LIDAR coverage includes the entire course
- [ ] Note the LIDAR acquisition date and point density
- [ ] Check CRS (should be WA State Plane South or UTM Zone 10N)

### 1.2 On-Course GPS Data Collection (~4 hours)

**Reference:** `guides/data_collection.md`

- [ ] Print 9 copies of `guides/templates/hole_survey_template.md`
- [ ] Charge phone and bring battery pack
- [ ] Install and configure GPS Tracks app (1-second interval, 1m filter)
- [ ] **Hole 1:** tee, fairway edges, green, bunkers, cart path
- [ ] **Hole 2:** tee, fairway edges, green, bunkers, cart path
- [ ] **Hole 3:** tee, fairway edges, green, bunkers, cart path
- [ ] **Hole 4:** tee, fairway edges, green, bunkers, cart path, tree waypoints
- [ ] **Hole 5:** tee, fairway edges, green, bunkers, cart path, tree waypoints, river edge
- [ ] **Hole 6:** tee, fairway edges, green, bunkers, cart path
- [ ] **Hole 7:** tee, fairway edges, green, bunkers, cart path, tree waypoints
- [ ] **Hole 8:** tee, fairway edges, green, bunkers, cart path, tree waypoints, river edge
- [ ] **Hole 9:** tee, fairway edges, green, bunkers, cart path
- [ ] Record OB boundaries for all holes
- [ ] Record clubhouse area and parking
- [ ] Record practice green and driving range (if present)
- [ ] Export all GPS tracks as GPX files
- [ ] Back up to computer: `gps/raw/`

### 1.3 Polycam Green Scanning (~2 hours)

**Reference:** `guides/polycam_guide.md`

- [ ] Green 1 scanned → `polycam/green_H1.ply`
- [ ] Green 2 scanned → `polycam/green_H2.ply`
- [ ] Green 3 scanned → `polycam/green_H3.ply`
- [ ] Green 4 scanned → `polycam/green_H4.ply`
- [ ] Green 5 scanned → `polycam/green_H5.ply`
- [ ] Green 6 scanned → `polycam/green_H6.ply`
- [ ] Green 7 scanned → `polycam/green_H7.ply`
- [ ] Green 8 scanned → `polycam/green_H8.ply`
- [ ] Green 9 scanned → `polycam/green_H9.ply`
- [ ] Review all scans for quality (no gaps, visible contour)
- [ ] Back up to computer: `polycam/`

### 1.4 Photo Documentation (included with GPS collection)

- [ ] Tee shot view — all 9 holes
- [ ] Approach view — all 9 holes
- [ ] Green views (front, back, sides) — all 9 holes
- [ ] All bunkers photographed
- [ ] All water hazards photographed
- [ ] Clubhouse exterior
- [ ] Course overview / scenic shots
- [ ] Organize into folders: `photos/hole_01/` through `photos/hole_09/`, `photos/course/`

### 1.5 Data Organization and Backup (1 hour)

- [ ] All GPS tracks exported and saved to `gps/raw/`
- [ ] All Polycam scans exported and saved to `polycam/`
- [ ] All photos organized by hole
- [ ] Survey templates filled in and saved to `guides/surveys/`
- [ ] All data backed up to a second location (cloud drive or external disk)
- [ ] Yardage book scanned or photographed (if obtained from pro shop)

**Milestone: All raw data collected and backed up.**

---

## Phase 2: Terrain Processing (4-8 hours)

Convert raw LIDAR and GPS data into usable terrain meshes.

### 2.1 LIDAR Processing (2-4 hours)

**Tools:** PDAL, QGIS

- [ ] Install PDAL (via conda: `conda install -c conda-forge pdal`)
- [ ] Merge LIDAR tiles covering the course area
- [ ] Filter to ground-classified points only (Class 2)
  - PDAL pipeline: `filters.range` with `Classification[2:2]`
- [ ] Reproject to UTM Zone 10N (EPSG:32610) if not already
- [ ] Generate DEM raster using `writers.gdal`
  - Resolution: 0.5m per pixel
  - Output: GeoTIFF (`lidar/processed/ellensburg_gc_dem.tif`)
- [ ] Generate hillshade for visual verification
- [ ] Verify DEM in QGIS — overlay on satellite imagery
- [ ] Check elevation range (should be ~460-470m / 1510-1545 ft)

### 2.2 Heightmap Generation (1-2 hours)

**Tools:** QGIS, GDAL

- [ ] Clip DEM to course boundary (with 50m buffer)
- [ ] Normalize elevation to 0-1 range (for 16-bit PNG)
- [ ] Export as 16-bit grayscale PNG
  - Target resolution: 4096x4096 or nearest power-of-2
  - Save to: `lidar/processed/heightmap.png`
- [ ] Generate metadata JSON with dimensions and elevation range
  - Save to: `lidar/processed/heightmap_metadata.json`
  - Must include: `real_width_m`, `real_height_m`, `elevation_min`, `elevation_max`, `pixel_size`
- [ ] Verify heightmap visually — should show terrain contours

### 2.3 GPS Track Processing (1-2 hours)

**Tools:** QGIS

- [ ] Import all GPX tracks into QGIS
- [ ] Verify each track against satellite imagery
- [ ] Clean up tracks with GPS drift (smooth or re-digitize)
- [ ] Reproject all tracks to project CRS (EPSG:32610)
- [ ] Export cleaned tracks as GeoJSON: `gps/processed/`
- [ ] Verify tee, green, and bunker outlines form closed shapes
- [ ] Cross-reference GPS data with satellite imagery for any missed features

**Milestone: Clean terrain heightmap and verified GPS features ready for design.**

---

## Phase 3: Course Design in Inkscape (8-15 hours)

Create the SVG spline definitions that OPCD uses to define course features.

**Depends on:** Phase 2 complete (heightmap, processed GPS tracks)

### 3.1 Reference Setup (1-2 hours)

**Tools:** Inkscape, QGIS (for export)

- [ ] Export satellite image of course from QGIS (georeferenced PNG)
- [ ] Import satellite image as base layer in Inkscape
- [ ] Scale to match real-world dimensions (use GPS reference points)
- [ ] Import GPS tracks as SVG paths (convert from GeoJSON)
- [ ] Set up Inkscape layers:
  - `Reference` — satellite image (locked)
  - `GPS_Tracks` — imported GPS data (locked, for reference)
  - `Fairways` — fairway outlines
  - `Greens` — green outlines
  - `Tees` — tee box outlines
  - `Bunkers` — bunker outlines
  - `Water` — water features
  - `CartPaths` — cart path lines
  - `OB` — out of bounds lines
  - `Rough` — rough area boundaries
  - `Trees` — tree positions (circles)
- [ ] Set document units to meters

### 3.2 Feature Tracing — Playing Surfaces (4-8 hours)

- [ ] **Hole 1:** Trace fairway, green, tee, bunkers from GPS + satellite
- [ ] **Hole 2:** Trace all features
- [ ] **Hole 3:** Trace all features
- [ ] **Hole 4:** Trace all features (more trees here)
- [ ] **Hole 5:** Trace all features + river edge
- [ ] **Hole 6:** Trace all features
- [ ] **Hole 7:** Trace all features (more trees)
- [ ] **Hole 8:** Trace all features + river edge
- [ ] **Hole 9:** Trace all features
- [ ] Smooth all splines — no sharp corners on natural features
- [ ] Verify green outlines match GPS + Polycam data
- [ ] Ensure no overlapping features (green inside fairway, etc. — OK; bunker overlapping fairway edge — fix)

### 3.3 Feature Tracing — Hazards and Boundaries (2-3 hours)

- [ ] Trace all water hazards
- [ ] Trace all OB lines
- [ ] Trace cart paths (as line + width, or as filled paths)
- [ ] Mark tree positions (from `blender/vegetation.json` and GPS waypoints)
- [ ] Add any bridges, walls, or structures

### 3.4 Quality Check (1-2 hours)

- [ ] Toggle satellite layer visibility — do features align?
- [ ] Check hole routing makes sense (tee → fairway → green, no overlaps between holes)
- [ ] Verify all greens are closed shapes
- [ ] Verify all bunkers are closed shapes
- [ ] Check scale: measure a known distance (e.g., 150-yard marker to green center)
- [ ] Export final SVG: `svg/ellensburg_gc_course.svg`
- [ ] Save Inkscape project file: `svg/ellensburg_gc_course.inkscape.svg`

**Milestone: Complete SVG with all course features traced and verified.**

---

## Phase 4: Blender / OPCD Modeling (15-25 hours)

Build the 3D course model using Blender and OPCD tools.

**Depends on:** Phase 2 (heightmap) + Phase 3 (SVG features)

### 4.1 Terrain Import (1-2 hours)

**Script:** `blender/import_dem.py`

- [ ] Open Blender, run `import_dem.py`
- [ ] Import heightmap: `lidar/processed/heightmap.png`
- [ ] Verify terrain dimensions match real-world (check 100m grid markers)
- [ ] Verify elevation range (check scale markers)
- [ ] Set vertical exaggeration to 3x for modeling, note to reset before export
- [ ] Save Blender file: `blender/ellensburg_gc.blend`

### 4.2 Material Setup (1 hour)

**Script:** `blender/materials.py`

- [ ] Run `materials.py` to create all course materials
- [ ] Verify materials look correct in Material Preview mode
- [ ] Apply base "Rough" material to entire terrain (default surface)

### 4.3 Feature Modeling (6-10 hours)

- [ ] Import SVG course features from Inkscape
- [ ] Convert SVG paths to mesh regions on the terrain
- [ ] Assign materials to each feature region:
  - [ ] All fairways → Fairway material
  - [ ] All greens → Green material
  - [ ] All tees → TeeBox material
  - [ ] All bunkers → Bunker material
  - [ ] All fringe areas → FringeCollar material
  - [ ] Water features → Water material
  - [ ] Cart paths → CartPath material
  - [ ] Heavy rough / native areas → HeavyRough material
- [ ] Verify material boundaries look clean and natural

### 4.4 Green Shaping (3-5 hours)

This is the most detail-intensive part of the build.

- [ ] Import Polycam scans (PLY files from `polycam/`)
- [ ] Align each scan with the corresponding green area on terrain
- [ ] Shape terrain mesh to match Polycam contours for each green:
  - [ ] Green 1
  - [ ] Green 2
  - [ ] Green 3
  - [ ] Green 4
  - [ ] Green 5
  - [ ] Green 6
  - [ ] Green 7
  - [ ] Green 8
  - [ ] Green 9
- [ ] Verify green contours from multiple camera angles
- [ ] Check that green edges blend smoothly into fringe/collar
- [ ] Reset vertical exaggeration to 1.0 and re-check

### 4.5 Bunker Shaping (2-3 hours)

- [ ] Model bunker depressions in terrain mesh
- [ ] Set correct depth for each bunker (from survey data)
- [ ] Shape bunker lips (raised edges)
- [ ] Ensure sand material covers the entire bunker floor
- [ ] Verify bunker edges blend into surrounding terrain

### 4.6 Vegetation Placement (2-3 hours)

**Data:** `blender/vegetation.json`

- [ ] Import or create tree models (3-4 pine variations, 2-3 deciduous variations)
- [ ] Place Ponderosa pines (72 trees) from vegetation.json
- [ ] Place cottonwoods (19 trees) along river corridor
- [ ] Place willows (21 trees) along river bank
- [ ] Place ornamental trees (22 trees) near clubhouse and features
- [ ] Randomize rotation and slight scale variation for natural appearance
- [ ] Apply correct trunk and foliage materials per species
- [ ] Verify tree placement against satellite imagery

### 4.7 Structures and Hardscape (1-2 hours)

- [ ] Model or place clubhouse (simple block model is fine)
- [ ] Add any bridges
- [ ] Model cart path surfaces (extruded from SVG paths)
- [ ] Add any fencing along OB lines
- [ ] Add tee markers (simple colored objects)
- [ ] Add flag sticks on greens (thin cylinders)

### 4.8 Lighting and Environment (1-2 hours)

- [ ] Set up sun light (angle for Central WA latitude ~47N)
- [ ] Set sky/environment (blue sky, few clouds — typical Ellensburg summer)
- [ ] Configure ambient light for natural appearance
- [ ] Set up wind parameters (Kittitas Valley is very windy — 15-25 mph typical)
- [ ] Test render from a few camera positions

### 4.9 Final Blender Review (1-2 hours)

- [ ] Walk through all 9 holes with camera
- [ ] Check for floating objects, clipping, or material errors
- [ ] Verify all greens have visible contour
- [ ] Verify tree positions and sizes look natural
- [ ] Check terrain edges are clean (no ragged boundaries)
- [ ] Save final Blender file

**Milestone: Complete 3D model with terrain, features, vegetation, and structures.**

---

## Phase 5: Unity Integration (5-10 hours)

Export from Blender and set up in Unity for GS Pro.

**Depends on:** Phase 4 complete

### 5.1 Blender Export (1-2 hours)

- [ ] Follow OPCD export guidelines for naming conventions
- [ ] Export terrain mesh as FBX
- [ ] Export vegetation as separate FBX (or use OPCD instancing)
- [ ] Export structures as separate FBX
- [ ] Verify all materials export with correct names
- [ ] Check UV mapping is intact

### 5.2 Unity Project Setup (1-2 hours)

- [ ] Create new Unity project (or use OPCD template)
- [ ] Import OPCD Unity package
- [ ] Import exported FBX files
- [ ] Verify all assets imported correctly (no missing textures/materials)
- [ ] Set up Unity project settings per OPCD documentation

### 5.3 Scene Assembly (2-3 hours)

- [ ] Place terrain in scene
- [ ] Place vegetation
- [ ] Place structures
- [ ] Set up terrain colliders
- [ ] Configure physics layers (ground, water, OB, etc.)
- [ ] Set up ball physics surfaces per material type
- [ ] Configure camera positions for each hole

### 5.4 Gameplay Element Setup (1-3 hours)

- [ ] Define tee positions for each hole (place OPCD tee markers)
- [ ] Define green boundaries (for pin placement zones)
- [ ] Define fairway/rough/bunker surface types for ball behavior
- [ ] Define water hazard penalty zones
- [ ] Define OB boundaries
- [ ] Configure drop zones (if applicable)
- [ ] Set up hole routing (1→2→3...→9)

**Milestone: Playable (rough) course in Unity.**

---

## Phase 6: GreenKeeper Configuration (3-5 hours)

Configure the course for GS Pro gameplay using GreenKeeper.

**Depends on:** Phase 5 complete (working Unity course)

### 6.1 Course Setup (1 hour)

- [ ] Open course in GreenKeeper
- [ ] Set course name: "Ellensburg Golf Club"
- [ ] Set location: Ellensburg, WA
- [ ] Set course type: Public
- [ ] Set number of holes: 9
- [ ] Set total par: 35
- [ ] Set total yardage: 3,075 (tips)
- [ ] Set elevation: 1,510 ft
- [ ] Set latitude/longitude: 47.0193, -120.6294

### 6.2 Hole Configuration (1-2 hours)

For each hole, configure:

| Hole | Par | Yards | HCP |
|------|-----|-------|-----|
| 1 | 4 | TBD | TBD |
| 2 | 4 | TBD | TBD |
| 3 | 3 | TBD | TBD |
| 4 | 4 | TBD | TBD |
| 5 | 5 | TBD | TBD |
| 6 | 3 | TBD | TBD |
| 7 | 4 | TBD | TBD |
| 8 | 5 | TBD | TBD |
| 9 | 4 | TBD | TBD |

(Fill in actual yardages from scorecard and GPS measurements)

- [ ] Set par for each hole
- [ ] Set yardages for each tee (if multiple tees)
- [ ] Set handicap index for each hole
- [ ] Set hole direction/routing

### 6.3 Pin Positions (1 hour)

- [ ] Configure 4 pin positions per green (front, middle, back, tucked)
- [ ] Pin 1: Front-center (standard)
- [ ] Pin 2: Middle (default position)
- [ ] Pin 3: Back (challenging)
- [ ] Pin 4: Tucked/corner (most difficult)
- [ ] Verify all pins are on the putting surface (not on fringe or off-green)
- [ ] Test that pin positions create varying difficulty levels

### 6.4 Tee Positions (30 min)

- [ ] Set tee positions for each hole
- [ ] If multiple tee colors exist, configure each
- [ ] Verify tee-to-pin distances match scorecard yardages

### 6.5 Environment Settings (30 min)

- [ ] Set default wind speed: 10-15 mph (Kittitas Valley average)
- [ ] Set wind direction: W or NW (prevailing for Ellensburg)
- [ ] Set altitude for ball flight calculations: 1,510 ft
- [ ] Set green speed: Stimp 8.5 (medium)
- [ ] Set fairway firmness: Medium-firm (semi-arid)
- [ ] Set rough penalty: Standard

**Milestone: Fully configured course in GreenKeeper, ready for testing.**

---

## Phase 7: Testing and Publishing (5-10 hours)

### 7.1 Solo Play Testing (2-4 hours)

- [ ] Play all 9 holes in GS Pro simulator
- [ ] **Hole-by-hole check:**
  - [ ] Hole 1: Distances correct? Green breaks realistic? Bunker playable?
  - [ ] Hole 2: Same checks
  - [ ] Hole 3: Same checks
  - [ ] Hole 4: Trees in correct positions? Gaps playable?
  - [ ] Hole 5: River boundary visible? Trees correct? Par 5 length right?
  - [ ] Hole 6: Par 3 distance correct? Green size right?
  - [ ] Hole 7: Tree-lined fairway plays correctly?
  - [ ] Hole 8: River hazard works? Par 5 length right?
  - [ ] Hole 9: Finishing hole plays well?
- [ ] Check ball physics on each surface type
- [ ] Check ball bouncing on greens is realistic
- [ ] Check that putts break in the correct direction on each green
- [ ] Test all 4 pin positions on every green
- [ ] Test OB penalties trigger correctly
- [ ] Test water hazard penalties trigger correctly
- [ ] Verify scorecard totals correctly

### 7.2 Adjustments (2-4 hours)

Based on play-testing, adjust:

- [ ] Green slopes (most common fix — greens too flat or too severe)
- [ ] Green speeds (stimp adjustment)
- [ ] Fairway widths (too narrow or too wide)
- [ ] Bunker positions and depths
- [ ] Tree placement (blocking intended shot lines?)
- [ ] Rough penalty (too punishing or too easy?)
- [ ] Wind effects (Ellensburg is very windy — make sure it plays like that)
- [ ] Distances (compare GPS-measured vs. in-game yardages)
- [ ] Tee box locations and angles
- [ ] Re-test after each round of adjustments

### 7.3 Visual Polish (1-2 hours)

- [ ] Check for visual artifacts (z-fighting, floating objects, texture seams)
- [ ] Verify skybox and environment look like Central WA (dry, sunny, big sky)
- [ ] Check that trees cast appropriate shadows
- [ ] Verify water features look correct from all angles
- [ ] Check overall color palette matches the semi-arid landscape
- [ ] Add any finishing touches (flowers near clubhouse, etc.)

### 7.4 Final Quality Check (30 min)

- [ ] Play one final round without making changes — just verify
- [ ] Take screenshots of each hole for the course listing
- [ ] Record a "flyover" video of all 9 holes (for community post)

### 7.5 Publishing (30 min)

- [ ] Export final course package per GS Pro requirements
- [ ] Create course listing:
  - Course name: Ellensburg Golf Club
  - Location: Ellensburg, WA
  - Holes: 9
  - Par: 35
  - Yardage: 3,075
  - Description: "Ellensburg Golf Club is a charming 9-hole public course in the heart of the Kittitas Valley in Central Washington. Set at 1,510 feet elevation with Ponderosa pines lining several fairways and the Yakima River forming the eastern boundary. Known for its windy conditions, this course rewards accurate shot-making. Built from LIDAR data and on-course GPS surveys."
  - Screenshots: scenic shots of 3-4 signature holes
- [ ] Upload to GS Pro community
- [ ] Test download and install on a clean GS Pro instance
- [ ] Verify course loads and plays correctly after install

**Milestone: Course published and available to the GS Pro community.**

---

## Progress Tracker

| Phase | Status | Hours Spent | Start Date | Complete Date |
|-------|--------|-------------|------------|---------------|
| 1. Data Collection | Not Started | | | |
| 2. Terrain Processing | Not Started | | | |
| 3. Inkscape Design | Not Started | | | |
| 4. Blender Modeling | Not Started | | | |
| 5. Unity Integration | Not Started | | | |
| 6. GreenKeeper Config | Not Started | | | |
| 7. Testing & Publish | Not Started | | | |
| **Total** | | **0 / 48-85 hrs** | | |

---

## File Reference

Key files in the repository and which phase creates/uses them:

| File | Created In | Used In |
|------|-----------|---------|
| `lidar/raw/*.las` | Phase 1.1 | Phase 2.1 |
| `lidar/processed/ellensburg_gc_dem.tif` | Phase 2.1 | Phase 2.2 |
| `lidar/processed/heightmap.png` | Phase 2.2 | Phase 4.1 |
| `lidar/processed/heightmap_metadata.json` | Phase 2.2 | Phase 4.1 |
| `gps/raw/*.gpx` | Phase 1.2 | Phase 2.3 |
| `gps/processed/*.geojson` | Phase 2.3 | Phase 3.1 |
| `polycam/green_H*.ply` | Phase 1.3 | Phase 4.4 |
| `photos/` | Phase 1.4 | Reference throughout |
| `guides/surveys/*.md` | Phase 1.5 | Reference for modeling |
| `svg/ellensburg_gc_course.svg` | Phase 3 | Phase 4.3 |
| `blender/import_dem.py` | Pre-built | Phase 4.1 |
| `blender/materials.py` | Pre-built | Phase 4.2 |
| `blender/vegetation.json` | Pre-built | Phase 4.6 |
| `blender/ellensburg_gc.blend` | Phase 4.1 | Phases 4-5 |

---

## Dependencies

```
Phase 1 (Data Collection)
  ├── no dependencies, start here
  │
Phase 2 (Terrain Processing)
  ├── depends on: Phase 1.1 (LIDAR), Phase 1.2 (GPS)
  │
Phase 3 (Inkscape Design)
  ├── depends on: Phase 2.2 (heightmap for reference), Phase 2.3 (GPS tracks)
  │
Phase 4 (Blender Modeling)
  ├── depends on: Phase 2.2 (heightmap), Phase 3 (SVG features)
  ├── Phase 4.4 depends on: Phase 1.3 (Polycam scans)
  │
Phase 5 (Unity Integration)
  ├── depends on: Phase 4 (complete Blender model)
  │
Phase 6 (GreenKeeper)
  ├── depends on: Phase 5 (working Unity course)
  │
Phase 7 (Testing & Publishing)
  ├── depends on: Phase 6 (configured course)
```

**Parallelism opportunities:**
- Phase 1.1 (LIDAR download) can happen while you plan the on-course visit
- Phase 3 (Inkscape) can start as soon as Phase 2 produces the heightmap and GPS tracks — you don't need Polycam scans yet
- Polycam scanning (Phase 1.3) can be a separate trip from GPS collection (Phase 1.2)
- Photos can be taken on either trip
