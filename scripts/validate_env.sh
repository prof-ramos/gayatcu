#!/bin/bash

# Environment validation script
# Checks secrets.toml template, data directory, and runs tests

set -e

ERRORS=0

echo "=== Environment Validation ==="
echo ""

# Check .streamlit/secrets.toml template exists
echo "Checking .streamlit/secrets.toml template..."
if [ ! -f ".streamlit/secrets.toml" ]; then
    echo "✗ .streamlit/secrets.toml not found"
    ERRORS=$((ERRORS + 1))
else
    echo "✓ .streamlit/secrets.toml exists"

    # Check if it's a template (contains placeholders)
    if grep -qE '(TODO|your_key_here|CHANGE_ME|<insert>|PLACEHOLDER)' ".streamlit/secrets.toml" 2>/dev/null; then
        echo "  ⚠ Warning: secrets.toml appears to be a template with placeholders"
    else
        echo "  ✓ secrets.toml appears to be configured"
    fi
fi
echo ""

# Check data/ directory exists
echo "Checking data directory..."
if [ ! -d "data" ]; then
    echo "✗ data/ directory not found"
    ERRORS=$((ERRORS + 1))
else
    echo "✓ data/ directory exists"

    # Check if directory is writable
    if [ -w "data" ]; then
        echo "  ✓ data/ directory is writable"
    else
        echo "  ⚠ Warning: data/ directory is not writable"
    fi
fi
echo ""

# Run pytest if available
echo "Checking for pytest..."
if ! command -v pytest &> /dev/null; then
    echo "⚠ pytest not found - skipping tests"
    echo "  Install with: pip install pytest"
else
    echo "✓ pytest found - running tests..."
    if pytest -v 2>&1; then
        echo "✓ All tests passed"
    else
        echo "✗ Some tests failed"
        ERRORS=$((ERRORS + 1))
    fi
fi
echo ""

# Summary
echo "=== Summary ==="
if [ $ERRORS -eq 0 ]; then
    echo "✓ All environment checks passed"
    exit 0
else
    echo "✗ $ERRORS validation error(s) found"
    exit 1
fi
