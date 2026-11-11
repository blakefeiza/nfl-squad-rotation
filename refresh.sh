#!/bin/bash
# Refresh the squad-rotation page with the latest games: re-download nflverse data and rebuild data/*.json.
# Usage: bash refresh.sh [SEASON]      (all 32 teams; default 2026)
set -e
cd "$(dirname "$0")"
python3 prep.py --season="${1:-2026}"
echo "data/ rebuilt. Preview with:  python3 -m http.server 4330"
