#!/usr/bin/env bash
set -euo pipefail

REPO="${REPO:-$HOME/adamArchives/Adam/varMax/PADataset}"
PY="${PY:-$(command -v python)}"

cd "$REPO"

mkdir -p commands/train results/train_workers manifests results

usage() {
  cat <<'EOF'
Usage:
  bash scripts/train/pa_trainctl.sh <command> [args...]

Commands:
  smoke-manifest [gpu=1] [batch=2] [epochs=1] [progress_interval=250]
      Build the functional smoke manifest/config.

  run [manifest=manifests/smoke_train_manifest.tsv] [jobs=1]
      Run manifest through GNU parallel launcher.

  direct-smoke
      Run current smoke config directly without GNU parallel.

  watch [manifest=manifests/smoke_train_manifest.tsv] [refresh=2]
      Launch live dashboard.

  reduce [results_root=results_pa_smoke] [out=results/smoke_train_leaderboard.csv]
      Aggregate summary.json files into CSV.

  verify <run_dir>
      Verify expected training artifacts.

  audit-cache
      Audit feature cache H5 readability.

  status
      Show git/log/GPU quick status.
EOF
}

record_command() {
  local name="$1"
  local body="$2"
  local ts
  ts="$(date +%Y%m%d_%H%M%S)"
  local file="commands/train/${ts}_${name}.sh"

  {
    echo '#!/usr/bin/env bash'
    echo 'set -euo pipefail'
    echo "cd \"$REPO\""
    echo
    echo "$body"
  } > "$file"
  chmod +x "$file"
  echo "Recorded command: $file"
}

cmd="${1:-}"
shift || true

case "$cmd" in
  smoke-manifest)
    gpu="${1:-1}"
    batch="${2:-2}"
    epochs="${3:-1}"
    interval="${4:-250}"

    body="python experiments/pa_make_train_manifest.py \\
  --grid smoke \\
  --paper-sets DISTINCT \\
  --unknowns PA1 \\
  --seeds 0 \\
  --gpus $gpu \\
  --out manifests/smoke_train_manifest.tsv \\
  --epochs $epochs \\
  --batch-size $batch \\
  --save-root results_pa_smoke

python - <<'PY'
import json
from pathlib import Path

cfg = Path('manifests/configs/smoke_train_manifest/distinct_smoke_ent005_lr2e4_unkPA1_c16384_seed0.json')
d = json.loads(cfg.read_text())
d['progress_interval'] = $interval
d['overwrite_existing_run'] = True
d['skip_cache_build'] = True
cfg.write_text(json.dumps(d, indent=2))
print(cfg)
print(json.dumps({
    'run_name': d['run_name'],
    'gpu': '$gpu',
    'batch_size': d['batch_size'],
    'epochs': d['epochs'],
    'progress_interval': d['progress_interval'],
    'skip_cache_build': d['skip_cache_build'],
    'cache_root': d['cache_root'],
}, indent=2))
PY"

    record_command "smoke_manifest" "$body"
    eval "$body"
    ;;

  run)
    manifest="${1:-manifests/smoke_train_manifest.tsv}"
    jobs="${2:-1}"
    body="JOBS=$jobs bash scripts/train/run_pa_train_parallel.sh $manifest"
    record_command "run_manifest" "$body"
    eval "$body"
    ;;

  direct-smoke)
    cfg="manifests/configs/smoke_train_manifest/distinct_smoke_ent005_lr2e4_unkPA1_c16384_seed0.json"
    body="CUDA_VISIBLE_DEVICES=1 \\
PYTHONUNBUFFERED=1 \\
OMP_NUM_THREADS=1 \\
MKL_NUM_THREADS=1 \\
OPENBLAS_NUM_THREADS=1 \\
NUMEXPR_NUM_THREADS=1 \\
VECLIB_MAXIMUM_THREADS=1 \\
python experiments/pa_train_one.py \\
  --cfg $cfg \\
  2>&1 | tee results/train_workers/direct_smoke_debug_\\\$(date +%Y%m%d_%H%M%S).log"
    record_command "direct_smoke" "$body"
    eval "$body"
    ;;

  watch)
    manifest="${1:-manifests/smoke_train_manifest.tsv}"
    refresh="${2:-2}"
    body="REFRESH=$refresh bash scripts/train/pa_dashboard.sh $manifest"
    record_command "watch_manifest" "$body"
    eval "$body"
    ;;

  reduce)
    results_root="${1:-results_pa_smoke}"
    out="${2:-results/smoke_train_leaderboard.csv}"
    body="python experiments/pa_reduce_train_summaries.py --results-root $results_root --out $out"
    record_command "reduce_train" "$body"
    eval "$body"
    ;;

  verify)
    run_dir="${1:-}"
    if [[ -z "$run_dir" ]]; then
      echo "ERROR: verify requires run_dir"
      exit 2
    fi

    echo "RUN_DIR=$run_dir"
    for f in config.json best_model.pt final_model.pt history.json summary.json train_complete.json train_progress.json; do
      if [[ -f "$run_dir/$f" ]]; then
        echo "OK $f"
      else
        echo "MISSING $f"
      fi
    done
    ;;

  audit-cache)
    body="python experiments/pa_audit_feature_cache.py"
    record_command "audit_cache" "$body"
    eval "$body"
    ;;

  status)
    echo "=== git ==="
    git branch --show-current || true
    git log --oneline -3 || true
    git status --short || true
    echo
    echo "=== gpu ==="
    nvidia-smi || true
    echo
    echo "=== workers ==="
    pgrep -af 'pa_train_one.py|run_pa_train_parallel|parallel.*manifest' || true
    ;;

  ""|-h|--help|help)
    usage
    ;;

  *)
    echo "ERROR: unknown command: $cmd"
    usage
    exit 2
    ;;
esac
