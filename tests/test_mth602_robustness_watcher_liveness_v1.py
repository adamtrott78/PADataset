from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_dashboard_restart_cannot_kill_pipeline_session():
    s=(ROOT/"scripts/mth602_robustness_tmux.sh").read_text()
    assert "PIPE_SESSION=mth602-robustness-pipeline" in s
    assert "UI_SESSION=mth602-robustness-ui" in s
    assert 'has-session -t "$PIPE_SESSION"' in s
    assert 'kill-session -t "$UI_SESSION"' in s
    # A stale/missing-heartbeat pipeline session may be recycled, but a healthy
    # one is preserved by the pipeline_healthy guard.
    assert "pipeline_healthy=1" in s
    assert 'if [[ "$pipeline_healthy" -ne 1 ]]' in s
    assert 'kill-session -t "$PIPE_SESSION"' in s

def test_pipeline_state_has_liveness_heartbeat():
    s=(ROOT/"scripts/mth602_robustness_local_pipeline.py").read_text()
    assert '"epoch":time.time()' in s
    assert '"pid":os.getpid()' in s

def test_dashboard_marks_stale_pipeline():
    s=(ROOT/"scripts/mth602_robustness_local_dashboard.py").read_text()
    assert 'p_state="ALIVE"' in s
    assert '"STALE"' in s
    assert "PIPELINE {p_state}" in s
