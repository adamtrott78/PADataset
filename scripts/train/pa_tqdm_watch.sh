#!/usr/bin/env bash
set -euo pipefail

RUN_DIR="${1:-results_pa_smoke/distinct_smoke_ent005_lr2e4_unkPA1_c16384_seed0}"
REFRESH="${REFRESH:-1}"

progress="$RUN_DIR/train_progress.json"

cleanup() {
  printf '\n'
  tput cnorm 2>/dev/null || true
}
trap cleanup EXIT INT TERM

tput civis 2>/dev/null || true

while true; do
  if [[ -f "$progress" ]]; then
    line="$(python - "$progress" <<'PY'
import json
import sys
from pathlib import Path

p = Path(sys.argv[1])
d = json.loads(p.read_text())

phase = d.get("phase", "?")
epoch = int(d.get("epoch", 0) or 0)
epochs = int(d.get("epochs", 0) or 0)
step = int(d.get("step", 0) or 0)
steps = int(d.get("steps", 0) or 0)
pct = float(d.get("pct", 0.0) or 0.0)
sps = float(d.get("steps_per_sec", 0.0) or 0.0)

bar_width = 10
filled = int(bar_width * pct / 100.0)
filled = max(0, min(bar_width, filled))
bar = "█" * filled + " " * (bar_width - filled)

elapsed = 0
eta = None
if sps > 0 and step > 0:
    elapsed = int(step / sps)
    eta = int(max(0, steps - step) / sps)

def fmt(sec):
    if sec is None:
        return "?"
    sec = int(sec)
    if sec >= 3600:
        return f"{sec//3600:d}:{(sec%3600)//60:02d}:{sec%60:02d}"
    return f"{sec//60:02d}:{sec%60:02d}"

if phase == "validation":
    print(f"Epoch {epoch}/{epochs}: validating... [{fmt(elapsed)}<?, ?it/s]")
elif phase == "epoch_done":
    print(f"Epoch {epoch}/{epochs}: 100%|{'█' * bar_width}| {steps}/{steps} [{fmt(elapsed)}<00:00, {sps:.2f}it/s]")
else:
    print(f"Epoch {epoch}/{epochs}: {pct:3.0f}%|{bar}| {step}/{steps} [{fmt(elapsed)}<{fmt(eta)}, {sps:.2f}it/s]")
PY
)"
    printf '\r\033[2K%s' "$line"
  else
    printf '\r\033[2Kwaiting for %s...' "$progress"
  fi

  sleep "$REFRESH"
done
