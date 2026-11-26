from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_pipeline_accepts_explicit_state_root_and_heartbeats_before_discovery():
    s=(ROOT/"scripts/mth602_robustness_local_pipeline.py").read_text()
    assert 'ap.add_argument("--state-root",default=None)' in s
    assert 'Path(a.state_root).expanduser() if a.state_root' in s
    hb=s.index('atomic_json(root/"pipeline_state.json"')
    discover=s.index('for rn,src in discover().items()')
    assert hb < discover
    assert '"phase":"STARTING"' in s
    assert '"phase":"RUNNING"' in s

def test_launcher_binds_exact_state_root_to_systemd_watcher():
    s=(ROOT/"scripts/mth602_robustness_tmux.sh").read_text()
    assert '--state-root "$STATE_ROOT"' in s
    assert "systemd-run" in s
