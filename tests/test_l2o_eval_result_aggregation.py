from __future__ import annotations

import itertools
import json
from pathlib import Path

import pandas as pd
import pytest

from experiments.l2o_eval_result_record import build_result_record
from experiments.l2o_eval_matrix_aggregate import aggregate_directional_results


PAS = ("PA1", "PA2", "PA3", "PA4", "PA8")


def _policy():
    return {
        "schema": "padataset.l2o-directional-eval-policy.v1",
        "policy_id": "l2o_dqnguard_track_a_frozen_v1",
        "checkpoint": "best_model",
        "band_accept_mode": "var_energy",
        "decision_mode": "score_threshold",
        "max_known_reject_cal": 0.05,
        "mix_true_open": False,
        "target_labels_used_for_tuning": False,
    }


def _matrix():
    rows = []
    aid = 100
    for a, b in itertools.combinations(PAS, 2):
        key = f"{a}-{b}"
        known = [x for x in PAS if x not in (a, b)]
        rows.append({
            "canonical_key": key,
            "canonical_pair": [a, b],
            "known_pas": known,
            "status": "COMPLETE",
            "artifact_id": aid,
            "artifact_digest": "sha256:" + f"{aid:064x}"[-64:],
            "workflow_run_id": aid + 1000,
            "workflow_job_id": aid + 2000,
            "candidate_sha": "a" * 40,
            "best_model_sha256": "b" * 64,
            "config_sha256": "c" * 64,
            "directed_cells": [
                {"evaluation_target": a, "evaluation_surrogate": b},
                {"evaluation_target": b, "evaluation_surrogate": a},
            ],
        })
        aid += 1
    return {
        "schema": "padataset.l2o-canonical-backbone-matrix.v1",
        "completed_backbone_count": 10,
        "remaining_backbone_count": 0,
        "backbones": rows,
    }


def _write_json(path: Path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_result_record_binds_frozen_request_and_metrics(tmp_path):
    matrix = _matrix()
    policy = _policy()
    backbone = matrix["backbones"][0]
    target, surrogate = backbone["canonical_pair"]
    request = {
        "schema": "padataset.l2o-directional-eval-request.v1",
        "policy_id": policy["policy_id"],
        "canonical_key": backbone["canonical_key"],
        "artifact_id": backbone["artifact_id"],
        "artifact_digest": backbone["artifact_digest"],
        "evaluation_target": target,
        "evaluation_surrogate": surrogate,
        "checkpoint": "best_model",
        "target_labels_used_for_tuning": False,
    }
    csv = tmp_path / "summary.csv"
    pd.DataFrame([{
        "target_unknown_pas": json.dumps([target]),
        "surrogate_open_pa": surrogate,
        "backbone_canonical_excluded_pair": json.dumps(backbone["canonical_pair"]),
        "target_labels_used_for_tuning": False,
        "directional_reuse": False,
        "decision_mode": "score_threshold",
        "max_known_reject_cal": 0.05,
        "band_accept_mode": "var_energy",
        "known_reject_rate": 0.05,
        "unknown_precision": 0.8,
        "unknown_recall": 0.7,
        "unknown_f1": 0.746,
        "osr_acc": 0.9,
        "osr_macro_f1": 0.85,
        "unknown_auroc": 0.92,
        "score_threshold": 0.5,
        "threshold_known_reject_cal": 0.05,
        "threshold_open_recall_cal": 0.7,
    }]).to_csv(csv, index=False)

    out = build_result_record(
        request_path=_write_json(tmp_path / "request.json", request),
        matrix_path=_write_json(tmp_path / "matrix.json", matrix),
        policy_path=_write_json(tmp_path / "policy.json", policy),
        summary_csv=csv,
        output_path=tmp_path / "result.json",
    )
    assert out["schema"] == "padataset.l2o-directional-eval-result.v1"
    assert out["evaluation_target"] == target
    assert out["provenance"]["target_labels_used_for_tuning"] is False
    assert out["metrics"]["unknown_auroc"] == pytest.approx(0.92)


def _write_all_results(tmp_path: Path, *, tamper=None):
    matrix = _matrix()
    policy = _policy()
    root = tmp_path / "results"
    root.mkdir()
    idx = 0
    for backbone in matrix["backbones"]:
        for cell in backbone["directed_cells"]:
            target = cell["evaluation_target"]
            surrogate = cell["evaluation_surrogate"]
            record = {
                "schema": "padataset.l2o-directional-eval-result.v1",
                "status": "COMPLETE",
                "policy_id": policy["policy_id"],
                "canonical_key": backbone["canonical_key"],
                "canonical_pair": backbone["canonical_pair"],
                "known_pas": backbone["known_pas"],
                "evaluation_target": target,
                "evaluation_surrogate": surrogate,
                "directional_reuse": target != backbone["canonical_pair"][0],
                "artifact": {
                    "id": backbone["artifact_id"],
                    "digest": backbone["artifact_digest"],
                    "workflow_run_id": backbone["workflow_run_id"],
                    "workflow_job_id": backbone["workflow_job_id"],
                    "candidate_sha": backbone["candidate_sha"],
                    "best_model_sha256": backbone["best_model_sha256"],
                    "config_sha256": backbone["config_sha256"],
                },
                "checkpoint": "best_model",
                "provenance": {
                    "target_labels_used_for_tuning": False,
                    "mix_true_open": False,
                    "threshold_source": "known_only",
                    "surrogate_only_open_calibration": True,
                },
                "metrics": {
                    "known_reject_rate": 0.05,
                    "unknown_precision": 0.8,
                    "unknown_recall": 0.7,
                    "unknown_f1": 0.746,
                    "osr_acc": 0.9,
                    "osr_macro_f1": 0.85,
                    "unknown_auroc": 0.92,
                },
            }
            if tamper is not None and idx == 0:
                tamper(record)
            d = root / f"cell_{idx:02d}"
            d.mkdir()
            _write_json(d / "result_record.json", record)
            idx += 1
    return matrix, policy, root


def test_aggregator_requires_and_accepts_exact_20_cells(tmp_path):
    matrix, policy, root = _write_all_results(tmp_path)
    result = aggregate_directional_results(
        canonical_matrix_path=_write_json(tmp_path / "matrix.json", matrix),
        policy_path=_write_json(tmp_path / "policy.json", policy),
        results_root=root,
        output_json=tmp_path / "matrix_out.json",
        output_csv=tmp_path / "matrix_out.csv",
    )
    assert result["status"] == "COMPLETE"
    assert result["directed_cells"] == 20
    assert result["aggregate_metrics"]["mean_unknown_auroc"] == pytest.approx(0.92)


def test_aggregator_rejects_target_tuning(tmp_path):
    matrix, policy, root = _write_all_results(
        tmp_path,
        tamper=lambda r: r["provenance"].__setitem__("target_labels_used_for_tuning", True),
    )
    with pytest.raises(ValueError, match="target tuning detected"):
        aggregate_directional_results(
            canonical_matrix_path=_write_json(tmp_path / "matrix.json", matrix),
            policy_path=_write_json(tmp_path / "policy.json", policy),
            results_root=root,
            output_json=tmp_path / "matrix_out.json",
            output_csv=tmp_path / "matrix_out.csv",
        )


def test_aggregator_rejects_artifact_provenance_drift(tmp_path):
    matrix, policy, root = _write_all_results(
        tmp_path,
        tamper=lambda r: r["artifact"].__setitem__("digest", "sha256:" + "f" * 64),
    )
    with pytest.raises(ValueError, match="artifact provenance mismatch"):
        aggregate_directional_results(
            canonical_matrix_path=_write_json(tmp_path / "matrix.json", matrix),
            policy_path=_write_json(tmp_path / "policy.json", policy),
            results_root=root,
            output_json=tmp_path / "matrix_out.json",
            output_csv=tmp_path / "matrix_out.csv",
        )


def test_aggregator_rejects_missing_cell(tmp_path):
    matrix, policy, root = _write_all_results(tmp_path)
    next(root.rglob("result_record.json")).unlink()
    with pytest.raises(ValueError, match="expected exactly 20"):
        aggregate_directional_results(
            canonical_matrix_path=_write_json(tmp_path / "matrix.json", matrix),
            policy_path=_write_json(tmp_path / "policy.json", policy),
            results_root=root,
            output_json=tmp_path / "matrix_out.json",
            output_csv=tmp_path / "matrix_out.csv",
        )
