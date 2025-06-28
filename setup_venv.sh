#!/bin/bash

# OptView2 Virtual Environment Setup Script
# This script creates a virtual environment and installs dependencies

set -e  # Exit on any error

VENV_DIR="venv"
PYTHON_CMD="python3"

echo "Setting up virtual environment for OptView2..."

# Check if Python 3 is available
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8 or later"
    exit 1
fi

# Check Python version (require 3.8+)
PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
REQUIRED_VERSION="3.8"

if ! $PYTHON_CMD -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "Error: Python $PYTHON_VERSION is installed, but OptView2 requires Python $REQUIRED_VERSION or later"
    exit 1
fi

echo "Found Python $PYTHON_VERSION ✓"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv $VENV_DIR
    echo "Virtual environment created in $VENV_DIR/"
else
    echo "Virtual environment already exists in $VENV_DIR/"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source $VENV_DIR/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "To activate the virtual environment in the future, run:"
echo "  source venv/bin/activate"
echo ""
echo "To deactivate the virtual environment, run:"
echo "  deactivate"
echo ""
echo "To run OptView2:"
echo "  source venv/bin/activate"
echo "  python opt-viewer.py --help"
