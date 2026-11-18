from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.l2o_hpo_eval_overlay import build_hpo_eval_overlay


def _matrix():
    return {
        "schema": "padataset.l2o-canonical-backbone-matrix.v1",
        "dataset_profile": "ota_core_high_run01_len16384_v1",
        "seed": 0,
        "cache_len": 16384,
        "backbones": [{
            "canonical_key": "PA2-PA3",
            "canonical_pair": ["PA2", "PA3"],
            "known_pas": ["PA1", "PA4", "PA8"],
            "status": "COMPLETE",
            "canonical_w4_config": "old.json",
            "directed_cells": [
                {"evaluation_target": "PA2", "evaluation_surrogate": "PA3"},
                {"evaluation_target": "PA3", "evaluation_surrogate": "PA2"},
            ],
        }],
    }


def _artifact(tmp_path: Path, *, target_consumed=False, stage="finalist"):
    root = tmp_path
    run_name = "l2o_hpo_v2_PA2_PA3_t004_finalist"
    run_dir = root / "scientific-results" / "backbone" / run_name
    run_dir.mkdir(parents=True)
    cfg = {
        "run_name": run_name,
        "target_unknown_pa": "PA2",
        "surrogate_open_pa": "PA3",
        "known_pas_l2o": ["PA1", "PA4", "PA8"],
        "open_val_frac": 0,
        "early_stopping_mode": "known_only",
        "quarantine_target_until_test": True,
        "hpo_trial": {
            "schema": "padataset.l2o-hpo-trial.v2",
            "trial_id": "PA2-PA3__t004",
            "canonical_pair": "PA2-PA3",
            "stage": stage,
            "selection_evidence": "known_validation_only",
            "target_metrics_allowed_for_selection": False,
            "test_metrics_allowed_for_selection": False,
        },
    }
    (run_dir / "config.json").write_text(json.dumps(cfg))
    (run_dir / "best_model.pt").write_bytes(b"best-model")
    (run_dir / "summary.json").write_text(json.dumps({
        "best_epoch": 17,
        "best_val_macro_f1": 0.97,
        "target_test_consumed": target_consumed,
        "target_quarantine_status": "PRESERVED_FOR_FINAL_FROZEN_EVALUATOR",
    }))
    receipt_root = root / "scientific-results"
    (receipt_root / "scientific-receipt.json").write_text(json.dumps({
        "schema": "padataset.scientific-execution-receipt.v1",
        "decision": "PASS",
        "operation": "train_backbone",
        "candidate_sha": "a" * 40,
    }))
    return run_name


def test_builds_two_requests_and_rebinds_only_selected_pair(tmp_path):
    run_name = _artifact(tmp_path)
    config_path = f"manifests/configs/l2o_hpo_pilot_v2/{run_name}.json"
    matrix, requests = build_hpo_eval_overlay(
        base_matrix=_matrix(),
        canonical_key="PA2-PA3",
        finalist_config_path=config_path,
        artifact_id=123,
        artifact_digest="sha256:" + "b" * 64,
        workflow_run_id=456,
        workflow_job_id=789,
        candidate_sha="a" * 40,
        artifact_root=tmp_path,
    )
    row = matrix["backbones"][0]
    assert row["artifact_id"] == 123
    assert row["canonical_w4_config"] == config_path
    assert row["hpo_selection_evidence"] == "known_validation_only"
    assert len(requests) == 2
    assert {(r["evaluation_target"], r["evaluation_surrogate"]) for r in requests} == {
        ("PA2", "PA3"), ("PA3", "PA2")
    }
    assert all(r["target_labels_used_for_tuning"] is False for r in requests)


def test_rejects_nonfinalist(tmp_path):
    run_name = _artifact(tmp_path, stage="refine")
    with pytest.raises(ValueError, match="only finalist"):
        build_hpo_eval_overlay(
            base_matrix=_matrix(),
            canonical_key="PA2-PA3",
            finalist_config_path=f"manifests/configs/{run_name}.json",
            artifact_id=1,
            artifact_digest="sha256:" + "b" * 64,
            workflow_run_id=2,
            workflow_job_id=3,
            candidate_sha="a" * 40,
            artifact_root=tmp_path,
        )


def test_rejects_target_consumed_before_freeze(tmp_path):
    run_name = _artifact(tmp_path, target_consumed=True)
    with pytest.raises(ValueError, match="target test consumed"):
        build_hpo_eval_overlay(
            base_matrix=_matrix(),
            canonical_key="PA2-PA3",
            finalist_config_path=f"manifests/configs/{run_name}.json",
            artifact_id=1,
            artifact_digest="sha256:" + "b" * 64,
            workflow_run_id=2,
            workflow_job_id=3,
            candidate_sha="a" * 40,
            artifact_root=tmp_path,
        )
