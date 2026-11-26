#!/usr/bin/env bash
set -euo pipefail
UI_SESSION=mth602-robustness-ui
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="$(command -v python3)"
STATE_ROOT="$HOME/.cache/workspace-control/mth602-robustness-pipeline"
STATE_FILE="$STATE_ROOT/pipeline_state.json"
LOG_DIR="$STATE_ROOT/logs"
WATCHER_LOG="$LOG_DIR/pipeline-watcher.log"
WATCHER_PID_FILE="$STATE_ROOT/pipeline-watcher.pid"

echo "Authenticating sudo for background watcher..."
sudo -v

OPERATOR_USER="${SUDO_USER:-$USER}"
OPERATOR_GROUP="$(id -gn "$OPERATOR_USER")"
sudo mkdir -p "$STATE_ROOT" "$LOG_DIR"
sudo chown "$OPERATOR_USER:$OPERATOR_GROUP" "$STATE_ROOT" "$LOG_DIR"
touch "$WATCHER_LOG"

pipeline_healthy=0
if [[ -f "$STATE_FILE" ]]; then
  if "$PYTHON_BIN" - "$STATE_FILE" <<'PY'
import json,os,sys,time
try:
    s=json.load(open(sys.argv[1]))
    age=time.time()-float(s["epoch"])
    pid=int(s.get("pid",0))
    os.kill(pid,0)
    raise SystemExit(0 if age <= 5.0 else 1)
except Exception:
    raise SystemExit(1)
PY
  then
    pipeline_healthy=1
  fi
fi

if [[ "$pipeline_healthy" -ne 1 ]]; then
  : > "$WATCHER_LOG"
  sudo -E bash -c "
    export SUDO_USER='$OPERATOR_USER'
    export CUDA_VISIBLE_DEVICES=''
    export OMP_NUM_THREADS=4
    export MKL_NUM_THREADS=4
    export OPENBLAS_NUM_THREADS=4
    export NUMEXPR_NUM_THREADS=4
    nohup '$PYTHON_BIN' '$ROOT/scripts/mth602_robustness_local_pipeline.py' \
      --repo '$ROOT' \
      --runtime-python '$PYTHON_BIN' \
      --max-workers 2 \
      --refresh 1 \
      >>'$WATCHER_LOG' 2>&1 </dev/null &
    echo \$! > '$WATCHER_PID_FILE'
  "
  sudo chown "$OPERATOR_USER:$OPERATOR_GROUP" "$WATCHER_PID_FILE" "$WATCHER_LOG" 2>/dev/null || true
fi

watcher_ok=0
for _ in $(seq 1 30); do
  if [[ -f "$STATE_FILE" ]] && "$PYTHON_BIN" - "$STATE_FILE" <<'PY'
import json,os,sys,time
try:
    s=json.load(open(sys.argv[1]))
    age=time.time()-float(s["epoch"])
    pid=int(s.get("pid",0))
    os.kill(pid,0)
    raise SystemExit(0 if age <= 5.0 else 1)
except Exception:
    raise SystemExit(1)
PY
  then
    watcher_ok=1
    break
  fi
  sleep 0.5
done

if [[ "$watcher_ok" -ne 1 ]]; then
  echo "PIPELINE_WATCHER_START=FAIL"
  echo "Watcher log:"
  tail -n 80 "$WATCHER_LOG" 2>/dev/null || true
  exit 1
fi

echo "PIPELINE_WATCHER_START=PASS"
"$PYTHON_BIN" - "$STATE_FILE" <<'PY'
import json,sys,time
s=json.load(open(sys.argv[1]))
print(f"PIPELINE_PID={s.get('pid')}")
print(f"PIPELINE_HEARTBEAT_AGE_SEC={max(0.0,time.time()-float(s['epoch'])):.2f}")
print(f"SPOOLED={s.get('backbones_spooled')}")
print(f"OSR_COMPLETE={s.get('osr_complete')}")
PY

tmux kill-session -t "$UI_SESSION" 2>/dev/null || true
tmux new-session -d -s "$UI_SESSION" -n dashboard "exec '$PYTHON_BIN' '$ROOT/scripts/mth602_robustness_local_dashboard.py'"
exec tmux attach -t "$UI_SESSION"
