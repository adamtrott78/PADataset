from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]

def test_dashboard_reads_completed_osr_results_and_displays_unknown_f1():
    s=(ROOT/"scripts/mth602_robustness_local_dashboard.py").read_text()
    assert "def osr_results(final_only=False)" in s
    assert 'readj(od/"osr_complete.json")' in s
    assert 'readj(od/"result.json")' in s
    assert "OSR RESULTS" in s
    assert "DQNG-UF1" in s
    assert "IDS-UF1" in s
    assert "VMAX-UF1" in s
    assert "unknown_f1" in s
    assert "completed directions=" in s
    assert "mean U-F1" in s

def test_dashboard_python_syntax():
    subprocess.run(["python3","-m","py_compile",str(ROOT/"scripts/mth602_robustness_local_dashboard.py")],check=True)
