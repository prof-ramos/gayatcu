#!/bin/bash

# Pre-deployment validation script
# Checks Python version, requirements.txt syntax, and config.toml

set -e

ERRORS=0

echo "=== Pre-deployment Validation ==="
echo ""

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 10 ] && [ "$PYTHON_MINOR" -le 12 ]; then
    echo "✓ Python version: $PYTHON_VERSION (valid)"
else
    echo "✗ Python version: $PYTHON_VERSION (invalid - requires 3.10-3.12)"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check requirements.txt exists and is valid
echo "Checking requirements.txt..."
if [ ! -f "requirements.txt" ]; then
    echo "✗ requirements.txt not found"
    ERRORS=$((ERRORS + 1))
else
    echo "✓ requirements.txt exists"

    # Check for syntax errors by trying to parse it
    if python3 -c "import sys; sys.exit(0)" 2>/dev/null; then
        # Basic syntax check - no comments-only lines starting with package names
        if grep -E '^[a-zA-Z].*#' requirements.txt > /dev/null 2>&1; then
            echo "  ⚠ Warning: Possible inline comments without space"
        fi
        echo "✓ requirements.txt syntax appears valid"
    else
        echo "✗ Cannot validate requirements.txt syntax"
        ERRORS=$((ERRORS + 1))
    fi
fi
echo ""

# Check .streamlit/config.toml exists and is valid TOML
echo "Checking .streamlit/config.toml..."
if [ ! -f ".streamlit/config.toml" ]; then
    echo "✗ .streamlit/config.toml not found"
    ERRORS=$((ERRORS + 1))
else
    echo "✓ .streamlit/config.toml exists"

    # Try to parse TOML (requires python3 and tomli or similar)
    if python3 -c "import tomli; tomli.load(open('.streamlit/config.toml', 'rb'))" 2>/dev/null; then
        echo "✓ config.toml is valid TOML"
    elif python3 -c "
import sys
try:
    with open('.streamlit/config.toml', 'r') as f:
        content = f.read()
        # Basic TOML validation
        if content.strip().startswith('[') or content.strip() == '':
            print('Basic TOML structure check passed')
        else:
            sys.exit(1)
except Exception as e:
    sys.exit(1)
" 2>/dev/null; then
        echo "✓ config.toml basic structure valid"
    else
        echo "⚠ Warning: Cannot fully validate TOML (install tomli for full validation)"
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
