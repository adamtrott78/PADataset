#!/usr/bin/env bash
set -euo pipefail

REPO="${REPO:-$HOME/adamArchives/Adam/varMax/PADataset}"
MANIFEST="${1:-manifests/smoke_train_manifest.tsv}"
REFRESH="${REFRESH:-2}"

cd "$REPO"
python experiments/pa_dashboard.py "$MANIFEST" --refresh "$REFRESH"
