#!/usr/bin/env bash
set -euo pipefail
cd "/home/atrott/adamArchives/Adam/varMax/PADataset"

python experiments/pa_make_train_manifest.py \
  --grid smoke \
  --paper-sets DISTINCT \
  --unknowns PA1 \
  --seeds 0 \
  --gpus 1 \
  --out manifests/smoke_train_manifest.tsv \
  --epochs 1 \
  --batch-size 2 \
  --save-root results_pa_smoke

python - <<'PY'
import json
from pathlib import Path

cfg = Path('manifests/configs/smoke_train_manifest/distinct_smoke_ent005_lr2e4_unkPA1_c16384_seed0.json')
d = json.loads(cfg.read_text())
d['progress_interval'] = 250
d['overwrite_existing_run'] = True
d['skip_cache_build'] = True
cfg.write_text(json.dumps(d, indent=2))
print(cfg)
print(json.dumps({
    'run_name': d['run_name'],
    'gpu': '1',
    'batch_size': d['batch_size'],
    'epochs': d['epochs'],
    'progress_interval': d['progress_interval'],
    'skip_cache_build': d['skip_cache_build'],
    'cache_root': d['cache_root'],
}, indent=2))
PY
