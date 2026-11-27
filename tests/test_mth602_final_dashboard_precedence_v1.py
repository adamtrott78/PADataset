from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
DASH=ROOT/"scripts/mth602_robustness_local_dashboard.py"

def test_final_campaign_precedes_smoke_for_same_cell():
    s=DASH.read_text()
    assert 'final_rows=[r for r in rows if r["rn"].startswith("mth602_final_robust_")]' in s
    assert "display_rows=final_rows if final_rows else rows" in s
    assert 'bycell={(r["pair"],r["p"],r["t"]):r["status"] for r in display_rows}' in s

def test_final_osr_aggregate_excludes_smoke_when_final_rows_exist():
    s=DASH.read_text()
    assert "def osr_results(final_only=False):" in s
    assert 'pats=("mth602_final_robust_*",) if final_only else' in s
    assert "osr_results(final_only=bool(final_rows))" in s
    assert "FINAL " in s

def test_dashboard_compiles():
    subprocess.run(["python3","-m","py_compile",str(DASH)],check=True)
