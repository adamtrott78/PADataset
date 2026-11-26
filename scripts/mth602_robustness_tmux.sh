#!/usr/bin/env bash
set -euo pipefail
PIPE_SESSION=mth602-robustness-pipeline
UI_SESSION=mth602-robustness-ui
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="$(command -v python3)"

if ! tmux has-session -t "$PIPE_SESSION" 2>/dev/null; then
  tmux new-session -d -s "$PIPE_SESSION" -n pipeline     "sudo -E python3 '$ROOT/scripts/mth602_robustness_local_pipeline.py' --repo '$ROOT' --runtime-python '$PYTHON_BIN' --max-workers 2 --refresh 1"
fi

tmux kill-session -t "$UI_SESSION" 2>/dev/null || true
tmux new-session -d -s "$UI_SESSION" -n dashboard   "sudo -E python3 '$ROOT/scripts/mth602_robustness_local_dashboard.py'"

exec tmux attach -t "$UI_SESSION"
