#!/bin/bash

# Pre-deployment validation script
# Checks uv lock workflow, Python version, and Streamlit config.

set -euo pipefail

ERRORS=0

echo "=== Pre-deployment Validation ==="
echo ""

# Check uv exists
echo "Checking uv..."
if ! command -v uv >/dev/null 2>&1; then
    echo "✗ uv not found in PATH"
    ERRORS=$((ERRORS + 1))
else
    echo "✓ uv available"
fi
echo ""

# Check dependency manager files
echo "Checking pyproject.toml and uv.lock..."
if [ ! -f "pyproject.toml" ]; then
    echo "✗ pyproject.toml not found"
    ERRORS=$((ERRORS + 1))
else
    echo "✓ pyproject.toml exists"
fi

if [ ! -f "uv.lock" ]; then
    echo "✗ uv.lock not found"
    ERRORS=$((ERRORS + 1))
else
    echo "✓ uv.lock exists"
fi
echo ""

# Check lockfile synchronization
echo "Checking lockfile synchronization..."
if uv lock --check >/dev/null 2>&1; then
    echo "✓ uv.lock is synchronized with pyproject.toml"
else
    echo "✗ uv.lock is out of date (run: uv lock)"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(uv run python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')" 2>/dev/null || true)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ -n "${PYTHON_VERSION}" ] && [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
    echo "✓ Python version: $PYTHON_VERSION (valid)"
else
    echo "✗ Python version: ${PYTHON_VERSION:-unknown} (invalid - requires 3.11+)"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check dependency imports in uv environment
echo "Checking import of core dependencies..."
if uv run python -c "import streamlit, pandas, plotly, sqlmodel, psutil" >/dev/null 2>&1; then
    echo "✓ Core dependencies import successfully"
else
    echo "✗ Failed to import one or more core dependencies in uv environment"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check .streamlit/config.toml exists and is valid TOML
echo "Checking .streamlit/config.toml..."
if [ ! -f ".streamlit/config.toml" ]; then
    echo "✗ .streamlit/config.toml not found"
    ERRORS=$((ERRORS + 1))
else
    echo "✓ .streamlit/config.toml exists"

    # Parse TOML using stdlib (Python 3.11+)
    if uv run python -c "import tomllib; tomllib.load(open('.streamlit/config.toml', 'rb'))" 2>/dev/null; then
        echo "✓ config.toml is valid TOML"
    else
        echo "✗ config.toml is invalid TOML"
        ERRORS=$((ERRORS + 1))
    fi
fi
echo ""

# Summary
echo "=== Summary ==="
if [ $ERRORS -eq 0 ]; then
    echo "✓ All pre-deployment checks passed"
    exit 0
else
    echo "✗ $ERRORS validation error(s) found"
    exit 1
fi
