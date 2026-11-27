from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"scripts/mth602_robustness_local_pipeline.py"

def test_watcher_discovers_final_runner_outputs():
    s=P.read_text()
    assert '/backbone/mth602_final_robust_*' in s
    assert s.count('mth602_final_robust_*') >= 3

def test_watcher_compiles():
    subprocess.run(["python3","-m","py_compile",str(P)],check=True)
