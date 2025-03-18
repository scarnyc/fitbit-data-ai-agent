#!/bin/bash
# save this as run.sh

echo "Debugging Replit Python environment..."

# Try to find Python in common Replit locations
echo "Checking standard Replit Python locations..."
PYTHON_LOCATIONS=(
  "/nix/store/$(ls -t /nix/store | grep python | head -n 1)/bin/python"
  "/opt/virtualenvs/python3/bin/python"
  "/usr/bin/python3"
  "/home/runner/$(ls -t /home/runner | grep python | head -n 1)/bin/python"
  "/opt/python/latest/bin/python"
  "/opt/python/3.12/bin/python"
  "/opt/python/3.10/bin/python"
  "./venv/bin/python"
)

PYTHON_CMD=""
for location in "${PYTHON_LOCATIONS[@]}"; do
  echo "Checking: $location"
  if [ -x "$location" ]; then
    PYTHON_CMD="$location"
    echo "Found Python at: $PYTHON_CMD"
    break
  fi
done

if [ -z "$PYTHON_CMD" ]; then
  # Try using the nix path directly from replit.nix
  echo "Attempting to find Python using nix..."
  
  # Look for Python in nix directories
  NIX_PYTHON=$(find /nix/store -name "python3" -type f -executable | head -n 1)
  if [ ! -z "$NIX_PYTHON" ]; then
    PYTHON_CMD="$NIX_PYTHON"
    echo "Found Python at: $PYTHON_CMD"
  fi
fi

# If still not found, try dynamic lookup from the nix path
if [ -z "$PYTHON_CMD" ]; then
  echo "Attempting nix-shell Python lookup..."
  PYTHON_CMD=$(which python3 || which python || echo "")
fi

# Final fallback - try python3.12 explicitly since that's in the module config
if [ -z "$PYTHON_CMD" ]; then
  echo "Trying explicit python3.12 command..."
  PYTHON_CMD="python3.12"
fi

# Check if we found a valid Python command
if [ -z "$PYTHON_CMD" ]; then
  echo "ERROR: Could not find any Python executable."
  echo "Please check your Replit configuration and ensure Python is properly set up."
  exit 1
fi

# Print Python version for debugging
echo "Using Python command: $PYTHON_CMD"
$PYTHON_CMD --version

# Run the main script
echo "Running main.py..."
$PYTHON_CMD main.py
