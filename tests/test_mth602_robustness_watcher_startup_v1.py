from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_launcher_authenticates_before_background_start_and_fails_closed():
    s=(ROOT/"scripts/mth602_robustness_tmux.sh").read_text()
    assert "sudo -v" in s
    assert "sudo -n -E python3" in s
    assert "PIPELINE_WATCHER_START=FAIL" in s
    assert "PIPELINE_WATCHER_START=PASS" in s
    assert "pipeline-watcher.log" in s
    assert "tail -n 80" in s

def test_launcher_preserves_healthy_pipeline_and_only_restarts_ui():
    s=(ROOT/"scripts/mth602_robustness_tmux.sh").read_text()
    assert "pipeline_healthy=1" in s
    assert 'kill-session -t "$PIPE_SESSION"' in s
    assert 'kill-session -t "$UI_SESSION"' in s
    assert "age <= 5.0" in s
