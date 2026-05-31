# Polycam LIDAR Scanning Guide — Putting Greens

**Purpose:** Capture high-resolution 3D scans of each putting green using the iPhone Pro's LIDAR sensor. These scans provide the detailed contour data needed to create realistic green surfaces in GS Pro.

**Why greens matter most:** In golf simulation, the putting green is where players spend the most strokes and notice inaccuracies immediately. A slope that is off by even 1 degree changes how a putt breaks. Fairway and rough contours can be approximated from LIDAR DEM data, but greens need finer detail than public LIDAR provides (typically 1-2m resolution). Polycam scanning at close range gives us centimeter-level contour resolution.

---

## Equipment

- **iPhone Pro** (12 Pro or newer) with LIDAR sensor
- **Polycam app** (free version works; Pro version gives higher export resolution)
- **Fully charged phone** (LIDAR scanning drains battery fast)
- **10-15 minutes per green** (budget ~2 hours for all 9 greens)

---

## Polycam App Settings

Before starting your first scan:

1. Open Polycam and go to **Settings**
2. **Scan mode:** LIDAR (not Photo mode — we need the depth data)
3. **Quality:** High (uses more battery but captures finer detail)
4. **Range:** 5 meters (we will be scanning from close range)
5. **Confidence filter:** Medium (filters out noisy readings)
6. **Point density:** High
7. **Mesh processing:** ON (we need the mesh, not just point cloud)

---

## Scanning Procedure — Per Green

### Preparation

1. **Wait for the green to be clear of players.** You will be walking on and around the green for 10-15 minutes.
2. **Remove the flag stick** if possible, or note its position (the stick creates scanning artifacts).
3. **Ideal conditions:**
   - Overcast sky or consistent shade (strong shadows create contrast issues)
   - Dry green (wet grass reflects the LIDAR beam unpredictably)
   - Morning or late afternoon (avoid direct overhead sun)
4. **Note the time and conditions** on your survey template

### Scanning Walk Pattern

The key is **complete coverage with significant overlap**. Think of it like mowing the green in stripes.

```
START → → → → → → → →
← ← ← ← ← ← ← ← ←
→ → → → → → → → → →
← ← ← ← ← ← ← ← ←
→ → → → → → → → → →
```

**Detailed steps:**

1. **Start the scan** from one edge of the green (pick a consistent starting point — front-left is a good convention)
2. **Hold the phone at waist height** (~1 meter above the ground), angled slightly downward (about 30-45 degrees from vertical)
3. **Walk slowly in parallel lines** across the green, like mowing stripes:
   - Walk from one side to the other
   - Step sideways about 1 meter (3 feet)
   - Walk back the other direction
   - Repeat until you have covered the entire green
4. **Overlap each stripe by about 30%** — this gives the stitching algorithm enough matching points
5. **Walk the perimeter** after the stripes — one complete loop around the green edge, staying on the fringe. This captures the green edge contour and helps Polycam close the model.
6. **Walk any severe slopes or tiers** a second time, moving perpendicular to the slope direction. Slopes are the hardest features to capture accurately.
7. **Stop the scan**

### Scan Height and Angle

- **Height:** Hold the phone 0.8-1.2 meters above the ground (waist to chest height)
- **Angle:** 30-45 degrees from vertical (so the LIDAR hits the ground, not the horizon)
- **Keep it steady:** Walk smoothly. Avoid jerky movements. Pretend you are carrying a tray of drinks.
- **Speed:** Slower than normal walking pace. About 0.5-1 meter per second.
- **Watch the screen:** Polycam shows a live mesh being built. Make sure the mesh is filling in without gaps. If you see holes, slow down and re-scan that area.

### What to Capture

Scan area should include:
- The **entire putting surface**
- The **fringe/collar** around the green (at least 1 meter beyond the green edge)
- Any **greenside bunker edges** that connect to the green
- The **approach area** just in front of the green (2-3 meters)

This gives context for how the green sits relative to the surrounding terrain.

### Common Problems and Solutions

| Problem | Cause | Solution |
|---------|-------|----------|
| Holes in the mesh | Moved too fast, or skipped an area | Slow down. Re-scan gaps before stopping. |
| Mesh "floats" or has layers | Phone height changed too quickly | Keep phone at consistent height. |
| Green surface looks flat (no contour) | LIDAR noise exceeds the subtle slope | Use Pro version for higher resolution. Make two passes. |
| Scan includes unwanted objects | Players, flags, shadows | Scan when green is clear. Remove flag. |
| Scan drifts (edges don't align) | Too large an area without overlap | Increase stripe overlap to 50%. |
| App crashes mid-scan | Memory limits | Scan only the green + 2m fringe, not the entire hole area. |

---

## After Scanning Each Green

1. **Review the scan** in Polycam before leaving the green
   - Rotate the 3D model to check for gaps
   - Look at it from the side — does the contour look right? Can you see the slope?
   - If it looks wrong, delete and re-scan (better now than discovering later)

2. **Name the scan** in Polycam: `Green_H<N>` (e.g., `Green_H1`, `Green_H2`, etc.)

3. **Take reference photos** (these help when integrating the scan into the terrain):
   - Photo from front of green looking at surface
   - Photo from behind green
   - Photo from left side
   - Photo from right side
   - Note the pin position (distance from front edge and left/right position)

---

## Exporting Scans

After completing all 9 greens, export each scan:

### Export Settings

1. Open each scan in Polycam
2. Tap **Export**
3. Choose format: **PLY** (preferred) or **OBJ**
   - PLY preserves vertex colors and is well-supported by Blender
   - OBJ works too but may lose some color data
4. Resolution: **High** (we need the detail for green contours)
5. Coordinate system: **Y-up** (Blender default)
6. Include textures: **No** (we will apply our own materials in Blender)

### File Organization

Save exported scans to the project:
```
ellensburg-gc-gspro/
  polycam/
    green_H1.ply
    green_H2.ply
    green_H3.ply
    ...
    green_H9.ply
```

### Backup

- Also save the original Polycam project files (in-app cloud backup or export as Polycam format)
- These let you re-export at different resolutions if needed

---

## Integration into Blender

The Polycam scans will be imported into the Blender terrain model during the modeling phase.

**Workflow (done later, during Blender modeling):**

1. Import the PLY file into Blender (`File > Import > Stanford PLY`)
2. The scan will be in its own local coordinate system — it needs to be aligned with the terrain
3. **Alignment process:**
   - Position the scan over the corresponding green area on the terrain mesh
   - Use the 3-point alignment technique: match 3 points on the scan edge to 3 points on the terrain GPS green outline
   - Fine-tune by comparing scan edges to the GPS-derived green perimeter
4. **Merge the scan contour into the terrain:**
   - Use the scan mesh to sculpt/deform the terrain mesh in the green area
   - The Blender Shrinkwrap modifier can project terrain vertices onto the scan surface
   - Or: manually sculpt the terrain to match the scan contours
5. **Delete the scan mesh** after the terrain has been shaped (keep it in a hidden collection for reference)
6. **Apply the Green material** from `materials.py`

---

## Tips for Best Results at Ellensburg GC

- **Wind:** The Kittitas Valley is notoriously windy. This does not affect LIDAR scanning directly, but it makes it harder to hold the phone steady. Consider scanning early morning when wind is typically calmest.
- **Sun angle:** Summer afternoon sun in Central WA is intense. Scan in morning or wait for cloud cover if possible. The LIDAR works in any light, but the RGB camera (which provides color for the scan mesh) struggles with harsh shadows.
- **Green speed:** Ellensburg GC greens are typically medium speed (Stimp ~8-9). Note the mowing pattern direction — it affects how greens appear visually.
- **Irrigation heads:** You may see sprinkler heads on the green edges. These are minor but try not to spend extra time scanning them — they create artifacts.
- **Small greens:** Several greens at Ellensburg GC are compact. This is actually good — smaller greens are easier to scan completely and produce higher-resolution results.

---

## Time Budget

| Green | Estimated Scan Time | Notes |
|-------|-------------------|-------|
| H1 | 10-12 min | |
| H2 | 10-12 min | |
| H3 | 8-10 min | Par 3, likely smaller green |
| H4 | 10-12 min | |
| H5 | 12-15 min | Par 5 green, likely larger with more contour |
| H6 | 8-10 min | Par 3 |
| H7 | 10-12 min | |
| H8 | 12-15 min | Par 5 green |
| H9 | 10-12 min | |
| **Total** | **~90-110 min** | |

Add 15-20 minutes for setup, troubleshooting, and export.

Total Polycam session: approximately **2 hours**.

This can be done on the same visit as GPS data collection or on a separate trip. If combining with GPS collection, do the Polycam scans first (morning, calmer wind, better light) and GPS tracks after.
