from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
PIPE=ROOT/"scripts/mth602_robustness_local_pipeline.py"
DASH=ROOT/"scripts/mth602_robustness_local_dashboard.py"

def test_pipeline_discovers_smoke_and_final_campaign_prefixes():
    s=PIPE.read_text()
    assert "mth602_robust_*" in s
    assert "mth602_final_robust_*" in s
    assert "def list_spooled_backbones(backbones):" in s
    assert 'for pat in ("mth602_robust_*","mth602_final_robust_*")' in s

def test_dashboard_discovers_smoke_and_final_campaign_prefixes():
    s=DASH.read_text()
    assert 'rn.startswith(("mth602_robust_","mth602_final_robust_"))' in s
    assert "mth602_final_robust_*" in s
    assert 'for pat in ("mth602_robust_*","mth602_final_robust_*")' in s

def test_scripts_compile():
    subprocess.run(["python3","-m","py_compile",str(PIPE),str(DASH)],check=True)
