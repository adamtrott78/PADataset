#!/usr/bin/env bash
set -euo pipefail

REPO="${REPO:-$HOME/adamArchives/Adam/varMax/PADataset}"
MATLAB_BIN="${MATLAB_BIN:-matlab}"

# User knobs
PROTO="${PROTO:-zigbee}"
DATASET_SUFFIX="${DATASET_SUFFIX:-pa1_run01}"
SHARDS="${SHARDS:-3}"
NPARTS="${NPARTS:-4}"
JOBS="${JOBS:-$NPARTS}"
CHUNK_N="${CHUNK_N:-8}"

# Use a test bank by default so we do not collide with active old bankers.
OUT_BANK="${OUT_BANK:-ota_pa1_split_test}"

cd "$REPO"
mkdir -p results/bank_pa1_split_workers

TS="$(date +%Y%m%d_%H%M%S)"
TASKS="results/bank_pa1_split_workers/tasks_${PROTO}_${DATASET_SUFFIX}_${TS}.txt"

: > "$TASKS"
for sh in $SHARDS; do
  for part in $(seq 1 "$NPARTS"); do
    printf "%s %s\n" "$sh" "$part" >> "$TASKS"
  done
done

echo "=== PA1 SPLIT BANK RUN $TS ==="
echo "PROTO=$PROTO"
echo "DATASET_SUFFIX=$DATASET_SUFFIX"
echo "SHARDS=$SHARDS"
echo "NPARTS=$NPARTS"
echo "JOBS=$JOBS"
echo "OUT_BANK=$OUT_BANK"
echo "CHUNK_N=$CHUNK_N"
echo ""

# Do not block if old bank_worker is running, because OUT_BANK defaults to a test bank.
# But warn if writing to the real final PA1 bank.
if [[ "$OUT_BANK" == "ota_pa1_run01" ]]; then
  ACTIVE="$(pgrep -af "MATLAB.*(bank_worker|build_ota_bank|pa1_split).*${PROTO}.*pa1_run01" || true)"
  if [[ -n "$ACTIVE" ]]; then
    echo "ERROR: active PA1 banking process detected for $PROTO while OUT_BANK=ota_pa1_run01."
    echo "$ACTIVE"
    exit 2
  fi
fi

echo "=== PART WORKERS ==="
parallel --line-buffer --colsep ' ' --tag --tagstring "${PROTO}|shard={1}|part={2}" --halt now,fail=1 -j "$JOBS" '
  sh={1}
  part={2}
  sh3=$(printf "%03d" "$sh")

  '"$MATLAB_BIN"' -batch "cd('\'''"$REPO"''\''); pa1_split_part_bank_v01('\'''"$PROTO"''\'','\'''"$DATASET_SUFFIX"''\'',$sh,$part,'"$NPARTS"', '\'''"$OUT_BANK"''\'','"$CHUNK_N"')" \
    2>&1 | tee "results/bank_pa1_split_workers/${PROTO}_${DATASET_SUFFIX}_shard_${sh3}_part_${part}_of_'"$NPARTS"'_'"$TS"'.log"
' :::: "$TASKS" \
  2>&1 | tee "results/bank_pa1_split_workers/${PROTO}_${DATASET_SUFFIX}_split_parts_${TS}_all.log"

echo ""
echo "=== MERGE PARTS ==="
for sh in $SHARDS; do
  sh3=$(printf "%03d" "$sh")
  "$MATLAB_BIN" -batch "cd('$REPO'); pa1_split_merge_v01('$PROTO','$DATASET_SUFFIX',$sh,$NPARTS,'$OUT_BANK',$CHUNK_N,true)" \
    2>&1 | tee "results/bank_pa1_split_workers/${PROTO}_${DATASET_SUFFIX}_shard_${sh3}_merge_${TS}.log"
done

echo ""
echo "=== VERIFY ==="
for sh in $SHARDS; do
  sh3=$(printf "%03d" "$sh")
  f="data/${PROTO}/ota/${OUT_BANK}/${OUT_BANK}__shard_${sh3}__PA1.mat"
  "$MATLAB_BIN" -batch "cd('$REPO'); f='$f'; M=matfile(f); fprintf('VERIFY | %s | N=%d | W=%d\n', f, size(M.X,1), size(M.X,3));"
done

echo ""
echo "=== DONE ==="
echo "Logs: results/bank_pa1_split_workers/"
