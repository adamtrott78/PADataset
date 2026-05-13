#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Unified core-bank relabel + PA1 split-part banking + cache
#
# Final cache source uses ONE bank root only:
#   data/<proto>/ota/ota_core_high_run01/
#
# Core bank contains:
#   PA2/PA3/PA4/PA8 normal one-file banks
#   PA1 split-part banks named as core shards
#
# No giant PA1 merge.
# ============================================================

REPO="${REPO:-$HOME/adamArchives/Adam/varMax/PADataset}"
MATLAB_BIN="${MATLAB_BIN:-matlab}"
PY="${PY:-$(command -v python)}"

PROTOCOLS="${PROTOCOLS:-wifi bluetooth zigbee}"
CORE_SHARDS="${CORE_SHARDS:-1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20}"

DATASET_SUFFIX="${DATASET_SUFFIX:-pa1_run01}"
CORE_BANK="${CORE_BANK:-ota_core_high_run01}"
CORE_NOISE="${CORE_NOISE:-high_run01}"

# 2 means PA1 is 2 files per core shard.
# This is equivalent to 8 files per original PA1 shard, because each PA1 shard maps to 4 core shards.
PARTS_PER_CORE="${PARTS_PER_CORE:-2}"

SPLIT_JOBS="${SPLIT_JOBS:-16}"
CACHE_JOBS="${CACHE_JOBS:-16}"
CHUNK_N="${CHUNK_N:-8}"

CACHE_LEN="${CACHE_LEN:-16384}"
CACHE_ROOT="${CACHE_ROOT:-$REPO/_feature_cache_nvme/len${CACHE_LEN}/norm/ota__${CORE_BANK}__${CORE_NOISE}}"

FORCE_CACHE="${FORCE_CACHE:-0}"
CLEAR_PA1_PART_CACHE="${CLEAR_PA1_PART_CACHE:-1}"

cd "$REPO"

mkdir -p results/buh_logs results/bank_pa1_split_workers results/cache_workers

TS="$(date +%Y%m%d_%H%M%S)"
LOG="results/buh_logs/unified_core_splitpa1_cache_${TS}.log"
IMPORTANT="results/buh_logs/unified_core_splitpa1_cache_${TS}_important.log"

exec > >(tee -a "$LOG") 2>&1

echo "=== UNIFIED CORE SPLIT-PA1 CACHE $TS ==="
echo "REPO=$REPO"
echo "PY=$PY"
echo "MATLAB_BIN=$MATLAB_BIN"
echo "PROTOCOLS=$PROTOCOLS"
echo "CORE_SHARDS=$CORE_SHARDS"
echo "DATASET_SUFFIX=$DATASET_SUFFIX"
echo "CORE_BANK=$CORE_BANK"
echo "CORE_NOISE=$CORE_NOISE"
echo "PARTS_PER_CORE=$PARTS_PER_CORE"
echo "SPLIT_JOBS=$SPLIT_JOBS"
echo "CACHE_JOBS=$CACHE_JOBS"
echo "CHUNK_N=$CHUNK_N"
echo "CACHE_ROOT=$CACHE_ROOT"
echo "FORCE_CACHE=$FORCE_CACHE"
echo "CLEAR_PA1_PART_CACHE=$CLEAR_PA1_PART_CACHE"
echo ""

if [[ ! -f "$REPO/pa1_core_split_part_bank_v01.m" ]]; then
  echo "ERROR: missing pa1_core_split_part_bank_v01.m"
  exit 2
fi

FORCE_ARG=()
if [[ "$FORCE_CACHE" == "1" ]]; then
  FORCE_ARG=(--force-rebuild)
fi

echo "=== PRECHECK: no active core-bank writers ==="
ACTIVE_CORE="$(pgrep -af "MATLAB.*(bank_worker|build_ota_bank|pa1_core_split).*${CORE_BANK}" || true)"
if [[ -n "$ACTIVE_CORE" ]]; then
  echo "ERROR: active writer appears to target CORE_BANK=$CORE_BANK"
  echo "$ACTIVE_CORE"
  echo "Stop those before running unified cache."
  exit 3
fi
echo "OK: no active core-bank writers detected."
echo ""

echo "=== PRECHECK: spliced PA1 sources ==="
for proto in $PROTOCOLS; do
  for pa1_sh in 1 2 3 4 5; do
    sh3="$(printf "%03d" "$pa1_sh")"
    src="data/${proto}/ota/spliced/simple/${proto}_${DATASET_SUFFIX}/shard_${sh3}/ota_rx_PA1.mat"
    if [[ ! -f "$src" ]]; then
      echo "ERROR: missing PA1 spliced source: $src"
      exit 4
    fi
    echo "OK: $src"
  done
done
echo ""

echo "=== CLEAN STALE CORE PA1 PART FILES FOR SELECTED CORE SHARDS ==="
for proto in $PROTOCOLS; do
  core_dir="data/${proto}/ota/${CORE_BANK}"
  mkdir -p "$core_dir"

  for core_sh in $CORE_SHARDS; do
    sh3="$(printf "%03d" "$core_sh")"
    find "$core_dir" -maxdepth 1 -type f -name "${CORE_BANK}__shard_${sh3}__PA1__part_*_of_*.mat" -delete
    find "$core_dir" -maxdepth 1 -type l -name "${CORE_BANK}__shard_${sh3}__PA1__part_*_of_*.mat" -delete
  done
done
echo "OK: removed stale core PA1 part files for selected shards."
echo ""

echo "=== RELABEL REGULAR CORE BANK FILES ==="
echo "This should set PA1=0, PA2=1, PA3=2, PA4=3, PA8=4 for files present in $CORE_BANK."
"$MATLAB_BIN" -batch "cd('$REPO'); pa_relabel_bank_labels_v01({'wifi','bluetooth','zigbee'}, '$CORE_BANK', {'PA1','PA2','PA3','PA4','PA8'});" \
  2>&1 | tee "results/buh_logs/relabel_core_${TS}.log"
echo ""

echo "=== BUILD PA1 CORE SPLIT PARTS ==="
PART_TASKS="results/bank_pa1_split_workers/core_pa1_part_tasks_${TS}.txt"
: > "$PART_TASKS"

for proto in $PROTOCOLS; do
  for core_sh in $CORE_SHARDS; do
    pa1_sh=$(( (core_sh - 1) / 4 + 1 ))
    for part in $(seq 1 "$PARTS_PER_CORE"); do
      printf "%s %s %s\n" "$proto" "$pa1_sh" "$core_sh" "$part" >> "$PART_TASKS"
    done
  done
done

parallel --line-buffer --colsep ' ' --tag --tagstring '{1}|core_shard={3}|part={4}/'"$PARTS_PER_CORE"'"' --halt now,fail=1 -j "$SPLIT_JOBS" '
  proto={1}
  pa1_sh={2}
  core_sh={3}
  part={4}
  core3=$(printf "%03d" "$core_sh")
  pp=$(printf "%02d" "$part")
  np=$(printf "%02d" '"$PARTS_PER_CORE"')

  echo "PA1 CORE PART TASK START | proto=${proto} | pa1_shard=${pa1_sh} | core_shard=${core3} | part=${pp}/${np}"

  '"$MATLAB_BIN"' -batch "cd('\'''"$REPO"''\''); pa1_core_split_part_bank_v01('\''${proto}'\'','\'''"$DATASET_SUFFIX"''\'',$pa1_sh,$core_sh,$part,'"$PARTS_PER_CORE"', '\'''"$CORE_BANK"''\'','"$CHUNK_N"')" \
    2>&1 | tee "results/bank_pa1_split_workers/core_pa1_${proto}_shard_${core3}_part_${pp}_of_${np}_${TS}.log"

  echo "PA1 CORE PART TASK DONE | proto=${proto} | core_shard=${core3} | part=${pp}/${np}"
' :::: "$PART_TASKS" \
  2>&1 | tee "results/bank_pa1_split_workers/core_pa1_parts_${TS}_all.log"

echo ""
echo "=== VERIFY CORE PA1 PART FILES ==="
for proto in $PROTOCOLS; do
  for core_sh in $CORE_SHARDS; do
    sh3="$(printf "%03d" "$core_sh")"
    np="$(printf "%02d" "$PARTS_PER_CORE")"
    cnt="$(find "data/${proto}/ota/${CORE_BANK}" \
      -maxdepth 1 \
      -name "${CORE_BANK}__shard_${sh3}__PA1__part_*_of_${np}.mat" \
      2>/dev/null | wc -l)"
    echo "CORE PA1 PART COUNT | proto=$proto | core_shard=$sh3 | count=$cnt/$PARTS_PER_CORE"
    if [[ "$cnt" != "$PARTS_PER_CORE" ]]; then
      echo "ERROR: expected $PARTS_PER_CORE PA1 core part files for $proto shard $sh3 but found $cnt"
      exit 5
    fi
  done
done

if [[ "$CLEAR_PA1_PART_CACHE" == "1" ]]; then
  echo ""
  echo "=== CLEAR OLD PA1 PART CACHE FILES FOR SELECTED CORE SHARDS ==="
  for proto in $PROTOCOLS; do
    for core_sh in $CORE_SHARDS; do
      sh3="$(printf "%03d" "$core_sh")"
      find "$CACHE_ROOT" -type f -name "*${proto}*${CORE_BANK}__shard_${sh3}__PA1__part_*_of_*.h5" -delete 2>/dev/null || true
    done
  done
  echo "OK: old PA1 part h5 files removed for selected shards."
fi

echo ""
echo "=== CACHE FROM SINGLE CORE BANK ROOT ==="
CACHE_TASKS="results/cache_workers/unified_core_cache_tasks_${TS}.txt"
: > "$CACHE_TASKS"

for proto in $PROTOCOLS; do
  for core_sh in $CORE_SHARDS; do
    sh3="$(printf "%03d" "$core_sh")"
    printf "%s %s\n" "$proto" "$sh3" >> "$CACHE_TASKS"
  done
done

parallel --line-buffer --colsep ' ' --tag --tagstring '{1}|cache|shard={2}' --halt now,fail=1 -j "$CACHE_JOBS" '
  proto={1}
  sh3={2}
  t0=$(date +%s)

  echo "CACHE CORE START | proto=${proto} | shard=${sh3}"

  '"$PY"' '"$REPO"'/cacheBuild.py \
    --data-root '"$REPO"'/data \
    --cache-root '"$CACHE_ROOT"' \
    --cache-len '"$CACHE_LEN"' \
    --normalize \
    --source-type ota \
    --source-name '"$CORE_BANK"' \
    --dataset-tag '"$CORE_BANK"' \
    --noise-tag '"$CORE_NOISE"' \
    --source-glob "${proto}/ota/'"$CORE_BANK"'/*__shard_${sh3}__*.mat" \
    '"${FORCE_ARG[*]}"' \
    2>&1 | tee "results/cache_workers/unified_core_cache_${proto}_shard_${sh3}_${TS}.log"

  t1=$(date +%s)
  dur=$((t1-t0))
  echo "CACHE CORE DONE | proto=${proto} | shard=${sh3} | duration=${dur}s"
' :::: "$CACHE_TASKS" \
  2>&1 | tee "results/cache_workers/unified_core_cache_${TS}_all.log"

echo ""
echo "=== VERIFY PA1 PART CACHE FILES ==="
for proto in $PROTOCOLS; do
  for core_sh in $CORE_SHARDS; do
    sh3="$(printf "%03d" "$core_sh")"
    np="$(printf "%02d" "$PARTS_PER_CORE")"
    cnt="$(find "$CACHE_ROOT" \
      -type f \
      -name "*${proto}*${CORE_BANK}__shard_${sh3}__PA1__part_*_of_${np}.h5" \
      2>/dev/null | wc -l)"
    echo "PA1 PART CACHE COUNT | proto=$proto | core_shard=$sh3 | count=$cnt/$PARTS_PER_CORE"
    if [[ "$cnt" != "$PARTS_PER_CORE" ]]; then
      echo "ERROR: expected $PARTS_PER_CORE PA1 part h5 files for $proto shard $sh3 but found $cnt"
      exit 6
    fi
  done
done

echo ""
echo "=== CACHE ROOT SIZE ==="
du -sh "$CACHE_ROOT" || true

echo ""
echo "=== DONE ==="
echo "Full log     : $LOG"
echo "Important log: $IMPORTANT"
echo "Relabel log  : results/buh_logs/relabel_core_${TS}.log"
echo "Split log    : results/bank_pa1_split_workers/core_pa1_parts_${TS}_all.log"
echo "Cache log    : results/cache_workers/unified_core_cache_${TS}_all.log"

grep -E '^(===|OK:|ERROR|PA1 CORE PART TASK START|PA1 CORE PART TASK DONE|CORE PA1 PART COUNT|CACHE CORE START|CACHE CORE DONE|PA1 PART CACHE COUNT|DONE)' \
  "$LOG" > "$IMPORTANT" || true
