import numpy as np

from evaluate import collect_split_outputs_from_loader
from osr_core import SplitOutputs
from experiments.l2o_directional_contract import resolve_directional_l2o_contract
from experiments.l2o_pair_cached_dqnguard import save_split, load_split


def _base_cfg():
    return {
        "split_mode": "open_pa",
        "unknown_pas": ["PA1"],
        "target_unknown_pa": "PA1",
        "surrogate_open_pa": "PA2",
        "known_pas_l2o": ["PA3", "PA4", "PA8"],
        "pas": ["PA3", "PA4", "PA8", "PA1"],
        "open_val_frac": 0,
        "build_balanced_val_open": False,
        "quarantine_target_until_test": True,
    }


def test_directional_contract_restores_proven_track_a_eval_partition():
    c = resolve_directional_l2o_contract(
        _base_cfg(),
        evaluation_target="PA1",
        evaluation_surrogate="PA2",
        model_class_names=["PA3", "PA4", "PA8"],
    )
    assert c.target_config["open_val_frac"] == 0.15
    assert c.target_config["build_balanced_val_open"] is True
    assert c.surrogate_config["open_val_frac"] == 0.15
    assert c.surrogate_config["build_balanced_val_open"] is True
    assert c.surrogate_config["require_true_val_open"] is True
    assert c.surrogate_config["allow_val_open_fallback"] is False


def test_empty_optional_loader_returns_none():
    class DummyModel:
        def eval(self):
            return self

    class DummyHandle:
        model = DummyModel()

    assert collect_split_outputs_from_loader(DummyHandle(), [], "empty") is None


def test_pair_cache_split_round_trip(tmp_path):
    original = SplitOutputs(
        split_name="val_known",
        y_true=np.asarray([0, 1], dtype=np.int64),
        logits=np.asarray([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32),
        features=np.asarray([[5.0], [6.0]], dtype=np.float32),
        closed_pred=np.asarray([1, 1], dtype=np.int64),
        probs=np.asarray([[0.25, 0.75], [0.4, 0.6]], dtype=np.float32),
        sample_meta=None,
    )
    path = tmp_path / "split.npz"
    save_split(path, original)
    restored = load_split(path)

    assert restored.split_name == original.split_name
    for field in ("y_true", "logits", "features", "closed_pred", "probs"):
        np.testing.assert_array_equal(getattr(restored, field), getattr(original, field))
