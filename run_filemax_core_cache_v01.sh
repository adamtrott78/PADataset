#!/usr/bin/env bash
set -euo pipefail

REPO="${REPO:-$HOME/adamArchives/Adam/varMax/PADataset}"
PY="${PY:-$(command -v python)}"

CORE_BANK="${CORE_BANK:-ota_core_high_run01}"
CORE_NOISE="${CORE_NOISE:-high_run01}"
CACHE_LEN="${CACHE_LEN:-16384}"

PROTOCOLS="${PROTOCOLS:-wifi bluetooth zigbee}"
CORE_SHARDS="${CORE_SHARDS:-1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20}"

# MAX MODE. 32 logical CPUs on your Threadripper.
CACHE_FILE_JOBS="${CACHE_FILE_JOBS:-32}"

CACHE_ROOT="${CACHE_ROOT:-$REPO/_feature_cache_nvme/len${CACHE_LEN}/norm/ota__${CORE_BANK}__${CORE_NOISE}}"

cd "$REPO"

mkdir -p results/cache_workers results/buh_logs "$CACHE_ROOT"

TS="$(date +%Y%m%d_%H%M%S)"
LOG="results/buh_logs/filemax_core_cache_${TS}.log"
IMPORTANT="results/buh_logs/filemax_core_cache_${TS}_important.log"
TASKS="results/cache_workers/filemax_core_cache_tasks_${TS}.txt"
JOBLOG="results/cache_workers/filemax_core_cache_joblog_${TS}.txt"

exec > >(tee -a "$LOG") 2>&1

echo "=== FILEMAX CORE CACHE $TS ==="
echo "REPO=$REPO"
echo "PY=$PY"
echo "CORE_BANK=$CORE_BANK"
echo "CORE_NOISE=$CORE_NOISE"
echo "CACHE_LEN=$CACHE_LEN"
echo "CACHE_ROOT=$CACHE_ROOT"
echo "PROTOCOLS=$PROTOCOLS"
echo "CORE_SHARDS=$CORE_SHARDS"
echo "CACHE_FILE_JOBS=$CACHE_FILE_JOBS"
echo ""

echo "=== BUILD FILE-LEVEL CACHE TASKS ==="
: > "$TASKS"

for proto in $PROTOCOLS; do
  for sh in $CORE_SHARDS; do
    sh3="$(printf "%03d" "$sh")"

    find "data/${proto}/ota/${CORE_BANK}" \
      -maxdepth 1 \
      -type f \
      \( -name "${CORE_BANK}__shard_${sh3}__PA1__part_*_of_*.mat" \
         -o -name "${CORE_BANK}__shard_${sh3}__PA2.mat" \
         -o -name "${CORE_BANK}__shard_${sh3}__PA3.mat" \
         -o -name "${CORE_BANK}__shard_${sh3}__PA4.mat" \
         -o -name "${CORE_BANK}__shard_${sh3}__PA8.mat" \) \
      -printf "${proto} ${sh3} %p\n" \
      | sed "s# data/# #"
  done
done | sort > "$TASKS.sorted"
shuf "$TASKS.sorted" > "$TASKS"

TASK_COUNT="$(wc -l < "$TASKS")"
echo "Task file: $TASKS"
echo "Task count: $TASK_COUNT"
echo "Expected task count: 360"

if [[ "$TASK_COUNT" != "360" ]]; then
  echo "ERROR: expected 360 .mat cache tasks but found $TASK_COUNT"
  echo "Task preview:"
  head -n 30 "$TASKS"
  exit 2
fi

awk '
  NF != 3 {
    print "BAD TASK LINE", NR, $0;
    bad=1
  }
  END { exit bad }
' "$TASKS"

echo ""
echo "=== START FILE-LEVEL CACHE ==="

# Prevent BLAS/thread oversubscription. We want 32 independent workers, not 32x32 nested threads.
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
  src={3}

  rel="${src#data/}"

  stem=$(basename "$src" .mat)

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
    2>&1 | tee "results/cache_workers/filemax_cache_${proto}_shard_${sh3}_${stem}_${TS}.log"

  h5=$(find "$CACHE_ROOT" -maxdepth 1 -type f -name "*${stem}.h5" | head -n 1 || true)
  if [[ -z "$h5" || ! -f "$h5" ]]; then
    echo "ERROR: h5 not found after cache | src=${rel} | stem=${stem}"
    exit 3
  fi

  bytes=$(stat -c%s "$h5")
  echo "FILECACHE DONE | proto=${proto} | shard=${sh3} | src=${rel} | h5=${h5} | bytes=${bytes}"
' :::: "$TASKS" \
  2>&1 | tee "results/cache_workers/filemax_core_cache_${TS}_all.log"

echo ""
echo "=== VERIFY FILEMAX CACHE ==="
H5_COUNT="$(find "$CACHE_ROOT" -maxdepth 1 -type f -name '*.h5' | wc -l)"
echo "H5 count: $H5_COUNT / 360"

if [[ "$H5_COUNT" != "360" ]]; then
  echo "ERROR: expected 360 h5 files but found $H5_COUNT"
  exit 4
fi

du -sh "$CACHE_ROOT" || true

echo ""
echo "=== DONE ==="
echo "Full log     : $LOG"
echo "Important log: $IMPORTANT"
echo "Task file    : $TASKS"
echo "Joblog       : $JOBLOG"
echo "Cache log    : results/cache_workers/filemax_core_cache_${TS}_all.log"

grep -E '^(===|Task count|Expected task count|FILECACHE START|FILECACHE DONE|H5 count|ERROR|DONE)' \
  "$LOG" > "$IMPORTANT" || true
