# Ellensburg GC → GSPro: Build Runbook

> **Reality check first.** A playable GSPro course is built through an interactive,
> GUI-driven pipeline on **your** PC: Inkscape → Blender (OPCD add-on) → Unity
> (grass/materials) → GreenKeeper V4 → GSPro. GSPro loads a **Unity-built course
> bundle** — there is no file anyone can hand you that you "drop into GSPro and play."
> No tool or assistant can do the Unity/OPCD steps for you; they require the apps below
> running locally. Current community estimate: **40–100+ hours** for a full course.
> But you can **play your first 2 holes before finishing the rest** — that's the real
> near-term target.

Source of truth (do the steps in this order): **The Perfect Lie / Between Two Biomes
"Building GSPro Courses – Complete Guide" (OPCD V4, updated Feb 2026)** and the **OPCD Discord**.
Links at the bottom.

---

## 1. Apps to download

Versions below are **confirmed from the OPCD "None to Done" V4 master doc** — OPCD is version-pinned, so match these exactly. Newer is NOT better here.

| App | Version (confirmed) | Why | Where |
|---|---|---|---|
| **Unity (via Unity Hub)** | **Unity 2018** | Where the course is assembled, grass (Stix 3DG) generated, and the bundle built | unity.com → Unity Hub → install the **2018** version OPCD specifies. ⚠️ This is old on purpose — do not install a newer Unity. |
| **Blender** | **4.0.2** | OPCD Blender add-on tools | blender.org → get **4.0.2** specifically. ⚠️ You have 5.1.2 installed — that worked for our custom scripts, but the **OPCD add-on wants 4.0.2**. Install 4.0.2 alongside it. |
| **OPCD V4 Toolset** (Blender add-on) | V4 | The actual course-building tool + Arborist | OPCD Discord → there's a **"Registering for the OPCD Toolset (V4)"** step; after registering you get an **OPCD Downloads drive** where the toolset, Arborist, and base Unity project live. |
| **Inkscape** | latest (V4.1 workflow) | Draw/spline the course feature layers | inkscape.org |
| **GreenKeeper V4** | V4 | Routing, tees, pins, OOB, hazards, scorecard; loads course into GSPro | Same OPCD/SGT ecosystem; install video: youtu.be/oOMUsH7_N0c |
| **GSPro** | current | The simulator itself | You have this |
| **QGIS + CloudCompare** | per OPCD support files | Re-derive OPCD's inner/outer RAW heightmaps from raw LIDAR | OPCD provides QGIS support files (Google Drive, linked in the doc). See heightmap note in §2. |

**Minimum to get moving:** join OPCD Discord → register for the toolset → install **Unity 2018**, **Blender 4.0.2**, the **OPCD add-on**, and **Inkscape**.

**Heads up — "Clender":** OPCD V4 uses a cloud service called the *Clender*. You submit your splined SVG to it and it returns cut blend files (you don't mesh-cut locally). Expect "Submit to Clender → wait → verify returned blend files" as a real step.

---

## 2. What in this repo is actually reusable (and what isn't)

Honest inventory after confirming the real OPCD V4 pipeline:

**Reusable / valuable**
- `lidar/data/laz/*.laz` + `lidar/data/dem_raw.tif` — **the raw LIDAR + DEM are the real prize.** OPCD §3 re-derives terrain its own way (CloudCompare/QGIS → **inner + outer heightmaps in RAW format** → Unity terrain), using OPCD's QGIS support files. Our downloaded LAZ tiles and DEM feed directly into those QGIS steps, so the hours spent fetching/processing LIDAR aren't wasted.
- ⚠️ **Correction to my earlier claim:** the finished `ellensburg_gc_heightmap_4096.png` is NOT a drop-in for OPCD. OPCD wants paired inner/outer **RAW** heightmaps imported to a **Unity terrain**, not a single PNG used for Blender displacement. The PNG/`.blend` are our own format. Keep the PNG as a reference/sanity-check of the elevation range; re-generate OPCD's heightmaps via its QGIS workflow.
- `svg/osm_course_opcd.svg` — a **rough OSM tracing** with the right OPCD-style layers (Fairway, Green, Rough, Tee, Bunker, Water, OB, CartPath) and per-hole groups. Good as a **starting template to trace over in Inkscape** — NOT accurate enough to use as-is (it's satellite-estimated and overflows the canvas).
- `course_data/greenkeeper_v4.json`, `holes.md`, `environment.json` — **reference data** for GreenKeeper V4 setup (yardages, par, grass types, climate). ⚠️ Treat as a data sheet to type from, **not** a direct import file — GreenKeeper V4 is configured in its GUI.

**NOT on the GSPro path (visualization/reference only)**
- `blender/ellensburg_gc.blend`, `blender/import_dem.py`, `blender/materials.py`, `blender/vegetation.json` — these are a **custom, homegrown** Blender approach. The real workflow uses the **OPCD add-on** (different objects, naming, and a Unity hand-off the GSPro exporter expects) and generates grass in **Unity (Stix 3DG)**, not via these materials. Keep them for visualization, but they do **not** become the GSPro course. Vegetation in the real pipeline = **OPCD Arborist**, not `vegetation.json`.

---

## 3. Your files → the 9 guide sections

| Guide section | What you do | Your starting material |
|---|---|---|
| 1. Getting Started | Install Unity + OPCD; learn Unity basics | — |
| 2. Lidar Data & Overlays | OPCD's QGIS/CloudCompare → inner/outer RAW heightmaps → Unity terrain + satellite overlays | Partial head start: our `*.laz` tiles + `dem_raw.tif` feed OPCD's QGIS steps. You still run OPCD's process (its support files) to make the RAW heightmaps. Our PNG is reference only. |
| 3. Inkscape – Splining | Draw fairway/green/rough/tee/bunker/OB splines | `svg/osm_course_opcd.svg` as a trace-over template; refine with your **field GPS** when you have it |
| 4. Blender (OPCD tools) | Conform meshes, dig terrain, bunkers/water | heightmap + splines |
| 5. Unity Setup & Materials | Materials, post-processing, **Stix 3D grass** | — |
| 6. Vegetation | Plant trees via **OPCD Arborist** | `vegetation.json` species list is a useful reference (Ponderosa/cottonwood/willow are correct for Kittitas Valley) |
| 7. GreenKeeper V4 | Routing, OOB, hazards, tees, pins, scorecard | `greenkeeper_v4.json` + `holes.md` as your data sheet |
| 8. Finishing & Publishing | Hole markers, perf checks, submit | — |
| 9. Advanced | Tee boxes, satellite shader, clubhouses, etc. | — |

---

## 4. Elevation reference numbers (OPCD §3 asks for max/min when building heightmaps)

- Resolution: **4096 × 4096**, 16-bit grayscale
- World size (XY): **2056 m × 1663 m**
- Elevation (Z) displacement range: **34.09 m** (gray 0 = 475.14 m, gray 65535 = 509.23 m)
- Pixel size: **0.50 m/px**
- CRS of source: EPSG:32610 (UTM 10N)

---

## 5. The fastest route to "I can press play"

1. Install the apps in §1 (correct Unity version!).
2. Guide §2: drop the **existing heightmap** into Unity — you skip the entire lidar pipeline most people grind for hours.
3. Guide §3: in Inkscape, **spline just holes 1–2**, tracing over `osm_course_opcd.svg` (good enough for a greybox; refine with field GPS later).
4. Guide §4–5: run those two holes through OPCD/Blender → Unity, basic materials + grass.
5. Guide §7: GreenKeeper V4 — set up just those 2 holes (tees, pins, par) from `greenkeeper_v4.json`.
6. **Load into GSPro and play 2 holes.** This proves the whole toolchain works on your rig before you invest in field data or the other 7 holes.

**Do this greybox FIRST.** The biggest risk isn't the field work — it's discovering the Unity/GreenKeeper export is broken *after* you've collected perfect GPS data. Prove the pipeline end-to-end on 2 ugly holes first.

---

## 6. Where to get help (you'll need it — this is a deep toolchain)

- **Between Two Biomes** YouTube — step-by-step videos for every section above.
- **OPCD Discord** — where the add-on lives and where designers actively help.
- The written OPCD V4 doc (Google Doc, linked from the guide).

---

## 7. What I (assistant) can still do for you between sessions

I can't run Unity/OPCD/GreenKeeper, but I can compress your manual time:
- Generate **per-hole spline SVGs** sized to the heightmap, so Inkscape tracing is faster.
- Turn `greenkeeper_v4.json` into a **clean printable data sheet** for GreenKeeper entry.
- Write a **hole-by-hole Blender/OPCD cheat sheet** keyed to the videos.
- Refine the OSM SVG (fix the canvas overflow, align to the 2056×1663 m extent).
- Troubleshoot errors you hit, as you hit them.

Tell me which and I'll grind on it.
