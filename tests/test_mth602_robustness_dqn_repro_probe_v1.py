import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"experiments/mth602_robustness_dqn_repro_probe.py"

def test_probe_enforces_deterministic_single_thread_cpu_envelope():
    s=SCRIPT.read_text()
    for marker in [
        'OMP_NUM_THREADS"]="1"',
        'MKL_NUM_THREADS"]="1"',
        'OPENBLAS_NUM_THREADS"]="1"',
        'NUMEXPR_NUM_THREADS"]="1"',
        'CUDA_VISIBLE_DEVICES"]=""',
        'torch.set_num_threads(1)',
        'torch.use_deterministic_algorithms(True)',
        'from experiments.mth602_robustness_posttrain_bundle import _fit_one',
        'weight_identity',
        'known_pred_mismatch',
        'DQN_REPRO=',
    ]:
        assert marker in s, marker

def test_probe_requires_exact_identity():
    s=SCRIPT.read_text()
    assert 'threshold_delta"]==0.0' in s
    assert 'known_score_max_abs_delta"]==0.0' in s
    assert 'known_pred_mismatch"]==0' in s

def test_probe_syntax():
    subprocess.run(["python3","-m","py_compile",str(SCRIPT)],check=True)
