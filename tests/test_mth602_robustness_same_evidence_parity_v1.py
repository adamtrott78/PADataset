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
        "ProcessPoolExecutor(max_workers=2)", "_fit_one", "load_backbone_run",
        "SAME_EVIDENCE_PARITY=",
    ]:
        assert marker in s, marker
    assert "CUDA_VISIBLE_DEVICES" in s
    assert "target_labels_used_for_tuning" in s

def test_same_evidence_gate_replays_exact_production_freeze():
    s=SCRIPT.read_text()
    assert "from experiments.mth602_robustness_posttrain_bundle import _fit_one" in s
    assert "fr=_fit_one(" in s
    assert "load_backbone_run(str(run_dir),\"best_model\",device=\"cpu\")" in s

def test_same_evidence_gate_uses_process_isolation_for_dqn_rng():
    s=SCRIPT.read_text()
    assert "ProcessPoolExecutor" in s
    assert "ThreadPoolExecutor" not in s

def test_same_evidence_gate_requires_prediction_identity_and_tiny_metric_tolerance():
    s=SCRIPT.read_text()
    assert "kp_mismatch==0" in s
    assert "op_mismatch==0" in s
    assert "default=1e-12" in s

def test_same_evidence_gate_syntax_and_cli_markers():
    subprocess.run(["python3","-m","py_compile",str(SCRIPT)],check=True)
    s=SCRIPT.read_text()
    assert 'ap.add_argument("--pipeline-root"' in s
    assert 'ap.add_argument("--tolerance"' in s
