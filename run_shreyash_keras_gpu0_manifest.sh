#!/usr/bin/env bash
set -euo pipefail

export CUDA_VISIBLE_DEVICES=0
export TF_FORCE_GPU_ALLOW_GROWTH=true
export TF_CPP_MIN_LOG_LEVEL=2
export LD_LIBRARY_PATH="$(python - <<'PYLIB'
import pathlib, sysconfig
purelib = pathlib.Path(sysconfig.get_paths()["purelib"])
nvidia = purelib / "nvidia"
dirs = []
if nvidia.exists():
    for d in sorted(nvidia.glob("*/lib")):
        dirs.append(str(d))
print(":".join(dirs))
PYLIB
):${LD_LIBRARY_PATH:-}"

MANIFEST="${1:-manifests/shreyash_keras_og_gpu0.tsv}"
mkdir -p results_pa_shreyash_keras/_logs

tail -n +2 "$MANIFEST" | while IFS=$'\t' read -r CFG OUT_DIR; do
  [ -z "${CFG:-}" ] && continue
  [ -z "${OUT_DIR:-}" ] && continue

  RUN_NAME="$(basename "$OUT_DIR")"
  LOG="results_pa_shreyash_keras/_logs/${RUN_NAME}.log"

  echo
  echo "=== SHREYASH KERAS | cfg=$CFG | out=$OUT_DIR | gpu=0 ==="

  python experiments/train_shreyash_keras_pa_stream.py \
    --cfg "$CFG" \
    --out-dir "$OUT_DIR" \
    --epochs 120 \
    --batch-size 500 \
    --predict-batch-size 512 \
    --resume \
    --epoch-metric-n 625 \
    --epoch-metric-every 5 \
    2>&1 | tee "$LOG"
done
