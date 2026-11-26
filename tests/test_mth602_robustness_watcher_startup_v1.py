from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_launcher_authenticates_and_fails_closed():
    s=(ROOT/"scripts/mth602_robustness_tmux.sh").read_text()
    assert "sudo -v" in s
    assert "sudo -E bash -c" in s
    assert "nohup '$PYTHON_BIN'" in s
    assert "sudo -n" not in s
    assert "PIPELINE_WATCHER_START=FAIL" in s
    assert "PIPELINE_WATCHER_START=PASS" in s
    assert "pipeline-watcher.log" in s
    assert "tail -n 80" in s

def test_launcher_only_restarts_ui_when_watcher_is_healthy():
    s=(ROOT/"scripts/mth602_robustness_tmux.sh").read_text()
    assert "pipeline_healthy=1" in s
    assert 'kill-session -t "$UI_SESSION"' in s
    assert "os.kill(pid,0)" in s
    assert "age <= 5.0" in s
