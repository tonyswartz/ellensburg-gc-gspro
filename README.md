# Ellensburg Golf Club — GSPro Course Build

Building [Ellensburg Golf Club](https://www.ellensburggolf.com/) as a playable course in [GSPro](https://gsprogolf.com/) golf simulator.

**Course:** 9 holes · Par 35 · ~3,075 yds (blue) · Ellensburg, WA
**Location:** 3231 Thorp Hwy S, Ellensburg, WA 98926 · 47.0193°N, 120.6294°W · ~1,510–1,545 ft
A semi-arid Central Washington course along the Yakima River, Ponderosa pines, and persistent Kittitas Valley wind.

---

## 👋 Start here (new collaborator)

This repo is **preparation work and reference data**, not a finished course. There is **no file here you can drop into GSPro and play.** A GSPro course is built through a manual, GUI-driven toolchain on your own PC and takes **40–100+ hours**.

**Read these two files first, in order:**
1. **[`BUILD_GSPRO_RUNBOOK.md`](BUILD_GSPRO_RUNBOOK.md)** — the real build pipeline, exact app versions, what in this repo is reusable, and the fastest route to a playable test.
2. **[`CLAUDE_NEXT_STEPS.md`](CLAUDE_NEXT_STEPS.md)** — fuller project history and the data that still needs ground-truthing.

The authoritative external guide is **OPCD "None to Done" (V4 Toolset)** — videos by Between Two Biomes, written guide + Discord linked in the runbook. Follow it; this repo just front-loads some of its inputs.

---

## The real pipeline (OPCD V4)

```
Raw LIDAR (.laz) + DEM ──► OPCD QGIS/CloudCompare ──► inner+outer RAW heightmaps ──► Unity terrain
                                                                                         │
GPS field data ──► Inkscape splines (over satellite overlay) ──► submit SVG to "Clender" ─┘
                                                                                         ▼
                              Blender 4.0.2 + OPCD add-on (conform meshes, bunkers, water, objects)
                                                                                         ▼
                              Unity 2018 (materials/MAHS shader, Stix 3DG grass, OPCD Arborist trees, build course)
                                                                                         ▼
                              GreenKeeper V4 (routing, tees, pins, OOB, scorecard) ──► GSPro
```

⚠️ The custom `blender/` scripts in this repo are **NOT** the OPCD toolset — see "What's reusable" below.

## Apps to install (versions are pinned — match them exactly)

| App | Version | Notes |
|---|---|---|
| Unity (via Unity Hub) | **2018** | Old on purpose. Do not install a newer Unity. |
| Blender | **4.0.2** | The OPCD add-on requires this. (Not the latest.) |
| OPCD V4 Toolset + Arborist | V4 | Join the [OPCD Discord](https://discord.gg/HrmpTbqavq), complete "Register for the Toolset," then download from the OPCD Downloads drive. |
| Inkscape | latest | Course splining. |
| GreenKeeper V4 | V4 | Last tool in the chain; install video in runbook §1. |
| GSPro | current | The simulator (paid). |
| QGIS + CloudCompare | per OPCD support files | Only to re-derive heightmaps from the raw LIDAR. |

## First milestone: 2 playable holes

The OPCD guide is explicitly structured to **build 2 holes → play them in GSPro → then do the rest.** Do that first. It proves the whole toolchain works on your rig before investing in full field data. Step-by-step in the runbook.

---

## What's in this repo (reusable vs off-path)

**Reusable / valuable**
- `lidar/data/laz/*.laz` + `lidar/data/dem_raw.tif` — raw LIDAR + DEM. Feed OPCD's QGIS terrain steps. (The 6 tiles are already downloaded.)
- `lidar/` scripts — `download_lidar.py` (USGS TNM API), `process_dem.py`, `Makefile` — how the DEM was built.
- `gps/gpx_to_svg.py` — converts GPS tracks → Inkscape SVG with OPCD-style layers. Use after field collection.
- `course_data/` — `greenkeeper_v4.json`, `holes.md`, `environment.json`: a **data sheet** to type from during GreenKeeper setup (not a direct import).
- `svg/osm_course_opcd.svg` — rough OSM tracing of the 9 holes; a loose template to trace over in Inkscape (not GPS-accurate).
- `guides/` — field protocols to print and take to the course.

**Off-path (visualization/reference only — does NOT become the GSPro course)**
- `blender/ellensburg_gc.blend`, `import_dem.py`, `materials.py`, `vegetation.json` — a homegrown Blender approach. OPCD imports the heightmap into **Unity** and generates grass (Stix 3DG) and trees (Arborist) there. Keep for visualization; don't build the course on it.
- `lidar/data/ellensburg_gc_heightmap_4096.png` — our PNG heightmap. OPCD wants **inner/outer RAW** heightmaps on a Unity terrain instead. Useful only as an elevation sanity-check (range 475.1–509.2 m / 34.1 m relief).

---

## The real bottleneck: on-course data collection

Everything downstream depends on real field data, which is **not collected yet**. With an iPhone + GPS Tracks app + Polycam, walk the course and record:

- Fairway edges, green perimeters, bunker edges, tee-box corners (GPS, ~1s interval)
- Green surface contours (Polycam LiDAR scan — highest-value data)
- Tee/approach/green photos per hole

Protocol: [`guides/data_collection.md`](guides/data_collection.md) · Greens: [`guides/polycam_guide.md`](guides/polycam_guide.md) · Print [`guides/templates/hole_survey_template.md`](guides/templates/hole_survey_template.md) ×9. Budget ~4–6 hours on site.

## Current data status

| Data point | Status |
|---|---|
| Location, layout, pars, yardages, scorecard | ✅ Confirmed |
| Raw LIDAR + DEM | ✅ Downloaded & processed |
| Hole routing | ⚠️ Estimated from satellite/OSM |
| Green shapes & contours | ❌ Needs field collection |
| Tee, pin, bunker, OB, cart-path positions | ⚠️/❌ Estimated or missing |
| Tree positions | ⚠️ Estimated (species correct for region) |

## Repo structure

```
ellensburg-gc-gspro/
├── README.md                  ← you are here
├── BUILD_GSPRO_RUNBOOK.md     ← read this 1st: real pipeline + app versions
├── CLAUDE_NEXT_STEPS.md       ← read this 2nd: history + data to verify
├── lidar/                     ← LIDAR fetch + DEM (raw data is reusable)
│   └── data/laz/, dem_raw.tif, *_heightmap_4096.png (reference)
├── gps/gpx_to_svg.py          ← GPS tracks → OPCD-layered SVG
├── course_data/               ← greenkeeper_v4.json, holes.md, environment.json
├── svg/osm_course_opcd.svg    ← rough OSM trace template for Inkscape
├── blender/                   ← custom scripts (visualization only — see above)
├── guides/                    ← field-collection protocols
└── checklist/build_checklist.md
```

## License

MIT — see [LICENSE](LICENSE). Community contributions welcome, especially field data from anyone who plays Ellensburg GC.
