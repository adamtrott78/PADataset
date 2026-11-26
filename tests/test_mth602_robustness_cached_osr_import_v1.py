from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]

def test_cached_osr_adds_repo_root_before_osr_core_import():
    s=(ROOT/"experiments/mth602_robustness_cached_all_osr.py").read_text()
    assert "REPO_ROOT=Path(__file__).resolve().parents[1]" in s
    assert "sys.path.insert(0,str(REPO_ROOT))" in s
    assert s.index("sys.path.insert(0,str(REPO_ROOT))") < s.index("from osr_core import")

def test_cached_osr_cli_imports_cleanly():
    p=subprocess.run(
        ["python3",str(ROOT/"experiments/mth602_robustness_cached_all_osr.py"),"--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert p.returncode == 0, p.stderr

def test_pipeline_quarantines_nonzero_worker_exit():
    s=(ROOT/"scripts/mth602_robustness_local_pipeline.py").read_text()
    assert "failed_workers={}" in s
    assert 'if rc != 0:' in s
    assert 'failed_workers[rn]={' in s
    assert 'd.name in failed_workers' in s
    assert '"failed_workers":failed_workers' in s

def test_dashboard_surfaces_failed_worker_count():
    s=(ROOT/"scripts/mth602_robustness_local_dashboard.py").read_text()
    assert "failed {len(ps.get('failed_workers',{}))}" in s
