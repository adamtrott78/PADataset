#!/usr/bin/env bash
set -euo pipefail
SESSION=mth602-robustness
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="$(command -v python3)"
tmux kill-session -t "$SESSION" 2>/dev/null || true
tmux new-session -d -s "$SESSION" -n dashboard "sudo -E python3 '$ROOT/scripts/mth602_robustness_local_dashboard.py'"
tmux new-window -t "$SESSION" -n pipeline "sudo -E python3 '$ROOT/scripts/mth602_robustness_local_pipeline.py' --repo '$ROOT' --runtime-python '$PYTHON_BIN' --max-workers 2 --refresh 2"
tmux select-window -t "$SESSION:dashboard"
exec tmux attach -t "$SESSION"
