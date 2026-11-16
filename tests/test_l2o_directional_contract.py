from __future__ import annotations

import copy
import pytest

from experiments.l2o_directional_contract import resolve_directional_l2o_contract


def _cfg():
    return {
        "split_mode": "open_pa",
        "unknown_pas": ["PA1"],
        "pas": ["PA2", "PA3", "PA8", "PA1"],
        "target_unknown_pa": "PA1",
        "surrogate_open_pa": "PA4",
        "known_pas_l2o": ["PA2", "PA3", "PA8"],
        "seed": 0,
    }


def test_original_direction_preserves_target_and_surrogate_roles():
    c = resolve_directional_l2o_contract(
        _cfg(),
        evaluation_target="PA1",
        evaluation_surrogate="PA4",
        model_class_names=["PA2", "PA3", "PA8"],
    )
    assert c.canonical_excluded_pair == ("PA1", "PA4")
    assert c.directional_reuse is False
    assert c.target_config["unknown_pas"] == ["PA1"]
    assert c.target_config["pas"] == ["PA2", "PA3", "PA8", "PA1"]
    assert c.surrogate_config["unknown_pas"] == ["PA4"]
    assert c.surrogate_config["pas"] == ["PA2", "PA3", "PA8", "PA4"]


def test_reverse_direction_reuses_same_backbone_without_target_in_surrogate_dataset():
    c = resolve_directional_l2o_contract(
        _cfg(),
        evaluation_target="PA4",
        evaluation_surrogate="PA1",
        model_class_names=["PA2", "PA3", "PA8"],
    )
    assert c.directional_reuse is True
    assert c.evaluation_target == "PA4"
    assert c.evaluation_surrogate == "PA1"
    assert c.target_config["unknown_pas"] == ["PA4"]
    assert c.target_config["pas"] == ["PA2", "PA3", "PA8", "PA4"]
    assert c.surrogate_config["unknown_pas"] == ["PA1"]
    assert c.surrogate_config["pas"] == ["PA2", "PA3", "PA8", "PA1"]
    assert "PA4" not in c.surrogate_config["pas"]


def test_rejects_pair_not_excluded_by_backbone():
    with pytest.raises(ValueError, match="does not match"):
        resolve_directional_l2o_contract(
            _cfg(),
            evaluation_target="PA1",
            evaluation_surrogate="PA2",
            model_class_names=["PA2", "PA3", "PA8"],
        )


def test_rejects_checkpoint_class_order_drift():
    with pytest.raises(ValueError, match="class_names"):
        resolve_directional_l2o_contract(
            _cfg(),
            evaluation_target="PA1",
            evaluation_surrogate="PA4",
            model_class_names=["PA3", "PA2", "PA8"],
        )


def test_rejects_backbone_pas_provenance_drift():
    cfg = _cfg()
    cfg["pas"] = ["PA2", "PA3", "PA8", "PA4"]
    with pytest.raises(ValueError, match="provenance drift"):
        resolve_directional_l2o_contract(
            cfg,
            evaluation_target="PA1",
            evaluation_surrogate="PA4",
            model_class_names=["PA2", "PA3", "PA8"],
        )


def test_does_not_mutate_source_config():
    cfg = _cfg()
    before = copy.deepcopy(cfg)
    resolve_directional_l2o_contract(
        cfg,
        evaluation_target="PA4",
        evaluation_surrogate="PA1",
        model_class_names=["PA2", "PA3", "PA8"],
    )
    assert cfg == before
