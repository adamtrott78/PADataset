from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_tmux_launcher_starts_dashboard_and_pipeline_and_attaches_dashboard():
    s=(ROOT/"scripts/mth602_robustness_tmux.sh").read_text()
    assert "mth602_robustness_local_dashboard.py" in s
    assert "mth602_robustness_local_pipeline.py" in s
    assert "--max-workers 2" in s
    assert "command -v python3" in s
    assert "select-window" in s
    assert "tmux attach" in s
