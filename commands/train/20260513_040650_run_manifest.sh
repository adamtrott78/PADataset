#!/usr/bin/env bash
set -euo pipefail
cd "/home/atrott/adamArchives/Adam/varMax/PADataset"

JOBS=1 bash scripts/train/run_pa_train_parallel.sh manifests/smoke_train_manifest.tsv
