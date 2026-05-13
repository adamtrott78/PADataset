#!/usr/bin/env bash
set -euo pipefail

# ---------------- user config ----------------
REPO="${REPO:-$HOME/adamArchives/Adam/varMax/PADataset}"
PY="${PY:-$HOME/miniforge3/envs/DNNs/bin/python}"
MATLAB_BIN="${MATLAB_BIN:-matlab}"

RESP_JOBS="${RESP_JOBS:-10}"
BANK_JOBS="${BANK_JOBS:-10}"
CACHE_JOBS="${CACHE_JOBS:-10}"

CAPTURE_ATTEMPTS="${CAPTURE_ATTEMPTS:-20}"
CAPTURE_MAX_EVENTS="${CAPTURE_MAX_EVENTS:-100}"
CAPTURE_MIN_FILL="${CAPTURE_MIN_FILL:-0.95}"
CAPTURE_PAUSE_S="${CAPTURE_PAUSE_S:-5.0}"

CORE_SUFFIX="${CORE_SUFFIX:-high_run01}"
PA1_SUFFIX="${PA1_SUFFIX:-pa1_run01}"

CORE_BANK="${CORE_BANK:-ota_core_${CORE_SUFFIX}}"
CORE_NOISE="${CORE_NOISE:-${CORE_SUFFIX}}"

PA1_BANK="${PA1_BANK:-ota_pa1_run01}"
PA1_NOISE="${PA1_NOISE:-${PA1_SUFFIX}}"

CACHE_LEN="${CACHE_LEN:-16384}"
CACHE_ROOT="${CACHE_ROOT:-$REPO/_feature_cache_nvme/len${CACHE_LEN}/norm/ota__${CORE_BANK}__${CORE_NOISE}}"
# --------------------------------------------

cd "$REPO"
mkdir -p results/buh_logs results/resplice_workers results/bank_workers results/cache_workers

TS="$(date +%Y%m%d_%H%M%S)"
ORCH_LOG="results/buh_logs/orch_${TS}.log"
IMPORTANT_LOG="results/buh_logs/orch_${TS}_important.log"

exec > >(tee -a "$ORCH_LOG") 2>&1

echo "=== ORCH RUN $TS ==="
echo "REPO=$REPO"
echo "RESP_JOBS=$RESP_JOBS BANK_JOBS=$BANK_JOBS CACHE_JOBS=$CACHE_JOBS"
echo "CAPTURE gate: attempts=$CAPTURE_ATTEMPTS max_events=$CAPTURE_MAX_EVENTS min_fill=$CAPTURE_MIN_FILL pause_s=$CAPTURE_PAUSE_S"
echo "CORE: suffix=$CORE_SUFFIX bank=$CORE_BANK noise=$CORE_NOISE"
echo "PA1 : suffix=$PA1_SUFFIX bank=$PA1_BANK noise=$PA1_NOISE"
echo "CACHE_ROOT=$CACHE_ROOT"
echo ""

run_status() {
  local tag="$1"
  local out="$REPO/results/buh_logs/status_${TS}_${tag}.txt"
  mkdir -p "$(dirname "$out")"
  bash "$REPO/pipeline_status.sh" >"$out"
  echo "STATUS saved: $out" >&2
  printf '%s\n' "$out"
}

extract_queue() {
  local q="$1" f="$2"
  awk -v q="$q" '
    $1==q && $2==":" {inside=1; next}
    inside && $1 ~ /^[A-Z_]+$/ && $2==":" {exit}
    inside && NF>=1 {print}
  ' "$f"
}

group_queue_map() {
  # stdin: "proto suffix shard"
  awk '
    NF==3 {
      key=$1"|" $2
      shards[key]=shards[key]" "$3
      proto[key]=$1
      suf[key]=$2
    }
    END {
      for (k in shards) {
        gsub(/^ /,"",shards[k])
        print k "\t" proto[k] "\t" suf[k] "\t" shards[k]
      }
    }
  '
}

matlab_capture_list() {
  local proto="$1" dataset="$2" shards="$3"
  local shvec
  shvec="$(echo "$shards" | xargs)"
  [[ -z "$shvec" ]] && return 0

  echo ""
  echo "=== CAPTURE | $proto | $dataset | shards=[$shvec] ==="
  "$MATLAB_BIN" -batch "cd('$REPO'); \
    jobs=struct('protocol','$proto','dataset_id','$dataset','shards',[$shvec]); \
    capture_batch(jobs, \
      'max_capture_attempts',$CAPTURE_ATTEMPTS, \
      'max_capture_events',$CAPTURE_MAX_EVENTS, \
      'min_fill_frac',$CAPTURE_MIN_FILL, \
      'pause_between_attempts_s',$CAPTURE_PAUSE_S, \
      'skip_if_bank_ok',true, \
      'skip_if_spliced_ok',true, \
      'skip_if_ota_ok',true, \
      'overwrite',false);"
}

parallel_resplice_list() {
  local proto="$1" dataset="$2" shards="$3"
  local shvec
  shvec="$(echo "$shards" | xargs)"
  [[ -z "$shvec" ]] && return 0

  echo ""
  echo "=== RESPLICE | $proto | $dataset | shards=[$shvec] | j=$RESP_JOBS ==="
  parallel --halt now,fail=1 -j "$RESP_JOBS" \
    --joblog "results/resplice_workers/joblog_${dataset}_${TS}.txt" '
      sh=$(printf "%03d" {});
      '"$MATLAB_BIN"' -batch "cd('\'''"$REPO"''\''); resplice_worker('\'''"$proto"''\'','\'''"$dataset"''\'',{})" \
        2>&1 | tee "results/resplice_workers/'"$dataset"'_shard_${sh}.log"
    ' ::: $shvec
}

parallel_bank_list_batched10() {
  local proto="$1" dataset="$2" shards="$3"
  local -a arr
  read -r -a arr <<<"$(echo "$shards" | xargs)"
  [[ ${#arr[@]} -eq 0 ]] && return 0

  local i=0 batch=0
  while [[ $i -lt ${#arr[@]} ]]; do
    batch=$((batch+1))
    local -a chunk=( "${arr[@]:i:10}" )
    i=$((i+10))

    echo ""
    echo "=== BANK | $proto | $dataset | batch=$batch | shards=[${chunk[*]}] | j=$BANK_JOBS ==="
    parallel --halt now,fail=1 -j "$BANK_JOBS" \
      --joblog "results/bank_workers/joblog_${dataset}_${TS}_b${batch}.txt" '
        sh=$(printf "%03d" {});
        '"$MATLAB_BIN"' -batch "cd('\'''"$REPO"''\''); bank_worker('\'''"$proto"''\'','\'''"$dataset"''\'',{})" \
          2>&1 | tee "results/bank_workers/'"$dataset"'_shard_${sh}.log"
      ' ::: "${chunk[@]}"
  done
}

cache_shard() {
  local proto="$1" shard="$2"
  local sh
  sh=$(printf "%03d" "$shard")

  "$PY" "$REPO/cacheBuild.py" \
    --data-root "$REPO/data" \
    --cache-root "$CACHE_ROOT" \
    --cache-len "$CACHE_LEN" \
    --normalize \
    --source-type ota \
    --source-name "$CORE_BANK" \
    --dataset-tag "$CORE_BANK" \
    --noise-tag "$CORE_NOISE" \
    --source-glob "${proto}/ota/${CORE_BANK}/*__shard_${sh}__*.mat"
}
export -f cache_shard

parallel_cache_range() {
  local proto="$1" lo="$2" hi="$3"
  echo ""
  echo "=== CACHE | ${proto} | shards ${lo}-${hi} | j=${CACHE_JOBS} ==="
  parallel --halt now,fail=1 -j "$CACHE_JOBS" \
    --joblog "results/cache_workers/joblog_cache_${proto}_${lo}_${hi}_${TS}.txt" \
    'cache_shard '"$proto"' {} 2>&1 | tee "results/cache_workers/cache_'"\$0"'_'"$TS"'.log" >/dev/null' \
    ::: $(seq "$lo" "$hi")
}

# ---------- 0) STATUS (pre) + clean stranded ota tmp ----------
STATUS0="$(run_status pre)"

TMP_LIST="$(extract_queue CLEAN_OTA_TMP "$STATUS0" | sed '/^$/d' || true)"
if [[ -n "${TMP_LIST:-}" ]]; then
  echo ""
  echo "=== CLEAN_OTA_TMP (deleting stranded tmp files) ==="
  echo "$TMP_LIST"
  while IFS= read -r f; do
    [[ -n "$f" ]] && rm -f "$f" || true
  done <<< "$TMP_LIST"
fi

BLOCKED="$(extract_queue BLOCKED "$STATUS0" | sed '/^$/d' || true)"
if [[ -n "${BLOCKED:-}" ]]; then
  echo ""
  echo "!!! BLOCKED shards (no tx_tape+spec AND no ota) — fix these first:"
  echo "$BLOCKED"
  exit 2
fi

# ---------- 1) CAPTURE missing ----------
CAPTURE_LIST="$(extract_queue CAPTURE "$STATUS0" | awk 'NF==3' || true)"
if [[ -n "${CAPTURE_LIST:-}" ]]; then
  MAP_CAPTURE="$(echo "$CAPTURE_LIST" | group_queue_map || true)"
  for ds in \
    "wifi|$CORE_SUFFIX" "bluetooth|$CORE_SUFFIX" "zigbee|$CORE_SUFFIX" \
    "wifi|$PA1_SUFFIX"  "bluetooth|$PA1_SUFFIX"  "zigbee|$PA1_SUFFIX"
  do
    row="$(echo "$MAP_CAPTURE" | awk -v k="$ds" -F'\t' '$1==k {print $0}' || true)"
    [[ -z "$row" ]] && continue
    proto="$(echo "$row" | cut -f2)"
    suf="$(echo "$row"   | cut -f3)"
    shards="$(echo "$row"| cut -f4)"
    dataset="${proto}_${suf}"
    matlab_capture_list "$proto" "$dataset" "$shards"
  done
else
  echo "=== CAPTURE QUEUE empty ==="
fi

# ---------- 2) RESPLICE missing ----------
STATUS1="$(run_status post_capture)"
RESPLICE_LIST="$(extract_queue RESPLICE "$STATUS1" | awk 'NF==3' || true)"
if [[ -n "${RESPLICE_LIST:-}" ]]; then
  MAP_RESPLICE="$(echo "$RESPLICE_LIST" | group_queue_map || true)"
  for ds in \
    "wifi|$CORE_SUFFIX" "bluetooth|$CORE_SUFFIX" "zigbee|$CORE_SUFFIX" \
    "wifi|$PA1_SUFFIX"  "bluetooth|$PA1_SUFFIX"  "zigbee|$PA1_SUFFIX"
  do
    row="$(echo "$MAP_RESPLICE" | awk -v k="$ds" -F'\t' '$1==k {print $0}' || true)"
    [[ -z "$row" ]] && continue
    proto="$(echo "$row" | cut -f2)"
    suf="$(echo "$row"   | cut -f3)"
    shards="$(echo "$row"| cut -f4)"
    dataset="${proto}_${suf}"
    parallel_resplice_list "$proto" "$dataset" "$shards"
  done
else
  echo "=== RESPLICE QUEUE empty ==="
fi

# ---------- 3) BANK missing (batched by 10) ----------
STATUS2="$(run_status post_resplice)"
BANK_LIST="$(extract_queue BANK "$STATUS2" | awk 'NF==3' || true)"
if [[ -n "${BANK_LIST:-}" ]]; then
  MAP_BANK="$(echo "$BANK_LIST" | group_queue_map || true)"
  for ds in \
    "wifi|$CORE_SUFFIX" "bluetooth|$CORE_SUFFIX" "zigbee|$CORE_SUFFIX" \
    "wifi|$PA1_SUFFIX"  "bluetooth|$PA1_SUFFIX"  "zigbee|$PA1_SUFFIX"
  do
    row="$(echo "$MAP_BANK" | awk -v k="$ds" -F'\t' '$1==k {print $0}' || true)"
    [[ -z "$row" ]] && continue
    proto="$(echo "$row" | cut -f2)"
    suf="$(echo "$row"   | cut -f3)"
    shards="$(echo "$row"| cut -f4)"
    dataset="${proto}_${suf}"
    parallel_bank_list_batched10 "$proto" "$dataset" "$shards"
  done
else
  echo "=== BANK QUEUE empty ==="
fi

# ---------- 4) MERGE+RELABEL (requires PA1 banks exist) ----------

echo ""
echo "=== MERGE+RELABEL ==="
for p in wifi bluetooth zigbee; do
  if [[ ! -d "$REPO/data/$p/ota/$PA1_BANK" ]]; then
    echo "ERROR: Source PA1 bank missing for $p: $REPO/data/$p/ota/$PA1_BANK" >&2
    exit 3
  fi
  if [[ ! -d "$REPO/data/$p/ota/$CORE_BANK" ]]; then
    echo "ERROR: Core bank missing for $p: $REPO/data/$p/ota/$CORE_BANK" >&2
    exit 3
  fi
done

"$MATLAB_BIN" -batch "cd('$REPO'); \
  pa_link_pa1_into_core_v01({'wifi','bluetooth','zigbee'}, '$PA1_BANK', '$CORE_BANK'); \
  pa_relabel_bank_labels_v01({'wifi','bluetooth','zigbee'}, '$CORE_BANK', {'PA1','PA2','PA3','PA4','PA8'});" \
  2>&1 | tee "results/buh_logs/relabel_${TS}.log"

# ---------- 5) CACHE (two batches of 10 per protocol; 10 parallel jobs) ----------
echo ""
echo "=== CACHE (core bank; includes PA1 after merge+relabel) ==="
parallel_cache_range "wifi"      1 10
parallel_cache_range "wifi"     11 20
parallel_cache_range "bluetooth" 1 10
parallel_cache_range "bluetooth"11 20
parallel_cache_range "zigbee"    1 10
parallel_cache_range "zigbee"   11 20

# ---------- important summary ----------
grep -E '^(===|CAPTURE PASS|CAPTURE FAIL|TXRX GATE|TXRX DONE|TXRX SAVE|RESP SIMPLE DONE|HDR DONE|BANK DONE|BANK WRITE|BANK FAIL|Cache build complete|Cache files present|ERROR|!!!)' \
  "$ORCH_LOG" > "$IMPORTANT_LOG" || true

echo ""
echo "=== ORCH DONE ==="
echo "Full log     : $ORCH_LOG"
echo "Important log: $IMPORTANT_LOG"