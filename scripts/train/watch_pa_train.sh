#!/usr/bin/env bash
set -euo pipefail

REPO="${REPO:-$HOME/adamArchives/Adam/varMax/PADataset}"
MANIFEST="${1:-manifests/smoke_train_manifest.tsv}"
LOGROOT="${LOGROOT:-results/train_workers}"
REFRESH="${REFRESH:-2}"

cd "$REPO"

if [[ ! -f "$MANIFEST" ]]; then
  echo "ERROR: manifest not found: $MANIFEST"
  exit 2
fi

artifact_flags() {
  local run_dir="$1"
  local out=""
  [[ -f "$run_dir/config.json" ]] && out="${out}C" || out="${out}-"
  [[ -f "$run_dir/best_model.pt" ]] && out="${out}B" || out="${out}-"
  [[ -f "$run_dir/final_model.pt" ]] && out="${out}F" || out="${out}-"
  [[ -f "$run_dir/history.json" ]] && out="${out}H" || out="${out}-"
  [[ -f "$run_dir/summary.json" ]] && out="${out}S" || out="${out}-"
  [[ -f "$run_dir/train_complete.json" ]] && out="${out}T" || out="${out}-"
  printf '%s' "$out"
}

latest_log_for_run() {
  local run_name="$1"
  ls -t "$LOGROOT/${run_name}"_*.log 2>/dev/null | head -n 1 || true
}

latest_progress_line() {
  local log="$1"
  if [[ -z "$log" || ! -f "$log" ]]; then
    printf 'no per-run log yet'
    return 0
  fi

  # tqdm often uses carriage returns. Convert them to newlines and keep useful recent lines.
  tail -c 30000 "$log" 2>/dev/null \
    | tr '\r' '\n' \
    | sed 's/\x1b\[[0-9;]*[A-Za-z]//g' \
    | sed '/^[[:space:]]*$/d' \
    | grep -E 'TRAIN START|TRAIN DONE|TRAIN ERROR|RUN_STAGE|TRAIN_EPOCH_START|TRAIN_STEP|TRAIN_EPOCH_TRAIN_DONE|TRAIN_EPOCH_DONE|Epoch|epoch|loss|Loss|acc|Acc|val|Val|test|Test|%|it/s|s/it' \
    | tail -n 1 \
    | cut -c1-160
}

status_for_run() {
  local run_name="$1"
  local cfg_path="$2"
  local run_dir="$3"

  if grep -h "TRAIN ERROR | run_name=${run_name}" "$LOGROOT"/train_all_*.log >/dev/null 2>&1; then
    printf 'ERROR'
  elif [[ -f "$run_dir/train_complete.json" ]] || grep -h "TRAIN DONE | run_name=${run_name}" "$LOGROOT"/train_all_*.log >/dev/null 2>&1; then
    printf 'DONE'
  elif pgrep -af "pa_train_one.py.*${cfg_path}" >/dev/null 2>&1 || pgrep -af "pa_train_one.py" | grep -F "$cfg_path" >/dev/null 2>&1; then
    printf 'RUNNING'
  elif grep -h "TRAIN START | run_name=${run_name}" "$LOGROOT"/train_all_*.log >/dev/null 2>&1; then
    printf 'STARTED'
  else
    printf 'PENDING'
  fi
}

while true; do
  now="$(date '+%Y-%m-%d %H:%M:%S')"
  clear

  echo "PA training dashboard | $now"
  echo "REPO=$REPO"
  echo "MANIFEST=$MANIFEST"
  echo "LOGROOT=$LOGROOT"
  echo

  echo "=== GPU STATUS ==="
  if command -v nvidia-smi >/dev/null 2>&1; then
    nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu \
      --format=csv,noheader,nounits 2>/dev/null \
      | awk -F, '{printf "GPU %s | %s | mem %s/%s MiB | util %s%%\n", $1, $2, $3, $4, $5}'
  else
    echo "nvidia-smi not found"
  fi

  echo
  echo "=== ACTIVE TRAINING PROCESSES ==="
  pgrep -af "pa_train_one.py" || echo "none"

  echo
  echo "=== RUN STATUS ==="
  printf '%-9s %-5s %-7s %-6s %-42s %-6s %s\n' "STATUS" "GPU" "SEED" "ARTS" "RUN" "LOG" "LATEST"
  printf '%-9s %-5s %-7s %-6s %-42s %-6s %s\n' "--------" "---" "----" "------" "------------------------------------------" "------" "------"

  total=0
  done=0
  running=0
  errors=0

  tail -n +2 "$MANIFEST" | while IFS=$'\t' read -r run_name paper_set family_tag unknown_pa seed gpu cfg_path save_root; do
    [[ -z "${run_name:-}" ]] && continue

    total=$((total + 1))
    run_dir="$save_root/$run_name"
    st="$(status_for_run "$run_name" "$cfg_path" "$run_dir")"
    arts="$(artifact_flags "$run_dir")"
    log="$(latest_log_for_run "$run_name")"
    logflag="no"
    [[ -n "$log" ]] && logflag="yes"

    latest="$(latest_progress_line "$log")"

    case "$st" in
      DONE) done=$((done + 1));;
      RUNNING) running=$((running + 1));;
      ERROR) errors=$((errors + 1));;
    esac

    printf '%-9s %-5s %-7s %-6s %-42s %-6s %s\n' "$st" "$gpu" "$seed" "$arts" "$run_name" "$logflag" "$latest"
  done

  echo
  echo "Artifact flags: C=config, B=best_model, F=final_model, H=history, S=summary, T=train_complete"
  echo "Refresh: ${REFRESH}s | Ctrl+C to exit dashboard only"

  sleep "$REFRESH"
done
