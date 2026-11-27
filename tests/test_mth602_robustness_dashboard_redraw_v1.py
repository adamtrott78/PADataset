from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_dashboard_redraw_is_width_aware_and_full_screen_atomic():
    s=(ROOT/"scripts/mth602_robustness_local_dashboard.py").read_text()
    assert "get_terminal_size" in s
    assert "clip_ansi" in s
    assert '"\\033[2J\\033[H"+rendered' in s
    assert "time.sleep(2)" in s
