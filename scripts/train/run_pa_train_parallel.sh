#!/usr/bin/env bash
set -euo pipefail

REPO="${REPO:-$HOME/adamArchives/Adam/varMax/PADataset}"
PY="${PY:-$(command -v python)}"
MANIFEST="${1:-manifests/train_manifest.tsv}"
JOBS="${JOBS:-2}"
LOGROOT="${LOGROOT:-results/train_workers}"
TS="$(date +%Y%m%d_%H%M%S)"

cd "$REPO"
mkdir -p "$LOGROOT"

if ! command -v parallel >/dev/null 2>&1; then
  echo "ERROR: GNU parallel is not installed or not on PATH."
  exit 2
fi

if [[ ! -f "$MANIFEST" ]]; then
  echo "ERROR: manifest not found: $MANIFEST"
  exit 3
fi

JOBLOG="$LOGROOT/train_joblog_${TS}.txt"
LOG="$LOGROOT/train_all_${TS}.log"

export REPO PY LOGROOT TS

echo "=== PA TRAIN PARALLEL ==="
echo "REPO=$REPO"
echo "PY=$PY"
echo "MANIFEST=$MANIFEST"
echo "JOBS=$JOBS"
echo "LOG=$LOG"
echo "JOBLOG=$JOBLOG"
echo

parallel --line-buffer --colsep '\t' \
  --header : \
  --joblog "$JOBLOG" \
  --tag --tagstring '{run_name}|gpu={gpu}' \
  --halt soon,fail=1 \
  -j "$JOBS" \
'
  set -euo pipefail

  run_name="{run_name}"
  gpu="{gpu}"
  cfg_path="{cfg_path}"

  export CUDA_VISIBLE_DEVICES="$gpu"
  export OMP_NUM_THREADS=1
  export MKL_NUM_THREADS=1
  export OPENBLAS_NUM_THREADS=1
  export NUMEXPR_NUM_THREADS=1
  export VECLIB_MAXIMUM_THREADS=1
  export PYTHONUNBUFFERED=1
  export TQDM_MININTERVAL=2

  exec 9>"/tmp/padataset_gpu_$gpu.lock"
  flock -n 9 || {
    echo "TRAIN ERROR | run_name=$run_name | gpu=$gpu | error=gpu_lock_busy"
    exit 99
  }

  "$PY" "$REPO/experiments/pa_train_one.py" \
    --cfg "$REPO/$cfg_path" \
    2>&1 | tee "$REPO/$LOGROOT/"$run_name"_"$TS".log"
' :::: "$MANIFEST" \
  2>&1 | tee "$LOG"

echo
echo "Training launcher finished."
echo "Log:    $LOG"
echo "Joblog: $JOBLOG"
