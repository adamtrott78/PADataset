from __future__ import annotations

import json
from pathlib import Path

from experiments.l2o_control_request_contract import resolve_control_eval_request


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "manifests" / "l2o_canonical_backbone_matrix_v1.json"
PLAN = ROOT / "manifests" / "l2o_control_matrix_plan_v1.json"
POLICY = ROOT / "manifests" / "l2o_control_eval_policy_v1.json"
REQUEST_ROOT = ROOT / "manifests" / "configs" / "l2o_control_eval_v1"


def test_all_20_frozen_control_requests_resolve():
    requests = sorted(REQUEST_ROOT.glob("*.json"))
    assert len(requests) == 20
    seen = set()
    for request in requests:
        d = json.loads(request.read_text(encoding="utf-8"))
        r = resolve_control_eval_request(
            request_path=request,
            matrix_path=MATRIX,
            plan_path=PLAN,
            policy_path=POLICY,
            run_dir=Path("/tmp/frozen-run"),
            out_dir=Path("/tmp/frozen-out"),
        )
        key = (r.evaluation_target, r.evaluation_surrogate)
        assert key not in seen
        seen.add(key)
        assert r.checkpoint == "best_model"
        assert "--policy" in r.evaluator_args
    assert len(seen) == 20


def test_control_policy_locks_target_firewall_and_historical_semantics():
    d = json.loads(POLICY.read_text(encoding="utf-8"))
    assert d["policy_id"] == "l2o_repaired_controls_frozen_v1"
    assert d["target_labels_used_for_tuning"] is False
    assert d["target_test_consumed_before_final_eval"] is False
    q = d["controls"]["dqn_ids_style"]
    assert q["state_mode"] == "softmax3"
    assert q["known_cap"] == 625 and q["open_cap"] == 625
    assert q["open_calibration_source"] == "external_surrogate_validation"
    assert q["final_decision"] == "hard_dqn_argmax"
    v = d["controls"]["varmax"]
    assert v["calibration_mode"] == "surrogate_all"
    assert v["sweep_grid"] == "smoke"
    assert v["external_surrogate_consumed"] is False
