from __future__ import annotations

import pytest

from experiments.l2o_hpo_extract import per_class_f1_from_confusion, record_from_payloads
from experiments.l2o_hpo_rank import validate_known_only_record


def _config():
    return {
        "hpo_trial": {
            "trial_id": "PA2-PA3__t000",
            "canonical_pair": "PA2-PA3",
            "stage": "screen",
            "selection_evidence": "known_validation_only",
            "target_metrics_allowed_for_selection": False,
            "test_metrics_allowed_for_selection": False,
        }
    }


def _summary():
    return {
        "best_epoch": 4,
        "best_val_macro_f1": 0.95,
        "class_names": ["PA1", "PA4", "PA8"],
        "target_test_consumed": False,
        "test_known_macro_f1": 0.01,
    }


def _checkpoint():
    return {
        "class_names": ["PA1", "PA4", "PA8"],
        "val_stats": {
            "macro_f1": 0.95,
            "confusion_matrix": [
                [90, 10, 0],
                [5, 95, 0],
                [0, 0, 100],
            ],
        },
    }


def test_per_class_f1():
    f1 = per_class_f1_from_confusion([[90, 10], [5, 95]])
    assert f1[0] == pytest.approx(180 / 195)
    assert f1[1] == pytest.approx(190 / 205)


def test_extractor_emits_ranker_safe_known_only_record():
    record = record_from_payloads(
        _config(),
        _summary(),
        _checkpoint(),
        config_path="manifests/configs/example.json",
        repo_config_sha256="a" * 64,
    )
    assert set(record) == {
        "trial_id",
        "canonical_pair",
        "stage",
        "config_path",
        "config_sha256",
        "status",
        "best_epoch",
        "val_macro_f1",
        "val_min_class_f1",
        "val_per_class_f1",
    }
    assert "test_known_macro_f1" not in record
    assert validate_known_only_record(record, expected_stage="screen")["trial_id"] == "PA2-PA3__t000"


def test_extractor_rejects_target_consumed_artifact():
    summary = _summary()
    summary["target_test_consumed"] = True
    with pytest.raises(ValueError, match="consumed target test"):
        record_from_payloads(
            _config(),
            summary,
            _checkpoint(),
            config_path="cfg.json",
        )


@pytest.mark.parametrize("field", ["target_metrics_allowed_for_selection", "test_metrics_allowed_for_selection"])
def test_extractor_rejects_selection_policy_drift(field):
    config = _config()
    config["hpo_trial"][field] = True
    with pytest.raises(ValueError, match="must be forbidden"):
        record_from_payloads(config, _summary(), _checkpoint(), config_path="cfg.json")
