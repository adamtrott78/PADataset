from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_launcher_repairs_task_state_permissions_after_sudo_auth():
    s=(ROOT/"scripts/mth602_robustness_tmux.sh").read_text()
    assert s.index("sudo -v") < s.index('sudo mkdir -p "$STATE_ROOT" "$LOG_DIR"')
    assert 'OPERATOR_USER="${SUDO_USER:-$USER}"' in s
    assert 'OPERATOR_GROUP="$(id -gn "$OPERATOR_USER")"' in s
    assert 'sudo chown "$OPERATOR_USER:$OPERATOR_GROUP" "$STATE_ROOT" "$LOG_DIR"' in s
    assert "chown -R" not in s
