import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"experiments/mth602_robustness_same_evidence_parity.py"

def test_same_evidence_gate_uses_exact_cached_tensors_and_frozen_constructors():
    s=SCRIPT.read_text()
    for marker in [
        "known_val.npz","known_test.npz","val_open_{surrogate}.npz",
        "target_cache/test_open_{target}.npz",
        "make_method","make_dqn_control","make_varmax_control",
        "cap_split","dqnguard_threshold","final_pred",
        "ThreadPoolExecutor(max_workers=2)",
        "SAME_EVIDENCE_PARITY=",
    ]:
        assert marker in s, marker
    assert "CUDA_VISIBLE_DEVICES" in s
    assert "target_labels_used_for_tuning" in s

def test_same_evidence_gate_requires_prediction_identity_and_tiny_metric_tolerance():
    s=SCRIPT.read_text()
    assert "kp_mismatch==0" in s
    assert "op_mismatch==0" in s
    assert "default=1e-12" in s

def test_same_evidence_gate_syntax_and_help():
    subprocess.run(["python3","-m","py_compile",str(SCRIPT)],check=True)
    p=subprocess.run(["python3",str(SCRIPT),"--help"],capture_output=True,text=True)
    assert p.returncode==0,p.stderr
    assert "--pipeline-root" in p.stdout
    assert "--tolerance" in p.stdout
