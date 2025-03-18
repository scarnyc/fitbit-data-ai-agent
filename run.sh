#!/bin/bash

echo "Debugging Replit Python environment..."

# Check environment variables
echo "Checking environment variables..."
echo "PYTHONBIN: $PYTHONBIN"
env | grep PYTHON

# Try direct environment variable first
if [ ! -z "$PYTHONBIN" ]; then
    echo "Found PYTHONBIN environment variable: $PYTHONBIN"
    PYTHON_CMD="$PYTHONBIN"
else
    # Try to find Python in common Replit locations
    echo "Checking standard Replit Python locations..."
    PYTHON_LOCATIONS=(
        "/nix/store/*/bin/python3.12"
        "/nix/store/*/bin/python3"
        "/usr/bin/python3.12"
        "/usr/bin/python3"
    )

    PYTHON_CMD=""
    for pattern in "${PYTHON_LOCATIONS[@]}"; do
        found=$(find /nix/store -path "$pattern" -type f -executable 2>/dev/null | head -n 1)
        if [ ! -z "$found" ]; then
            PYTHON_CMD="$found"
            echo "Found Python at: $PYTHON_CMD"
            break
        fi
    done
fi

# Final check and execution
if [ -z "$PYTHON_CMD" ]; then
    echo "ERROR: Could not find Python executable"
    exit 1
fi

echo "Using Python: $PYTHON_CMD"
$PYTHON_CMD --version

echo "Running main.py..."
$PYTHON_CMD main.py