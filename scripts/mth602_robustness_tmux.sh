#!/usr/bin/env bash
set -euo pipefail
SESSION=mth602-robustness
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmux kill-session -t "$SESSION" 2>/dev/null || true
tmux new-session -d -s "$SESSION" "sudo -E python3 '$ROOT/scripts/mth602_robustness_local_dashboard.py'"
exec tmux attach -t "$SESSION"
