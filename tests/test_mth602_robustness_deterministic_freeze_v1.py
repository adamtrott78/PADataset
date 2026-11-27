import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
POST=ROOT/"experiments/mth602_robustness_posttrain_bundle.py"

def test_posttrain_freeze_enables_deterministic_algorithms():
    s=POST.read_text()
    assert "torch.use_deterministic_algorithms(True)" in s
    assert "torch.set_num_threads(min(4,max(1,os.cpu_count() or 1)))" in s

def test_posttrain_bundle_syntax():
    subprocess.run(["python3","-m","py_compile",str(POST)],check=True)
