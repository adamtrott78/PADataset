from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "manifests" / "l2o_control_eval_policy_v1.json"
EVALUATOR = ROOT / "experiments" / "pa_eval_l2o_controls_v1.py"


def test_dqn_control_factory_is_plain_softmax3_dqn():
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    d = policy["controls"]["dqn_ids_style"]
    source = EVALUATOR.read_text(encoding="utf-8")
    assert d["state_mode"] == "softmax3"
    assert d["episodes"] == 30
    assert d["anchor_fraction"] == 0.05
    assert d["train_subsample_size"] == 1250
    assert d["centroid_update_threshold"] == 0.75
    assert "return DQNOSR(" in source
    assert 'state_mode="softmax3"' in source
    assert "BandedGuardDQNOSR" not in source


def test_policy_has_no_dqnguard_band_or_threshold_fields_for_dqn_control():
    p = json.loads(POLICY.read_text(encoding="utf-8"))
    d = p["controls"]["dqn_ids_style"]
    forbidden = {"band_accept_mode", "band_weight", "max_known_reject_cal", "decision_mode"}
    assert forbidden.isdisjoint(d)
    source = EVALUATOR.read_text(encoding="utf-8")
    assert "known-only percentile" not in source.lower()
    assert "score_threshold" not in source
