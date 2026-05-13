#!/usr/bin/env bash
set -euo pipefail

# ---------------- config ----------------
REPO="${REPO:-$HOME/adamArchives/Adam/varMax/PADataset}"
PY="${PY:-$HOME/miniforge3/envs/DNNs/bin/python}"
MATLAB_BIN="${MATLAB_BIN:-matlab}"

CORE_SUFFIX="${CORE_SUFFIX:-high_run01}"
PA1_SUFFIX="${PA1_SUFFIX:-pa1_run01}"

CORE_BANK="${CORE_BANK:-ota_core_${CORE_SUFFIX}}"
CORE_NOISE="${CORE_NOISE:-${CORE_SUFFIX}}"

PA1_BANK="${PA1_BANK:-ota_pa1_run01}"

CACHE_LEN="${CACHE_LEN:-16384}"
CACHE_JOBS="${CACHE_JOBS:-16}"
CACHE_ROOT="${CACHE_ROOT:-$REPO/_feature_cache_nvme/len${CACHE_LEN}/norm/ota__${CORE_BANK}__${CORE_NOISE}}"
# ----------------------------------------

cd "$REPO"
mkdir -p results/buh_logs results/cache_workers

TS="$(date +%Y%m%d_%H%M%S)"
LOG="results/buh_logs/merge_relabel_cache_${TS}.log"
IMPORTANT="results/buh_logs/merge_relabel_cache_${TS}_important.log"

exec > >(tee -a "$LOG") 2>&1

echo "=== MERGE+RELABEL+CACHE RUN $TS ==="
echo "REPO=$REPO"
echo "CORE_BANK=$CORE_BANK"
echo "CORE_NOISE=$CORE_NOISE"
echo "PA1_BANK=$PA1_BANK"
echo "CACHE_ROOT=$CACHE_ROOT"
echo "CACHE_LEN=$CACHE_LEN"
echo "CACHE_JOBS=$CACHE_JOBS"
echo ""

echo "=== PRECHECK: active bank workers ==="
if pgrep -af 'MATLAB.*bank_worker' >/tmp/active_bank_workers_${TS}.txt; then
  echo "ERROR: bank_worker processes are still running. Do NOT merge/cache yet."
  cat /tmp/active_bank_workers_${TS}.txt
  exit 2
else
  echo "OK: no active bank_worker processes."
fi

echo ""
echo "=== PRECHECK: required bank dirs ==="
for p in wifi bluetooth zigbee; do
  pa1_dir="$REPO/data/$p/ota/$PA1_BANK"
  core_dir="$REPO/data/$p/ota/$CORE_BANK"

  if [[ ! -d "$pa1_dir" ]]; then
    echo "ERROR: missing PA1 bank dir: $pa1_dir"
    exit 3
  fi

  if [[ ! -d "$core_dir" ]]; then
    echo "ERROR: missing core bank dir: $core_dir"
    exit 3
  fi

  echo "OK: $p PA1 bank  -> $pa1_dir"
  echo "OK: $p core bank -> $core_dir"
done

echo ""
echo "=== PRECHECK: current pipeline status summary ==="
if [[ -x "$REPO/pipeline_status.sh" ]]; then
  "$REPO/pipeline_status.sh" | sed -n '/=== QUEUES/,/BLOCKED/p' || true
else
  echo "WARN: pipeline_status.sh not executable/found; skipping status check."
fi

echo ""
echo "=== MERGE+RELABEL ==="
"$MATLAB_BIN" -batch "cd('$REPO'); \
  pa_link_pa1_into_core_v01({'wifi','bluetooth','zigbee'}, '$PA1_BANK', '$CORE_BANK'); \
  pa_relabel_bank_labels_v01({'wifi','bluetooth','zigbee'}, '$CORE_BANK', {'PA1','PA2','PA3','PA4','PA8'});" \
  2>&1 | tee "results/buh_logs/relabel_${TS}.log"

echo ""
echo "=== CACHE ALL CORE SHARDS IN ONE PARALLEL BATCH ==="
echo "This caches wifi/bluetooth/zigbee shards 1-20 from $CORE_BANK."
echo ""

CACHE_TASKS="results/cache_workers/cache_tasks_${TS}.txt"
: > "$CACHE_TASKS"

for proto in wifi bluetooth zigbee; do
  for sh in $(seq 1 20); do
    printf "%s %03d\n" "$proto" "$sh" >> "$CACHE_TASKS"
  done
done

parallel --line-buffer --colsep ' ' --halt now,fail=1 -j "$CACHE_JOBS" \
  --joblog "results/cache_workers/joblog_cache_all_${TS}.txt" '
    proto={1}
    sh={2}

    echo "CACHE START | ${proto} | shard=${sh}"

    '"$PY"' '"$REPO"'/cacheBuild.py \
      --data-root '"$REPO"'/data \
      --cache-root '"$CACHE_ROOT"' \
      --cache-len '"$CACHE_LEN"' \
      --normalize \
      --source-type ota \
      --source-name '"$CORE_BANK"' \
      --dataset-tag '"$CORE_BANK"' \
      --noise-tag '"$CORE_NOISE"' \
      --source-glob "${proto}/ota/'"$CORE_BANK"'/*__shard_${sh}__*.mat" \
      2>&1 | tee "results/cache_workers/cache_${proto}_shard_${sh}_${TS}.log"

    echo "CACHE DONE | ${proto} | shard=${sh}"
  ' :::: "$CACHE_TASKS" \
  2>&1 | tee "results/cache_workers/cache_all_${TS}.log"

echo ""
echo "=== POSTCHECK: cache outputs ==="
find "$CACHE_ROOT" -maxdepth 3 -type f | wc -l | awk '{print "Cache file count:", $1}'
du -sh "$CACHE_ROOT" 2>/dev/null || true

echo ""
echo "=== POSTCHECK: pipeline status ==="
if [[ -x "$REPO/pipeline_status.sh" ]]; then
  "$REPO/pipeline_status.sh" | tee "results/buh_logs/status_after_cache_${TS}.txt"
else
  echo "WARN: pipeline_status.sh not executable/found; skipping status check."
fi

grep -E '^(===|OK:|ERROR|WARN|CACHE START|CACHE DONE|Cache build complete|Cache files present|Full log|Important log)' \
  "$LOG" > "$IMPORTANT" || true

echo ""
echo "=== DONE ==="
echo "Full log     : $LOG"
echo "Important log: $IMPORTANT"
echo "Cache all log: results/cache_workers/cache_all_${TS}.log"
echo "Joblog       : results/cache_workers/joblog_cache_all_${TS}.txt"
