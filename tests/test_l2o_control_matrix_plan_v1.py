import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "manifests" / "l2o_control_matrix_plan_v1.json"


def load_plan():
    return json.loads(PLAN.read_text(encoding="utf-8"))


def test_control_matrix_plan_is_frozen_and_complete():
    d = load_plan()
    assert d["status"] == "FROZEN_PLAN_NO_EXECUTION"
    assert d["source_binding"]["exact_head"] == "f1256048b51fd863ad3fb46f9c547eff401016e7"
    assert d["source_binding"]["canonical_backbone_count"] == 10
    assert d["source_binding"]["directed_cell_count"] == 20
    cells = d["cells"]
    assert len(cells) == 20
    assert len({c["cell_id"] for c in cells}) == 20
    assert len({c["canonical_key"] for c in cells}) == 10
    assert all(c["checkpoint"] == "best_model" for c in cells)
    assert all(c["target_test_consumed_before_final_eval"] is False for c in cells)


def test_dqn_ids_style_control_is_target_blind_and_matched():
    d = load_plan()["controls"]["dqn_ids_style_matched"]
    assert d["method_id"] == "dqn_ids_style_softmax3_external_surrogate_cap625_v1"
    assert d["state_features"] == ["p_max", "p1_p2_gap", "entropy"]
    assert d["calibration"]["known_cap"] == 625
    assert d["calibration"]["open_cap"] == 625
    assert d["calibration"]["open_source"] == "directional cell external-surrogate validation split"
    assert d["calibration"]["target_open_consumed"] is False
    assert d["calibration"]["target_test_consumed"] is False
    forbidden = set(d["forbidden"])
    assert "true-target validation during fit" in forbidden
    assert "Keras/Shreyash backbone substitution" in forbidden


def test_varmax_control_preserves_surrogate_all_semantics():
    d = load_plan()["controls"]["varmax_surrogate_all_matched"]
    assert d["method_id"] == "varmax_surrogate_all_smoke_matched_l2o_v1"
    assert d["modes"] == ["surrogate_all"]
    assert d["sweep_grid"] == "smoke"
    assert d["calibration"]["external_surrogate_consumed"] is False
    assert d["calibration"]["target_open_consumed"] is False
    assert d["calibration"]["target_test_consumed"] is False
    assert all(c["varmax_external_surrogate_consumed"] is False for c in load_plan()["cells"])


def test_execution_is_blocked_until_candidate_is_validated():
    d = load_plan()
    assert d["execution_gate"]["state"] == "BLOCKED_UNTIL_IMPLEMENTATION_VALIDATED"
