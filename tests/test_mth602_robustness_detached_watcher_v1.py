from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_watcher_is_systemd_managed_not_tmux_or_nohup():
    s=(ROOT/"scripts/mth602_robustness_tmux.sh").read_text()
    assert "systemd-run" in s
    assert "systemctl is-active" in s
    assert "nohup" not in s
    assert "PIPE_SESSION=" not in s

def test_systemd_watcher_uses_exact_dnn_python_and_operator_home():
    s=(ROOT/"scripts/mth602_robustness_tmux.sh").read_text()
    assert 'PYTHON_BIN="$(command -v python3)"' in s
    assert '--setenv=SUDO_USER="$OPERATOR_USER"' in s
    assert '"$PYTHON_BIN" "$ROOT/scripts/mth602_robustness_local_pipeline.py"' in s
    assert '--runtime-python "$PYTHON_BIN"' in s
