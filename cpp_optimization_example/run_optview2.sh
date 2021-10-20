#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")" || exit 1

echo "Running make..."
make

echo "Running optview2..."
../opt-viewer.py --output-dir ./html_output --source-dir ./ ./yaml_optimization_remarks


