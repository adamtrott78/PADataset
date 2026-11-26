import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"experiments/mth602_robustness_parity_gate.py"
MANIFEST=ROOT/"manifests/mth602_robustness_parity_smoke_v1.json"

def test_parity_manifest_pins_exact_four_smokes_and_two_gpus():
    d=json.loads(MANIFEST.read_text())
    assert d["schema"]=="padataset.mth602-robustness-parity-smoke.v1"
    assert d["status"]=="READY_FOR_LOCAL_PARITY_GATE"
    assert d["abs_tolerance"]==1e-6
    assert d["methods"]==["DQNGuard","DQN-IDS-style","VarMax"]
    assert len(d["metrics"])==7
    assert sorted(x["gpu"] for x in d["lanes"])==[0,1]
    cells=[c for lane in d["lanes"] for c in lane["cells"]]
    assert len(cells)==4
    assert len({c["run_name"] for c in cells})==4
    assert {c["run_name"] for c in cells}=={
        "mth602_robust_smoke_A_PA1_PA2_p01_t00",
        "mth602_robust_smoke_A_PA3_PA8_p01_t00",
        "mth602_robust_smoke_B_PA2_PA4_p02_t00",
        "mth602_robust_smoke_B_PA4_PA8_p02_t00",
    }
    assert d["invariants"]["checkpoint"]=="best_model"
    assert d["invariants"]["dqn_seed"]==42
    assert d["invariants"]["target_labels_used_for_tuning"] is False
    assert d["invariants"]["canonical_state_mutation"] is False
    assert d["invariants"]["retraining"] is False

def test_parity_driver_uses_frozen_canonical_semantics_and_all_metrics():
    s=SCRIPT.read_text()
    required=[
        "pa_eval_dqn_guard_surrogate_open.py",
        "pa_eval_l2o_controls_v1.py",
        "--checkpoint", "best_model",
        "--mode", "var_energy",
        "--decision-mode", "score_threshold",
        "--max-known-reject-cal", "0.05",
        "--known-cap", "625",
        "--open-cap", "625",
        "l2o_control_eval_policy_v1.json",
        "CUDA_VISIBLE_DEVICES",
        "ThreadPoolExecutor(max_workers=2)",
        "expected_method_direction_rows",
        "metric_comparisons",
        "target_labels_used_for_tuning",
        "canonical_state_modified",
        "retraining_performed",
    ]
    for marker in required:
        assert marker in s, marker
    for metric in (
        "known_reject_rate","unknown_precision","unknown_recall","unknown_f1",
        "osr_acc","osr_macro_f1","unknown_auroc",
    ):
        assert metric in s

def test_parity_driver_is_syntax_valid_and_help_works():
    subprocess.run(["python3","-m","py_compile",str(SCRIPT)],check=True)
    p=subprocess.run(["python3",str(SCRIPT),"--help"],text=True,capture_output=True)
    assert p.returncode==0, p.stderr
    assert "--pipeline-root" in p.stdout
    assert "--data-root" in p.stdout
    assert "--fresh" in p.stdout
