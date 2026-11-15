#!/usr/bin/env bash
set -Eeuo pipefail

# One-shot local launcher for the MTH602 STFT-track representation ablation.
# Intended to run from an exact detached worktree of PR #21.
#
# Phase 1 (CPU): build/resume the alternate STFT-track cache.
# Phase 2 (parallel): GPU1 backbone training + CPU PA1/PA4 diagnostic.

CANON_REPO="${CANON_REPO:-$HOME/adamArchives/Adam/varMax/PADataset}"
DATA_ROOT="${DATA_ROOT:-$CANON_REPO/data}"
CACHE_ROOT="${CACHE_ROOT:-$CANON_REPO/_feature_cache_nvme/len16384/norm_stfttracks64_v1/ota__ota_core_high_run01__high_run01}"
RESULT_ROOT="${RESULT_ROOT:-$CANON_REPO/results_pa_mth602_stft_ablation}"
DIAG_ROOT="${DIAG_ROOT:-$CANON_REPO/results/pa1_pa4_stft_diagnostic/stfttracks64_v1}"
VENV="${VENV:-$HOME/adamArchives/venvs/DNNs}"
GPU_INDEX="${GPU_INDEX:-1}"
CPU_THREADS="${CPU_THREADS:-16}"
FRAME_COUNT="${FRAME_COUNT:-64}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_ROOT="$CANON_REPO/local_artifacts/stft_ablation_v1"
mkdir -p "$LOG_ROOT" "$RESULT_ROOT" "$DIAG_ROOT"

[[ -x "$VENV/bin/python" ]] || { echo "Missing DNNs python: $VENV/bin/python" >&2; exit 20; }
PY="$VENV/bin/python"

echo "=== STFT TRACK ABLATION ==="
echo "candidate_sha=$(git -C "$ROOT" rev-parse HEAD)"
echo "worktree=$ROOT"
echo "cache_root=$CACHE_ROOT"
echo "gpu_index=$GPU_INDEX"

export OMP_NUM_THREADS="$CPU_THREADS"
export MKL_NUM_THREADS="$CPU_THREADS"
export OPENBLAS_NUM_THREADS="$CPU_THREADS"

echo
echo "=== PREFLIGHT: STFT TRAJECTORY UNIT TEST ==="
"$PY" -m pytest -q "$ROOT/tests/test_stft_track_features.py"

echo
echo "=== PHASE 1: BUILD/RESUME STFT TRACK CACHE ==="
"$PY" "$ROOT/experiments/pa_build_stft_track_cache.py" \
  --data-root "$DATA_ROOT" \
  --cache-root "$CACHE_ROOT" \
  --cache-len 16384 \
  --source-type ota \
  --source-name ota_core_high_run01 \
  --dataset-tag ota_core_high_run01 \
  --noise-tag high_run01 \
  --frame-count "$FRAME_COUNT" \
  2>&1 | tee "$LOG_ROOT/cache_build.log"

[[ -f "$CACHE_ROOT/stft_track_cache_manifest.json" ]] || {
  echo "Cache manifest missing after build" >&2
  exit 21
}

echo
echo "=== PHASE 2: START GPU TRAINING + CPU DIAGNOSTIC IN PARALLEL ==="

NORM_CFG="$LOG_ROOT/stft_seed0_normalized.json"
"$PY" - "$ROOT/manifests/configs/mth602_stage03/archC_backbone_knownonly_unkPA2_c16384_seed0_stfttracks64_v1.json" "$CACHE_ROOT" "$RESULT_ROOT" "$NORM_CFG" <<'PY'
import json, pathlib, sys
src, cache_root, result_root, out = sys.argv[1:]
cfg = json.loads(pathlib.Path(src).read_text())
cfg["cache_root"] = cache_root
cfg["save_root"] = result_root
cfg["skip_cache_build"] = True
cfg["force_rebuild_cache"] = False
pathlib.Path(out).write_text(json.dumps(cfg, indent=2, sort_keys=True) + "\n")
PY

(
  export CUDA_VISIBLE_DEVICES="$GPU_INDEX"
  "$PY" "$ROOT/experiments/pa_train_one.py" \
    --cfg "$NORM_CFG" \
    --data-root "$DATA_ROOT"
) >"$LOG_ROOT/train_gpu${GPU_INDEX}.log" 2>&1 &
TRAIN_PID=$!

(
  "$PY" "$ROOT/experiments/pa_stft_track_diagnostic.py" \
    --cache-root "$CACHE_ROOT" \
    --out-dir "$DIAG_ROOT" \
    --max-per-file 512 \
    --quant-step 0.02 \
    --folds 5
) >"$LOG_ROOT/diagnostic_cpu.log" 2>&1 &
DIAG_PID=$!

cat > "$LOG_ROOT/processes.json" <<EOF
{
  "candidate_sha": "$(git -C "$ROOT" rev-parse HEAD)",
  "training_pid": $TRAIN_PID,
  "diagnostic_pid": $DIAG_PID,
  "gpu_index": "$GPU_INDEX",
  "cache_root": "$CACHE_ROOT",
  "training_log": "$LOG_ROOT/train_gpu${GPU_INDEX}.log",
  "diagnostic_log": "$LOG_ROOT/diagnostic_cpu.log"
}
EOF

echo "training_pid=$TRAIN_PID"
echo "diagnostic_pid=$DIAG_PID"
echo "training_log=$LOG_ROOT/train_gpu${GPU_INDEX}.log"
echo "diagnostic_log=$LOG_ROOT/diagnostic_cpu.log"

set +e
wait "$DIAG_PID"
DIAG_RC=$?
wait "$TRAIN_PID"
TRAIN_RC=$?
set -e

"$PY" - "$LOG_ROOT" "$DIAG_RC" "$TRAIN_RC" <<'PY'
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
diag_rc, train_rc = map(int, sys.argv[2:4])
payload = {
    "diagnostic_exit_code": diag_rc,
    "training_exit_code": train_rc,
    "success": diag_rc == 0 and train_rc == 0,
}
(root / "completion.json").write_text(json.dumps(payload, indent=2) + "\n")
print(json.dumps(payload, indent=2))
PY

[[ "$DIAG_RC" -eq 0 && "$TRAIN_RC" -eq 0 ]]
