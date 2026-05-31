# ===========================================================================
# Ellensburg Golf Club — LIDAR to Heightmap Pipeline
# ===========================================================================
#
# Usage:
#   make all         — full pipeline: download → DEM → heightmap
#   make download    — download LAZ tiles from WA DNR
#   make dem         — process LAZ → raw DEM via PDAL
#   make heightmap   — clip, smooth, export 16-bit heightmap PNG
#   make clean       — remove intermediate files
#   make distclean   — remove everything (including downloads)
#   make info        — show pipeline status
#
# Requirements:
#   - Python 3.10+ with: requests, rasterio, scipy, Pillow, numpy
#   - PDAL (with LAZ support)
#   - Optional: scikit-image (for resampling)
#
# ===========================================================================

SHELL := /bin/bash
.DEFAULT_GOAL := all

# ---------------------------------------------------------------------------
# Directories
# ---------------------------------------------------------------------------
LIDAR_DIR   := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
DATA_DIR    := $(LIDAR_DIR)data
LAZ_DIR     := $(DATA_DIR)/laz

# ---------------------------------------------------------------------------
# Files
# ---------------------------------------------------------------------------
BOUNDARY     := $(LIDAR_DIR)course_boundary.geojson
PIPELINE     := $(LIDAR_DIR)pdal_pipeline.json
DEM_RAW      := $(DATA_DIR)/dem_raw.tif
DEM_CLIPPED  := $(DATA_DIR)/ellensburg_gc_dem_clipped.tif
DEM_PROC     := $(DATA_DIR)/ellensburg_gc_dem_processed.tif
HEIGHTMAP    := $(DATA_DIR)/ellensburg_gc_heightmap_4096.png
METADATA     := $(DATA_DIR)/ellensburg_gc_heightmap_meta.json

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PYTHON       := $(shell [ -f $(dir $(abspath $(lastword $(MAKEFILE_LIST))))../.venv/bin/python3 ] && echo $(dir $(abspath $(lastword $(MAKEFILE_LIST))))../.venv/bin/python3 || echo python3)
PDAL         := pdal
RESOLUTION   := 4096
SIGMA        := 1.0
VERBOSE      := -v
# macOS: Homebrew Python 3.14 needs this to find the correct libexpat
export DYLD_LIBRARY_PATH := /opt/homebrew/opt/expat/lib:$(DYLD_LIBRARY_PATH)

# ---------------------------------------------------------------------------
# Phony targets
# ---------------------------------------------------------------------------
.PHONY: all download dem heightmap clean distclean info list-tiles check-deps

all: heightmap

# ---------------------------------------------------------------------------
# Download LAZ tiles from WA DNR
# ---------------------------------------------------------------------------
download: check-deps-download $(LAZ_DIR)
	@echo "=== Downloading LIDAR tiles ==="
	$(PYTHON) $(LIDAR_DIR)download_lidar.py \
		--output-dir $(LAZ_DIR) \
		$(VERBOSE)

list-tiles: check-deps-download
	@echo "=== Listing available LIDAR tiles ==="
	$(PYTHON) $(LIDAR_DIR)download_lidar.py \
		--list-only \
		$(VERBOSE)

$(LAZ_DIR):
	mkdir -p $(LAZ_DIR)

# ---------------------------------------------------------------------------
# Generate raw DEM from LAZ via PDAL
# ---------------------------------------------------------------------------
dem: $(DEM_RAW)

$(DEM_RAW): $(PIPELINE) | $(DATA_DIR)
	@echo "=== Building DEM from LAZ files ==="
	@# Check that LAZ files exist
	@if ! ls $(LAZ_DIR)/*.laz 1>/dev/null 2>&1; then \
		echo "ERROR: No LAZ files found in $(LAZ_DIR)"; \
		echo "Run 'make download' first."; \
		exit 1; \
	fi
	@echo "Processing $$(ls $(LAZ_DIR)/*.laz | wc -l | tr -d ' ') LAZ file(s)..."
	@# Generate a pipeline JSON with explicit file paths (PDAL can't expand globs)
	$(PYTHON) -c "\
import json, glob, sys; \
files = sorted(glob.glob('$(LAZ_DIR)/*.laz')); \
pipe = json.load(open('$(PIPELINE)')); \
readers = [{'type': 'readers.las', 'filename': f, 'tag': 'r'+str(i)} for i, f in enumerate(files)]; \
merge = {'type': 'filters.merge', 'inputs': ['r'+str(i) for i in range(len(files))]}; \
rest = [s for s in pipe['pipeline'] if not s.get('type','').startswith('readers')]; \
out = {'pipeline': readers + [merge] + rest}; \
json.dump(out, open('/tmp/pdal_pipeline_expanded.json', 'w'), indent=2); \
print(f'Generated pipeline for {len(files)} files')"
	$(PDAL) pipeline /tmp/pdal_pipeline_expanded.json
	@echo "Raw DEM created: $(DEM_RAW)"
	@echo "Size: $$(du -h $(DEM_RAW) | cut -f1)"

$(DATA_DIR):
	mkdir -p $(DATA_DIR)

# ---------------------------------------------------------------------------
# Process DEM → Heightmap
# ---------------------------------------------------------------------------
heightmap: $(HEIGHTMAP)

$(HEIGHTMAP): $(DEM_RAW) $(BOUNDARY)
	@echo "=== Generating heightmap ==="
	$(PYTHON) $(LIDAR_DIR)process_dem.py \
		--input $(DEM_RAW) \
		--boundary $(BOUNDARY) \
		--output-dir $(DATA_DIR) \
		--resolution $(RESOLUTION) \
		--sigma $(SIGMA) \
		$(VERBOSE)
	@echo "Heightmap created: $(HEIGHTMAP)"

# ---------------------------------------------------------------------------
# Dependency checks
# ---------------------------------------------------------------------------
check-deps:
	@echo "Checking dependencies..."
	@command -v $(PYTHON) >/dev/null 2>&1 || { echo "ERROR: $(PYTHON) not found"; exit 1; }
	@command -v $(PDAL) >/dev/null 2>&1   || { echo "ERROR: pdal not found. Install with: conda install -c conda-forge pdal"; exit 1; }
	@$(PYTHON) -c "import rasterio"  2>/dev/null || { echo "ERROR: rasterio not installed. pip install rasterio"; exit 1; }
	@$(PYTHON) -c "import scipy"     2>/dev/null || { echo "ERROR: scipy not installed. pip install scipy"; exit 1; }
	@$(PYTHON) -c "import numpy"     2>/dev/null || { echo "ERROR: numpy not installed. pip install numpy"; exit 1; }
	@$(PYTHON) -c "import PIL"       2>/dev/null || { echo "ERROR: Pillow not installed. pip install Pillow"; exit 1; }
	@$(PYTHON) -c "import requests"  2>/dev/null || { echo "ERROR: requests not installed. pip install requests"; exit 1; }
	@echo "All dependencies OK."

check-deps-download:
	@command -v $(PYTHON) >/dev/null 2>&1 || { echo "ERROR: $(PYTHON) not found"; exit 1; }
	@$(PYTHON) -c "import requests" 2>/dev/null || { echo "ERROR: requests not installed. pip install requests"; exit 1; }

# ---------------------------------------------------------------------------
# Info / status
# ---------------------------------------------------------------------------
info:
	@echo "=== Pipeline Status ==="
	@echo ""
	@echo "Directories:"
	@echo "  LIDAR dir:  $(LIDAR_DIR)"
	@echo "  Data dir:   $(DATA_DIR)"
	@echo "  LAZ dir:    $(LAZ_DIR)"
	@echo ""
	@echo "Files:"
	@printf "  %-40s %s\n" "Course boundary:" "$$([ -f $(BOUNDARY) ] && echo 'OK' || echo 'MISSING')"
	@printf "  %-40s %s\n" "PDAL pipeline:" "$$([ -f $(PIPELINE) ] && echo 'OK' || echo 'MISSING')"
	@printf "  %-40s %s\n" "LAZ tiles:" "$$(ls $(LAZ_DIR)/*.laz 2>/dev/null | wc -l | tr -d ' ') file(s)"
	@printf "  %-40s %s\n" "Raw DEM:" "$$([ -f $(DEM_RAW) ] && echo 'OK ('$$(du -h $(DEM_RAW) | cut -f1)')' || echo 'NOT BUILT')"
	@printf "  %-40s %s\n" "Clipped DEM:" "$$([ -f $(DEM_CLIPPED) ] && echo 'OK ('$$(du -h $(DEM_CLIPPED) | cut -f1)')' || echo 'NOT BUILT')"
	@printf "  %-40s %s\n" "Processed DEM:" "$$([ -f $(DEM_PROC) ] && echo 'OK ('$$(du -h $(DEM_PROC) | cut -f1)')' || echo 'NOT BUILT')"
	@printf "  %-40s %s\n" "Heightmap PNG:" "$$([ -f $(HEIGHTMAP) ] && echo 'OK ('$$(du -h $(HEIGHTMAP) | cut -f1)')' || echo 'NOT BUILT')"
	@printf "  %-40s %s\n" "Metadata JSON:" "$$([ -f $(METADATA) ] && echo 'OK' || echo 'NOT BUILT')"
	@echo ""
	@if [ -f $(METADATA) ]; then \
		echo "Metadata:"; \
		cat $(METADATA) | $(PYTHON) -m json.tool 2>/dev/null || cat $(METADATA); \
		echo ""; \
	fi

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------
clean:
	@echo "Removing intermediate files..."
	rm -f $(DEM_RAW) $(DEM_CLIPPED) $(DEM_PROC)
	@echo "Done. (LAZ downloads and final outputs preserved)"

distclean: clean
	@echo "Removing all generated files (including downloads and heightmap)..."
	rm -f $(HEIGHTMAP) $(METADATA)
	rm -rf $(LAZ_DIR)
	@echo "Done."
