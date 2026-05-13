#!/usr/bin/env bash
set -euo pipefail

REPO="${REPO:-$HOME/adamArchives/Adam/varMax/PADataset}"
PY="${PY:-$(command -v python)}"
CORE_BANK="${CORE_BANK:-ota_core_high_run01}"
CORE_NOISE="${CORE_NOISE:-high_run01}"
CACHE_LEN="${CACHE_LEN:-16384}"
CACHE_ROOT="${CACHE_ROOT:-$REPO/_feature_cache_nvme/len${CACHE_LEN}/norm/ota__${CORE_BANK}__${CORE_NOISE}}"
CACHE_FILE_JOBS="${CACHE_FILE_JOBS:-56}"

cd "$REPO"
mkdir -p results/cache_workers results/buh_logs

TS="$(date +%Y%m%d_%H%M%S)"
TASKS="results/cache_workers/missing_h5_tasks_${TS}.txt"
LOG="results/cache_workers/missing_h5_cache_${TS}_all.log"
JOBLOG="results/cache_workers/missing_h5_cache_joblog_${TS}.txt"

python - <<'PY' > "$TASKS"
from pathlib import Path
import os

ROOT = Path.cwd()
CORE_BANK = "ota_core_high_run01"
CACHE_ROOT = ROOT / "_feature_cache_nvme/len16384/norm/ota__ota_core_high_run01__high_run01"
protocols = ["wifi", "bluetooth", "zigbee"]

def expected_sources(proto, sh):
    sh3 = f"{sh:03d}"
    d = ROOT / "data" / proto / "ota" / CORE_BANK
    files = [
        d / f"{CORE_BANK}__shard_{sh3}__PA1__part_01_of_02.mat",
        d / f"{CORE_BANK}__shard_{sh3}__PA1__part_02_of_02.mat",
        d / f"{CORE_BANK}__shard_{sh3}__PA2.mat",
        d / f"{CORE_BANK}__shard_{sh3}__PA3.mat",
        d / f"{CORE_BANK}__shard_{sh3}__PA4.mat",
        d / f"{CORE_BANK}__shard_{sh3}__PA8.mat",
    ]
    return files

for proto in protocols:
    for sh in range(1, 21):
        sh3 = f"{sh:03d}"
        for src in expected_sources(proto, sh):
            if not src.exists():
                continue
            stem = src.name.replace(".mat", "")
            exists = bool(list(CACHE_ROOT.glob(f"*{proto}*{stem}.h5")))
            if not exists:
                rel = src.relative_to(ROOT / "data")
                print(proto, sh3, rel)
PY

echo "Missing-task count:"
wc -l "$TASKS"
echo
cat "$TASKS"

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1

export REPO PY CACHE_ROOT CACHE_LEN CORE_BANK CORE_NOISE TS

parallel --line-buffer --colsep ' ' \
  --joblog "$JOBLOG" \
  --tag --tagstring '{1}|shard={2}|{3}' \
  --halt now,fail=1 \
  -j "$CACHE_FILE_JOBS" \
'
  set -euo pipefail

  proto={1}
  sh3={2}
  rel={3}
  stem=$(basename "$rel" .mat)

  echo "FILECACHE START | proto=${proto} | shard=${sh3} | src=${rel}"

  "$PY" "$REPO/cacheBuild.py" \
    --data-root "$REPO/data" \
    --cache-root "$CACHE_ROOT" \
    --cache-len "$CACHE_LEN" \
    --normalize \
    --source-type ota \
    --source-name "$CORE_BANK" \
    --dataset-tag "$CORE_BANK" \
    --noise-tag "$CORE_NOISE" \
    --source-glob "$rel" \
    2>&1 | tee "results/cache_workers/missing_h5_${proto}_shard_${sh3}_${stem}_${TS}.log"

  h5=$(find "$CACHE_ROOT" -maxdepth 1 -type f -name "*${proto}*${stem}.h5" | head -n 1 || true)
  if [[ -z "$h5" || ! -f "$h5" ]]; then
    echo "ERROR: protocol-specific h5 not found after cache | proto=${proto} | src=${rel} | stem=${stem}"
    exit 3
  fi

  bytes=$(stat -c%s "$h5")
  echo "FILECACHE DONE | proto=${proto} | shard=${sh3} | src=${rel} | h5=${h5} | bytes=${bytes}"
' :::: "$TASKS" \
  2>&1 | tee "$LOG"

echo
echo "=== FINAL COUNT ==="
find "$CACHE_ROOT" -maxdepth 1 -type f -name '*.h5' | wc -l
du -sh "$CACHE_ROOT"

echo
echo "=== JOB FAILURES ==="
awk 'NR==1 || $7 != 0 {print}' "$JOBLOG" | column -t || true
