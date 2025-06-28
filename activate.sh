#!/bin/bash
# Quick activation script for OptView2 virtual environment

if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Run './setup_venv.sh' first."
    exit 1
fi

source venv/bin/activate

echo "Virtual environment activated!"
echo "You can now run: python opt-viewer.py --help"
echo "To deactivate: deactivate"
