#!/usr/bin/env bash
#
# Ellensburg GC GS Pro Course Build - Setup Script
# Installs all dependencies on macOS via Homebrew
#
set -euo pipefail

echo "============================================"
echo "Ellensburg GC - GS Pro Course Build Setup"
echo "============================================"
echo ""

# ---- Check for Homebrew ----
if ! command -v brew &> /dev/null; then
    echo "ERROR: Homebrew is required. Install from https://brew.sh"
    exit 1
fi
echo "[OK] Homebrew found"

# ---- System dependencies via Homebrew ----
echo ""
echo "Installing system dependencies..."

BREW_PACKAGES=(gdal pdal proj)
for pkg in "${BREW_PACKAGES[@]}"; do
    if brew list "$pkg" &> /dev/null; then
        echo "  [OK] $pkg already installed"
    else
        echo "  [..] Installing $pkg..."
        brew install "$pkg"
        echo "  [OK] $pkg installed"
    fi
done

# ---- Python check ----
echo ""
PYTHON=""
if command -v python3 &> /dev/null; then
    PYTHON="python3"
elif command -v python &> /dev/null; then
    PYTHON="python"
else
    echo "ERROR: Python 3 is required. Install via: brew install python"
    exit 1
fi

PY_VERSION=$($PYTHON --version 2>&1 | awk '{print $2}')
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 9 ]); then
    echo "ERROR: Python 3.9+ required (found $PY_VERSION)"
    exit 1
fi
echo "[OK] Python $PY_VERSION found"

# ---- Virtual environment ----
echo ""
VENV_DIR="$(cd "$(dirname "$0")" && pwd)/.venv"

if [ -d "$VENV_DIR" ]; then
    echo "[OK] Virtual environment already exists at $VENV_DIR"
else
    echo "Creating virtual environment..."
    $PYTHON -m venv "$VENV_DIR"
    echo "[OK] Virtual environment created"
fi

source "$VENV_DIR/bin/activate"
echo "[OK] Virtual environment activated"

# ---- Python dependencies ----
echo ""
echo "Installing Python dependencies..."
pip install --upgrade pip setuptools wheel -q
pip install -r "$(dirname "$0")/requirements.txt" -q
echo "[OK] Python dependencies installed"

# ---- Verify critical tools ----
echo ""
echo "Verifying installations..."

check_tool() {
    if command -v "$1" &> /dev/null; then
        echo "  [OK] $1 found: $($1 --version 2>&1 | head -1)"
    else
        echo "  [!!] $1 not found - may need manual installation"
    fi
}

check_tool pdal
check_tool gdalinfo
check_tool ogr2ogr
check_python_module() {
    if $PYTHON -c "import $1" 2>/dev/null; then
        echo "  [OK] Python module: $1"
    else
        echo "  [!!] Python module missing: $1"
    fi
}

check_python_module rasterio
check_python_module numpy
check_python_module scipy
check_python_module shapely
check_python_module pyproj

# ---- Additional software (manual install) ----
echo ""
echo "============================================"
echo "Manual installs needed (if not already done):"
echo "============================================"
echo ""
echo "1. QGIS           → https://qgis.org/download/"
echo "2. Inkscape        → https://inkscape.org/release/"
echo "3. Blender (3.6+)  → https://www.blender.org/download/"
echo "4. Unity Hub       → https://unity.com/download"
echo "5. GS Pro          → https://gsprogolf.com/"
echo "6. OPCD Plugin     → Install via Blender preferences"
echo ""
echo "Optional for data collection:"
echo "7. GPS Tracks (iOS) → App Store"
echo "8. Polycam (iOS)    → App Store"
echo ""
echo "============================================"
echo "Setup complete! Activate the venv with:"
echo "  source .venv/bin/activate"
echo "============================================"
