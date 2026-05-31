# On-Course Data Collection Guide

**Course:** Ellensburg Golf Club, Ellensburg WA
**Purpose:** Collect GPS tracks, LIDAR scans, and photos to build a GS Pro course
**Estimated time:** 3-4 hours (can be split across two sessions)

---

## Equipment Checklist

Before heading to the course, make sure you have:

- [ ] **iPhone** (Pro model preferred for Polycam LIDAR scanning)
- [ ] **GPS Tracks app** by Dmitry Vakhtin (installed and tested before the round)
- [ ] **Polycam app** (for green scanning — requires iPhone Pro with LIDAR)
- [ ] **Fully charged phone** — GPS and LIDAR scanning drain battery fast
- [ ] **Portable charger / battery pack** — essential for 3-4 hours of GPS recording
- [ ] **Lightning/USB-C cable** for the charger
- [ ] **Printed copy of hole_survey_template.md** (9 copies, one per hole)
- [ ] **Pen or pencil** (pen smears in rain; pencil works in any weather)
- [ ] **Tape measure** (25 ft / 8m retractable) — for tee box dimensions, bunker depth
- [ ] **Yardage book** from the pro shop (if available) — helpful reference
- [ ] **Water bottle and sunscreen** — Kittitas Valley sun is strong and there is little shade
- [ ] **Hat and sunglasses** — you will be looking at your phone screen a lot outdoors
- [ ] **Golf cart** (recommended) — speeds up perimeter walking between holes

**Optional but helpful:**
- [ ] Rangefinder — for verifying distances
- [ ] Small notebook — backup if phone notes fail
- [ ] Clip or armband phone mount — keeps hands free while walking

---

## GPS App Setup (GPS Tracks by Dmitry Vakhtin)

This app was chosen because it records continuous GPS tracks (not just waypoints), exports in GPX format, and has good battery management.

### Before You Leave Home

1. **Install GPS Tracks** from the App Store
2. Open the app and grant location permissions ("Always Allow" for best accuracy)
3. Go to Settings in the app:
   - **Recording interval:** 1 second (maximum accuracy)
   - **Distance filter:** 1 meter (records a point every 1m of movement)
   - **Accuracy filter:** 10 meters (discard points with >10m estimated error)
   - **Auto-pause:** OFF (we want continuous recording)
   - **Map type:** Satellite (helps you see where you are relative to features)
   - **Units:** Meters (matches our GIS pipeline)
4. **Test it:** Take a 5-minute walk around your neighborhood. Verify the track shows up accurately on the satellite view. Export as GPX and confirm the file is readable.

### At the Course

- **Keep the app in the foreground** as much as possible (better GPS accuracy)
- If you must switch apps (for photos or Polycam), the GPS continues recording in the background, but accuracy may decrease
- **Start a new track segment** for each distinct feature (named per the convention below)

---

## Track Naming Convention

Every GPS track segment must be named so the converter script can identify it. Use this format:

```
H<hole>_<feature>_<detail>
```

**Examples:**
| Track name | What it is |
|---|---|
| `H1_TEE` | Hole 1 tee box perimeter |
| `H1_FW_LEFT` | Hole 1 fairway left edge |
| `H1_FW_RIGHT` | Hole 1 fairway right edge |
| `H1_GREEN` | Hole 1 green perimeter |
| `H1_BUNKER_GL` | Hole 1 bunker, greenside left |
| `H1_BUNKER_GR` | Hole 1 bunker, greenside right |
| `H1_BUNKER_FW` | Hole 1 fairway bunker |
| `H1_WATER` | Hole 1 water hazard edge |
| `H1_OB_LEFT` | Hole 1 OB line, left side |
| `H1_CARTPATH` | Hole 1 cart path edges |

**Feature codes:**
- `TEE` — tee box perimeter
- `FW_LEFT` / `FW_RIGHT` — fairway edges
- `GREEN` — putting green perimeter
- `BUNKER_GL` / `BUNKER_GR` / `BUNKER_FW` — bunkers (greenside left/right, fairway)
- `WATER` — water hazard edge
- `OB_LEFT` / `OB_RIGHT` — out-of-bounds line
- `CARTPATH` — cart path edges
- `TREE_<species>` — notable tree positions (point waypoints, not tracks)

---

## Per-Hole Procedure

Work through each hole systematically. This takes 15-25 minutes per hole depending on complexity.

### 1. Tee Box (3-5 min)

1. **Start a new track:** Name it `H<N>_TEE`
2. Walk to the back-left corner of the tee box
3. **Stand still for 5 seconds** (GPS averages for better accuracy)
4. Walk slowly along the back edge to the back-right corner
5. Continue around all four sides, pausing 3-5 seconds at each corner
6. Return to starting point to close the shape
7. **Stop the track**
8. **Measure the tee box** with tape measure: length and width in meters
9. **Take photos:** One from the tee looking down the fairway (the "tee shot view")
10. Note the tee surface condition on your survey template

### 2. Fairway (5-10 min)

1. **Start track:** `H<N>_FW_LEFT`
2. Walk the left edge of the fairway from tee to green
3. Walk where the fairway meets the rough — the mowing line
4. Walk at a normal pace but slow down at bends or contour changes
5. **Stop track** when you reach the green collar
6. **Start track:** `H<N>_FW_RIGHT`
7. Walk back up the right edge of the fairway to the tee
8. **Stop track**

**Tips:**
- At the landing zone (where drives typically land), note the fairway width on your template
- If the fairway has a significant dogleg, walk the inside corner carefully — this shape matters
- Note any fairway contour changes: mounding, swales, drainage channels

### 3. Green (5-8 min)

The green is the most important feature. Take your time here.

1. **Start track:** `H<N>_GREEN`
2. Walk the perimeter of the green, staying on the edge where putting surface meets fringe
3. Walk slowly — 1-2 steps per second maximum
4. **Pause 5 seconds at each "corner"** of the green shape (where the edge changes direction)
5. Close the loop back to your starting point
6. **Stop track**
7. **Note the pin position** — estimate it as "front-left", "center", "back-right", etc., and distance from edges
8. **Estimate the green slope:** Which direction does it tilt? Front-to-back? Left-to-right? Subtle or severe?
9. **Polycam scan** (see separate Polycam guide): Do a full green scan
10. **Take photos:** Approach view, and views from all four sides showing green contour

### 4. Bunkers (2-5 min each)

1. **Start track:** `H<N>_BUNKER_<position>` (e.g., `H3_BUNKER_GR`)
2. Walk the top edge of the bunker (the lip)
3. Walk slowly around the full perimeter
4. Close the loop
5. **Stop track**
6. **Measure depth:** Step into the bunker and estimate or measure the depth from lip to sand
7. **Note the sand condition:** Firm? Fluffy? Wet? (affects how it plays)
8. **Take a photo** from outside showing the bunker shape and face
9. Repeat for each bunker on the hole

### 5. Water Hazards (2-5 min)

1. **Start track:** `H<N>_WATER`
2. Walk the edge of the water hazard that is in play (the side facing the fairway)
3. If it's a pond or creek that wraps around, walk the full perimeter
4. Note whether there are hazard stakes (red or yellow) and their positions
5. **Stop track**
6. **Take a photo** showing the water feature relative to the fairway/green

### 6. Out of Bounds (1-3 min)

1. **Start track:** `H<N>_OB_<side>`
2. Walk along the OB line (fence, stakes, property line)
3. Only need to record the section that is in play (not distant boundaries)
4. **Stop track**
5. Note whether OB is marked by stakes, fence, road edge, etc.

### 7. Notable Trees (1-2 min)

For significant trees that affect play (strategic trees, specimen trees):

1. **Add a waypoint** (single GPS point, not a track)
2. Name it `H<N>_TREE_<species>` (e.g., `H4_TREE_PINE`)
3. Estimate the height and canopy spread
4. Note whether it's a single tree or group
5. **Take a photo** if it's a significant course feature

### 8. Cart Path (1-2 min)

Cart paths define hard surfaces in the course model.

1. **Start track:** `H<N>_CARTPATH`
2. Walk one edge of the cart path through the hole
3. **Stop track**
4. Note the path width (typically 8-10 feet)
5. Note the surface (asphalt, concrete, gravel)

### 9. Final Photos for the Hole

Before moving to the next hole, take these shots:

- [ ] **Tee shot view** — standing on the tee, looking at the target
- [ ] **Approach view** — from 150 yards out (or wherever the typical approach shot is)
- [ ] **Green approach** — from just in front of the green, looking at the putting surface
- [ ] **Green back** — from behind the green, looking back toward the tee
- [ ] **Each bunker** — showing shape and depth
- [ ] **Each water hazard** — showing relation to play
- [ ] **Any unique features** — bridges, rock walls, drainage, etc.

**Photo naming:** Use your phone's default naming. We will organize by timestamp later. But try to take them in the order listed above so they are sequential in the camera roll.

---

## After the Round

### Immediately (same day)

1. **Back up all GPS data:**
   - Export all tracks from GPS Tracks as GPX files
   - Export to Files app or iCloud Drive
   - Copy to your computer: `ellensburg-gc-gspro/gps/raw/`

2. **Back up all photos:**
   - Create a folder per hole: `photos/hole_01/`, `photos/hole_02/`, etc.
   - Sort photos into the correct hole folders
   - If you took general course photos (clubhouse, parking, overview), put them in `photos/course/`

3. **Back up Polycam scans:**
   - Export each green scan (see Polycam guide for format)
   - Save to: `ellensburg-gc-gspro/polycam/`
   - Name each export: `green_H1.ply`, `green_H2.ply`, etc.

4. **Review your survey templates:**
   - Fill in any fields you missed while your memory is fresh
   - Note any GPS tracks you think might have issues (bad signal, walked wrong edge, etc.)

### Within a few days

5. **Post-process GPS tracks:**
   - Open the GPX files in QGIS
   - Check each track against the satellite image — does it match the feature it should?
   - Clean up any tracks that have GPS wander (smooth them or re-digitize from satellite)
   - Convert all tracks to the project CRS (UTM Zone 10N, EPSG:32610)

6. **Organize everything in the repo:**
   - GPS tracks: `gps/processed/`
   - Photos: `photos/` (organized by hole)
   - Polycam: `polycam/`
   - Survey templates: `guides/surveys/`

---

## Tips for Accuracy

- **Walk slowly near corners and edges.** GPS points spaced 1m apart give you much better curve definition.
- **Stop and stand still for 5 seconds at key corners.** The GPS averages multiple readings, giving a more accurate position.
- **Stay consistent about which edge you walk.** Always walk the mowing line (fairway/rough boundary), not somewhere vaguely "near" the edge.
- **Use waypoint markers at key spots.** If the GPS app supports it, drop a named waypoint at tee centers, green centers, and pin positions.
- **Check your phone's GPS accuracy.** GPS Tracks shows the current estimated accuracy. If it says >5m, slow down and wait for it to improve before recording critical features.
- **Time of day matters.** GPS accuracy is generally best mid-morning. Avoid recording right at sunrise or sunset when satellite geometry may be poor.
- **Kittitas Valley note:** GPS should be excellent here. The valley is flat and open with no tall buildings or canyons to block signals. Tree cover on holes 4, 5, 7, 8 may slightly reduce accuracy under the canopy.

## If GPS Signal Is Bad

This is unlikely at Ellensburg (open valley, no tall buildings), but if you encounter poor accuracy:

1. **Wait 30-60 seconds** for the phone to acquire more satellites
2. **Move to an open area** if you are under dense tree cover
3. **Restart the GPS app** (sometimes helps reset the satellite fix)
4. **Note on your survey template** which tracks had bad signal
5. **Worst case:** Take extra photos from multiple angles. You can digitize features from satellite imagery + photos in QGIS later.

---

## Estimated Time Budget

| Activity | Time |
|---|---|
| Setup and first tee | 15 min |
| Holes 1-3 (simpler holes) | 45-60 min |
| Holes 4-5 (tree-lined, river) | 40-50 min |
| Hole 6 (par 3, quick) | 15-20 min |
| Holes 7-8 (tree-lined, river) | 40-50 min |
| Hole 9 | 15-25 min |
| Clubhouse area and general photos | 15-20 min |
| **Total** | **3-4 hours** |

If you split across two sessions, a natural break point is after hole 5 (roughly halfway through the course and a good stopping point near the turn area).

---

## Quick Reference Card

Print this and tape it to your scorecard:

```
TRACK NAMES: H<N>_<FEATURE>
  TEE, FW_LEFT, FW_RIGHT, GREEN
  BUNKER_GL, BUNKER_GR, BUNKER_FW
  WATER, OB_LEFT, OB_RIGHT, CARTPATH

AT EACH HOLE:
  1. Tee box: walk perimeter, measure, photo
  2. Fairway: walk both edges tee-to-green
  3. Green: walk perimeter SLOWLY, Polycam scan
  4. Bunkers: walk each lip, measure depth
  5. Hazards: walk edges
  6. OB: walk stakes/fence
  7. Trees: waypoint notable ones
  8. Cart path: walk one edge
  9. Photos: tee view, approach, green (all sides), bunkers, hazards

ACCURACY:
  - Walk slow (1-2 steps/sec) on edges
  - Stop 5 sec at corners
  - Stay on the mowing line
```
