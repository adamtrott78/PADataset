from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_cached_osr_adds_repo_root_before_osr_core_import():
    src=(ROOT/"experiments/mth602_robustness_cached_all_osr.py").read_text()
    assert "REPO_ROOT=Path(__file__).resolve().parents[1]" in src
    assert "sys.path.insert(0,str(REPO_ROOT))" in src
    assert src.index("sys.path.insert(0,str(REPO_ROOT))") < src.index("from osr_core import")

def test_osr_core_local_dependencies_exist_at_repo_root():
    src=(ROOT/"osr_core.py").read_text()
    assert "from prepData import" in src
    assert "from discriminate import" in src
    assert (ROOT/"prepData.py").is_file()
    assert (ROOT/"discriminate.py").is_file()

def test_pipeline_quarantines_nonzero_worker_exit():
    src=(ROOT/"scripts/mth602_robustness_local_pipeline.py").read_text()
    assert "failed_workers={}" in src
    assert "if rc != 0:" in src
    assert "failed_workers[rn]={" in src
    assert "d.name in failed_workers" in src
    assert '"failed_workers":failed_workers' in src

def test_dashboard_surfaces_failed_worker_count():
    src=(ROOT/"scripts/mth602_robustness_local_dashboard.py").read_text()
    assert "failed {len(ps.get('failed_workers',{}))}" in src
