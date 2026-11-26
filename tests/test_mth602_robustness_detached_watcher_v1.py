from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_watcher_uses_foreground_authenticated_detached_sudo_launch():
    s=(ROOT/"scripts/mth602_robustness_tmux.sh").read_text()
    assert "sudo -v" in s
    assert "sudo -E bash -c" in s
    assert "nohup '$PYTHON_BIN'" in s
    assert "pipeline-watcher.pid" in s
    assert "sudo -n" not in s

def test_dashboard_runs_unprivileged_and_health_uses_pid_plus_heartbeat():
    s=(ROOT/"scripts/mth602_robustness_tmux.sh").read_text()
    assert "os.kill(pid,0)" in s
    assert "age <= 5.0" in s
    assert "exec '$PYTHON_BIN'" in s
    assert "exec sudo" not in s
