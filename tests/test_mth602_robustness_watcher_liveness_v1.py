from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_watcher_is_not_owned_by_tmux_lifecycle():
    s=(ROOT/"scripts/mth602_robustness_tmux.sh").read_text()
    assert "UI_SESSION=mth602-robustness-ui" in s
    assert "PIPE_SESSION=" not in s
    assert "nohup '$PYTHON_BIN'" in s
    assert "pipeline-watcher.pid" in s

def test_pipeline_state_has_liveness_heartbeat():
    s=(ROOT/"scripts/mth602_robustness_local_pipeline.py").read_text()
    assert '"epoch":time.time()' in s
    assert '"pid":os.getpid()' in s

def test_dashboard_marks_stale_pipeline():
    s=(ROOT/"scripts/mth602_robustness_local_dashboard.py").read_text()
    assert 'p_state="ALIVE"' in s
    assert '"STALE"' in s
    assert "PIPELINE {p_state}" in s
