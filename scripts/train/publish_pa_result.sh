#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: bash scripts/train/publish_pa_result.sh <source_csv> <published_name_without_csv>"
  echo
  echo "Example:"
  echo "  bash scripts/train/publish_pa_result.sh results/catalog_tiny_smoke_leaderboard.csv catalog_tiny_smoke_leaderboard"
  exit 2
fi

SRC="$1"
NAME="$2"

DEST_DIR="docs/experiments/run_results"
DEST="$DEST_DIR/${NAME}.csv"

mkdir -p "$DEST_DIR"

if [[ ! -f "$SRC" ]]; then
  echo "ERROR: source CSV not found: $SRC"
  exit 1
fi

cp "$SRC" "$DEST"

echo "Published:"
echo "  $SRC"
echo "to:"
echo "  $DEST"

git add -f "$DEST"
git status --short "$DEST"
