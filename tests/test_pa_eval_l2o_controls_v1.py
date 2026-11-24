from __future__ import annotations

import json
from pathlib import Path

from experiments.pa_eval_l2o_controls_v1 import load_policy, make_dqn_control


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "manifests" / "l2o_control_eval_policy_v1.json"


def test_dqn_control_factory_is_plain_softmax3_dqn():
    p = load_policy(POLICY)
    dqn = make_dqn_control(p)
    assert dqn.state_mode == "softmax3"
    assert dqn.episodes == 30
    assert dqn.anchor_fraction == 0.05
    assert dqn.train_subsample_size == 1250
    assert dqn.centroid_update_threshold == 0.75


def test_policy_has_no_dqnguard_band_or_threshold_fields_for_dqn_control():
    p = json.loads(POLICY.read_text(encoding="utf-8"))
    d = p["controls"]["dqn_ids_style"]
    forbidden = {"band_accept_mode", "band_weight", "max_known_reject_cal", "decision_mode"}
    assert forbidden.isdisjoint(d)
