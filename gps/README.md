# GPS to SVG Converter for OPCD

Convert GPS tracks recorded on-course into Inkscape SVG files compatible with
the Open Platform Course Designer (OPCD) for GS Pro golf simulator.

## What This Does

`gpx_to_svg.py` takes GPX files containing GPS track data — recorded by walking
the edges of fairways, greens, bunkers, and other course features — and converts
them into properly layered Inkscape SVG files with smooth Bezier spline paths.
The output SVGs can be opened directly in Inkscape and used with OPCD to build
the course in GS Pro.

Key processing steps:
1. Parse GPS coordinates from GPX track segments
2. Project WGS84 lat/lon to UTM Zone 10N (meters), then scale to SVG units
3. Apply Ramer-Douglas-Peucker simplification to reduce GPS noise
4. Convert point sequences to smooth cubic Bezier splines (Catmull-Rom)
5. Organize paths into OPCD-compatible named layers in Inkscape SVG format

## How to Collect GPS Data

### Recommended Apps (iPhone)

**GPS Tracks by Dmitry Vakhtin** (Best for this purpose)
- Highest accuracy track recording available on iOS
- Supports custom track naming during recording
- Exports clean GPX 1.1 files
- Settings: set recording interval to **1 second**, accuracy filter to **Best**

**Strava** (Good alternative)
- Reliable GPS recording
- Slightly less granular than GPS Tracks
- Export GPX from the Strava website (Activity → Export GPX)

**Bad Elf GPS** (If using external GPS receiver)
- Pairs with Bad Elf Bluetooth GPS receivers for sub-meter accuracy
- Excellent for courses where phone GPS struggles (tree-lined holes)

### GPS App Settings

For all apps, configure these before walking the course:

| Setting | Value | Why |
|---------|-------|-----|
| Recording interval | 1 second | Captures enough detail for curves |
| Accuracy mode | High / Best | Reduces wandering points |
| Auto-pause | **OFF** | Prevents gaps when you stop to check position |
| Screen lock | **OFF** | Some apps reduce GPS when screen locks |

### Walking the Course

Walk each feature edge as a separate track, naming it with the convention:

```
<feature-type>-<hole-number>
```

**Feature types:**

| Feature | Track name prefix | What to walk |
|---------|-------------------|-------------|
| Fairway left edge | `fairway-left-` | Left boundary of fairway (looking tee→green) |
| Fairway right edge | `fairway-right-` | Right boundary of fairway |
| Green edge | `green-edge-` | Full perimeter of putting green |
| Bunker edge | `bunker-edge-` | Full perimeter of each bunker |
| Tee box | `tee-box-` | Perimeter of tee box |
| Cart path | `cart-path-` | Center line of cart path |
| OB line | `ob-line-` | Out of bounds boundary |
| Water edge | `water-edge-` | Shoreline of water hazards |
| Tree line | `tree-line-` | Edge of tree lines / forest |
| Rough edge | `rough-edge-` | Boundary between rough and other areas |

**Tips for accurate data:**

- Walk at a **steady, slow pace** (2-3 mph) along the exact edge
- For closed shapes (greens, bunkers, tees), walk the full perimeter and
  overlap your start point by a few steps
- For fairways, walk one side tee-to-green, then the other side
- Hold the phone at a **consistent height** (waist or chest, not in pocket)
- Walk on **clear days** — cloud cover degrades GPS slightly
- Avoid walking near buildings or dense tree canopy when possible
- Drop **waypoints** at key reference points: tee centers, green centers,
  150-yard markers, and any known survey points

### Exporting GPX

**From GPS Tracks:**
1. Open the track in the app
2. Tap Share → Export as GPX
3. AirDrop or save to Files

**From Strava:**
1. Log in to strava.com on a computer
2. Open the activity
3. Click the wrench icon → Export GPX

**From Bad Elf:**
1. Connect Bad Elf app to the receiver
2. Go to Tracks → select track
3. Share → GPX format

## Using the Converter

### Basic Usage

Convert a single GPX file:
```bash
python gpx_to_svg.py fairway_h1.gpx -o hole1.svg
```

Convert all GPX files in a directory into one SVG:
```bash
python gpx_to_svg.py ./gpx_data/ -o ellensburg_gc.svg
```

### Command-Line Options

```
python gpx_to_svg.py <input> [options]

Required:
  input                   GPX file or directory of GPX files

Options:
  -o, --output FILE       Output SVG path (default: course.svg)
  --scale FLOAT           SVG units per meter (default: 2.0)
  --simplify-tolerance F  RDP simplification tolerance (default: 0.3, 0=off)
  --smooth                Use Catmull-Rom Bezier splines (default)
  --no-smooth             Use polylines instead of splines
  --feature-type TYPE     Override feature type for all tracks
  --hole N                Override hole number for all tracks
  --canvas-size FLOAT     SVG canvas size in units (default: 2000)
  --center-lat FLOAT      Course center latitude (default: 47.0193)
  --center-lon FLOAT      Course center longitude (default: -120.6294)
  -v, --verbose           Verbose logging
```

### Examples

Process the sample files:
```bash
# Convert sample fairway
python gpx_to_svg.py samples/sample_fairway.gpx -o sample_out.svg -v

# Convert sample green
python gpx_to_svg.py samples/sample_green.gpx -o green_out.svg -v

# Combine all samples into one SVG
python gpx_to_svg.py samples/ -o combined.svg --scale 3.0
```

Override feature type when track names don't follow convention:
```bash
python gpx_to_svg.py unnamed_track.gpx -o bunker.svg --feature-type bunker-edge --hole 5
```

Adjust simplification for noisy GPS data:
```bash
# More aggressive simplification (removes more points)
python gpx_to_svg.py noisy_data.gpx -o clean.svg --simplify-tolerance 1.0

# No simplification (keep all GPS points)
python gpx_to_svg.py precise_data.gpx -o raw.svg --simplify-tolerance 0
```

## Full Workflow

1. **Walk the course** with GPS Tracks app, recording each feature as a
   separate named track (e.g., `fairway-left-1`, `green-edge-1`)

2. **Export GPX files** from the app — one file per track or session

3. **Organize GPX files** into the `gps/` directory:
   ```
   gps/
     hole1_fairway.gpx
     hole1_green.gpx
     hole1_bunkers.gpx
     hole2_fairway.gpx
     ...
   ```

4. **Run the converter** to produce a single SVG:
   ```bash
   cd gps/
   python gpx_to_svg.py . -o ../course_draft.svg --scale 2.0 -v
   ```

5. **Open in Inkscape** — the SVG has proper layers (Fairway, Green, Bunker,
   etc.) that match OPCD conventions. Each layer contains grouped paths
   organized by hole number.

6. **Refine in Inkscape** — adjust control points, close paths that should be
   closed (greens, bunkers), smooth out GPS artifacts, and verify alignment
   between features.

7. **Import into OPCD** for final course assembly in GS Pro.

## OPCD Layer Names

The converter creates the following Inkscape layers, matching OPCD conventions:

| Layer | Contents |
|-------|----------|
| Rough | Rough area boundaries |
| Fairway | Fairway left/right edges |
| Green | Putting green perimeters |
| Bunker | Sand trap perimeters |
| Tee | Tee box perimeters |
| CartPath | Cart path center lines |
| Water | Water hazard shorelines |
| Trees | Tree line boundaries |
| OB | Out of bounds lines |
| Waypoints | Reference markers (tee/green centers, yardage markers) |

## Coordinate System

- GPS coordinates (WGS84) are projected to **UTM Zone 10N** (EPSG:32610)
- The course center is subtracted so the course is centered on the SVG canvas
- Y-axis is flipped (SVG Y increases downward, UTM northing increases upward)
- Default scale is 2.0 SVG units per meter (adjustable with `--scale`)
- Default canvas is 2000x2000 units, fitting a course ~1km across at default scale

## Troubleshooting

**Paths look jagged:** Increase `--scale` or decrease `--simplify-tolerance`

**Paths are too smooth / missing detail:** Decrease `--simplify-tolerance` (try 0.1)
or set to 0 to disable simplification

**Features not on correct layers:** Check that GPX track names follow the
`<feature-type>-<hole>` convention, or use `--feature-type` to override

**Course appears tiny or off-center:** Verify `--center-lat` and `--center-lon`
match the actual course center. Check with `--verbose` to see UTM coordinates.

**"Unknown feature type" warnings:** The track name didn't match any known
feature type. Rename the track in your GPX app or use `--feature-type`.
