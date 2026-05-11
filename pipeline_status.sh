#!/usr/bin/env bash
set -euo pipefail

REPO="${REPO:-$HOME/adamArchives/Adam/varMax/PADataset}"

# dataset naming (suffix = dataset_id suffix after "<proto>_")
CORE_SUFFIX="${CORE_SUFFIX:-high_run01}"
PA1_SUFFIX="${PA1_SUFFIX:-pa1_run01}"

# bank naming
CORE_BANK="${CORE_BANK:-ota_core_${CORE_SUFFIX}}"
CORE_NOISE="${CORE_NOISE:-${CORE_SUFFIX}}"
PA1_BANK="${PA1_BANK:-ota_pa1_run01}"
PA1_NOISE="${PA1_NOISE:-${PA1_SUFFIX}}"

# shard ranges
CORE_SHARDS="${CORE_SHARDS:-$(seq 1 20)}"
PA1_SHARDS="${PA1_SHARDS:-$(seq 1 5)}"

# which PAs must exist at each stage
CORE_PAS=( ${CORE_PAS:-PA2 PA3 PA4 PA8} )
PA1_PAS=( ${PA1_PAS:-PA1} )

CACHELEN="${CACHELEN:-16384}"
CACHE_DIR_CORE="$REPO/_feature_cache_nvme/len${CACHELEN}/norm/ota__${CORE_BANK}__${CORE_NOISE}"
CACHE_DIR_PA1="$REPO/_feature_cache_nvme/len${CACHELEN}/norm/ota__${PA1_BANK}__${PA1_NOISE}"

exists_glob() {
  shopt -s nullglob
  local arr=( $1 )
  shopt -u nullglob
  (( ${#arr[@]} > 0 ))
}
yn() { [[ "$1" == "1" ]] && echo "Y" || echo "N"; }

# queues
CLEAN_OTA_TMP_Q=()
CAPTURE_Q=()
RESPLICE_Q=()
BANK_Q=()
CACHE_Q=()
BLOCK_Q=()

printf "\n=== PIPELINE STATUS DASHBOARD (v3) ===\n"
printf "REPO=%s\n" "$REPO"
printf "CORE: suffix=%s bank=%s noise=%s shards=[%s] PAs=%s\n" "$CORE_SUFFIX" "$CORE_BANK" "$CORE_NOISE" "$(echo $CORE_SHARDS)" "$(printf "%s " "${CORE_PAS[@]}")"
printf "PA1 : suffix=%s bank=%s noise=%s shards=[%s] PAs=%s\n" "$PA1_SUFFIX" "$PA1_BANK" "$PA1_NOISE" "$(echo $PA1_SHARDS)" "$(printf "%s " "${PA1_PAS[@]}")"
printf "CACHELEN=%s\n" "$CACHELEN"
printf "CORE_CACHE_DIR=%s\n" "$CACHE_DIR_CORE"
printf "PA1_CACHE_DIR=%s\n\n" "$CACHE_DIR_PA1"

printf "%-10s %-22s %-5s | TX  OTA  TMP  SPL  BANK  CACH  SUM | NEXT\n" "proto" "dataset" "sh"
printf "%-10s %-22s %-5s | --- --- ---- --- ---- ---- ---- | ----\n" "-----" "------" "--"

check_one() {
  local proto="$1" suffix="$2" bank="$3" noise="$4"
  shift 4
  local shards="$1"; shift
  local pas=( "$@" )

  local dataset_full="${proto}_${suffix}"

  for sid in $shards; do
    local s; s=$(printf "%03d" "$sid")

    # TX inputs
    local tx_tape="$REPO/txrx/tapes/digital/$proto/$dataset_full/tx_tape_shard_${s}.mat"
    local tx_spec="$REPO/txrx/tapes/digital/$proto/$dataset_full/tx_spec_shard_${s}.mat"
    local has_tx=0
    [[ -f "$tx_tape" && -f "$tx_spec" ]] && has_tx=1

    # OTA + tmp
    local ota="$REPO/txrx/tapes/ota/$proto/$dataset_full/ota_tape_shard_${s}.mat"
    local ota_tmp="${ota}.tmp"
    local has_ota=0
    local has_tmp=0
    [[ -f "$ota" ]] && has_ota=1
    [[ -f "$ota_tmp" ]] && has_tmp=1

    # resplice summary (useful signal, not a stage requirement)
    local sum="$REPO/results/$proto/ota/rx_resplice_simple/$dataset_full/shard_${s}/resplice_summary_simple.mat"
    local has_sum=0
    [[ -f "$sum" ]] && has_sum=1

    # spliced
    local spl_dir="$REPO/data/$proto/ota/spliced/simple/$dataset_full/shard_${s}"
    local spl_ok=1
    if [[ -d "$spl_dir" ]]; then
      for pa in "${pas[@]}"; do
        [[ -f "$spl_dir/ota_rx_${pa}.mat" ]] || spl_ok=0
      done
    else
      spl_ok=0
    fi

    # bank
    local bank_dir="$REPO/data/$proto/ota/$bank"
    local bank_ok=1
    if [[ -d "$bank_dir" ]]; then
      for pa in "${pas[@]}"; do
        [[ -f "$bank_dir/${bank}__shard_${s}__${pa}.mat" ]] || bank_ok=0
      done
    else
      bank_ok=0
    fi

    # cache (per-PA h5 exists)
    local cache_dir="$REPO/_feature_cache_nvme/len${CACHELEN}/norm/ota__${bank}__${noise}"
    local cache_ok=1
    if [[ -d "$cache_dir" ]]; then
      for pa in "${pas[@]}"; do
        if ! exists_glob "$cache_dir/${proto}__ota__${bank}__*__shard_${s}__${pa}.h5"; then
          cache_ok=0
        fi
      done
    else
      cache_ok=0
    fi

    # queue: clean tmp
    if [[ $has_tmp -eq 1 && $has_ota -eq 0 ]]; then
      CLEAN_OTA_TMP_Q+=( "$proto $suffix $sid" )
    fi

    # decide NEXT
    local next="DONE"
    if [[ $cache_ok -eq 1 ]]; then
      next="DONE"
    elif [[ $bank_ok -eq 1 ]]; then
      next="CACHE"
      CACHE_Q+=( "$proto $suffix $sid" )
    elif [[ $spl_ok -eq 1 ]]; then
      next="BANK"
      BANK_Q+=( "$proto $suffix $sid" )
    elif [[ $has_ota -eq 1 ]]; then
      next="RESPLICE"
      RESPLICE_Q+=( "$proto $suffix $sid" )
    else
      if [[ $has_tx -eq 1 ]]; then
        next="CAPTURE"
        CAPTURE_Q+=( "$proto $suffix $sid" )
      else
        next="BLOCK_NO_TX"
        BLOCK_Q+=( "$proto $suffix $sid" )
      fi
    fi

    printf "%-10s %-22s %-5s |  %s   %s   %s    %s    %s    %s    %s  | %s\n" \
      "$proto" "$dataset_full" "$s" \
      "$(yn $has_tx)" "$(yn $has_ota)" "$(yn $has_tmp)" "$(yn $spl_ok)" "$(yn $bank_ok)" "$(yn $cache_ok)" "$(yn $has_sum)" \
      "$next"
  done
}

check_one "wifi"      "$CORE_SUFFIX" "$CORE_BANK" "$CORE_NOISE" "$CORE_SHARDS" "${CORE_PAS[@]}"
check_one "bluetooth" "$CORE_SUFFIX" "$CORE_BANK" "$CORE_NOISE" "$CORE_SHARDS" "${CORE_PAS[@]}"
check_one "zigbee"    "$CORE_SUFFIX" "$CORE_BANK" "$CORE_NOISE" "$CORE_SHARDS" "${CORE_PAS[@]}"

check_one "wifi"      "$PA1_SUFFIX" "$PA1_BANK" "$PA1_NOISE" "$PA1_SHARDS" "${PA1_PAS[@]}"
check_one "bluetooth" "$PA1_SUFFIX" "$PA1_BANK" "$PA1_NOISE" "$PA1_SHARDS" "${PA1_PAS[@]}"
check_one "zigbee"    "$PA1_SUFFIX" "$PA1_BANK" "$PA1_NOISE" "$PA1_SHARDS" "${PA1_PAS[@]}"

echo ""
echo "=== QUEUES (what’s missing) ==="
echo "CLEAN_OTA_TMP : ${#CLEAN_OTA_TMP_Q[@]}   (remove ota_tape_shard_###.mat.tmp if MATLAB died mid-save)"
printf '%s\n' "${CLEAN_OTA_TMP_Q[@]:-}" | sed '/^$/d' | head -n 500
echo ""
echo "CAPTURE       : ${#CAPTURE_Q[@]}"
printf '%s\n' "${CAPTURE_Q[@]:-}" | sed '/^$/d' | head -n 500
echo ""
echo "RESPLICE      : ${#RESPLICE_Q[@]}"
printf '%s\n' "${RESPLICE_Q[@]:-}" | sed '/^$/d' | head -n 500
echo ""
echo "BANK          : ${#BANK_Q[@]}"
printf '%s\n' "${BANK_Q[@]:-}" | sed '/^$/d' | head -n 500
echo ""
echo "CACHE         : ${#CACHE_Q[@]}"
printf '%s\n' "${CACHE_Q[@]:-}" | sed '/^$/d' | head -n 500
echo ""
echo "BLOCKED       : ${#BLOCK_Q[@]}  (no tx_tape+spec AND no ota)"
printf '%s\n' "${BLOCK_Q[@]:-}" | sed '/^$/d' | head -n 500