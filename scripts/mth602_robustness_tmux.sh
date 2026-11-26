#!/usr/bin/env bash
set -euo pipefail
PIPE_SESSION=mth602-robustness-pipeline
UI_SESSION=mth602-robustness-ui
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="$(command -v python3)"
STATE_ROOT="$HOME/.cache/workspace-control/mth602-robustness-pipeline"
STATE_FILE="$STATE_ROOT/pipeline_state.json"
LOG_DIR="$STATE_ROOT/logs"
WATCHER_LOG="$LOG_DIR/pipeline-watcher.log"

echo "Authenticating sudo for background watcher..."
sudo -v

# Earlier versions may have left this task-scoped state directory root-owned.
OPERATOR_USER="${SUDO_USER:-$USER}"
OPERATOR_GROUP="$(id -gn "$OPERATOR_USER")"
sudo mkdir -p "$STATE_ROOT" "$LOG_DIR"
sudo chown "$OPERATOR_USER:$OPERATOR_GROUP" "$STATE_ROOT" "$LOG_DIR"
touch "$WATCHER_LOG"

# Kill only stale/missing-heartbeat pipeline sessions. Never bounce a healthy watcher.
pipeline_healthy=0
if tmux has-session -t "$PIPE_SESSION" 2>/dev/null && [[ -f "$STATE_FILE" ]]; then
  if python3 - "$STATE_FILE" <<'PY'
import json,sys,time
try:
    s=json.load(open(sys.argv[1]))
    age=time.time()-float(s["epoch"])
    raise SystemExit(0 if age <= 5.0 else 1)
except Exception:
    raise SystemExit(1)
PY
  then
    pipeline_healthy=1
  fi
fi

if [[ "$pipeline_healthy" -ne 1 ]]; then
  tmux kill-session -t "$PIPE_SESSION" 2>/dev/null || true
  : > "$WATCHER_LOG"
  tmux new-session -d -s "$PIPE_SESSION" -n pipeline     "exec sudo -n -E python3 '$ROOT/scripts/mth602_robustness_local_pipeline.py' --repo '$ROOT' --runtime-python '$PYTHON_BIN' --max-workers 2 --refresh 1 >>'$WATCHER_LOG' 2>&1"
fi

# Fail closed unless the watcher proves liveness.
watcher_ok=0
for _ in $(seq 1 20); do
  if [[ -f "$STATE_FILE" ]] && python3 - "$STATE_FILE" <<'PY'
import json,sys,time
try:
    s=json.load(open(sys.argv[1]))
    age=time.time()-float(s["epoch"])
    raise SystemExit(0 if age <= 5.0 and int(s.get("pid",0)) > 0 else 1)
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
python3 - "$STATE_FILE" <<'PY'
import json,sys,time
s=json.load(open(sys.argv[1]))
print(f"PIPELINE_PID={s.get('pid')}")
print(f"PIPELINE_HEARTBEAT_AGE_SEC={max(0.0,time.time()-float(s['epoch'])):.2f}")
print(f"SPOOLED={s.get('backbones_spooled')}")
print(f"OSR_COMPLETE={s.get('osr_complete')}")
PY

# UI is disposable; restarting it must never touch the pipeline session.
tmux kill-session -t "$UI_SESSION" 2>/dev/null || true
tmux new-session -d -s "$UI_SESSION" -n dashboard   "exec sudo -n -E python3 '$ROOT/scripts/mth602_robustness_local_dashboard.py'"

exec tmux attach -t "$UI_SESSION"
