from __future__ import annotations

import itertools
import json
from pathlib import Path

import pytest

from experiments.l2o_canonical_matrix_validate import PA_NAMES, validate_canonical_matrix


def _fixture(tmp_path: Path):
    request_root = tmp_path / "requests"
    request_root.mkdir()
    rows = []
    complete_keys = {"PA1-PA2", "PA1-PA3"}

    for a, b in itertools.combinations(PA_NAMES, 2):
        key = f"{a}-{b}"
        known = [pa for pa in PA_NAMES if pa not in (a, b)]
        row = {
            "canonical_pair": [a, b],
            "canonical_key": key,
            "known_pas": known,
            "directed_cells": [
                {"evaluation_target": a, "evaluation_surrogate": b},
                {"evaluation_target": b, "evaluation_surrogate": a},
            ],
            "status": "PENDING_BACKBONE",
        }
        if key in complete_keys:
            row.update({
                "status": "COMPLETE",
                "training_direction": {"target": a, "surrogate": b},
                "workflow_run_id": 1,
                "workflow_job_id": 2,
                "artifact_id": 3,
                "artifact_digest": "sha256:" + "a" * 64,
                "candidate_sha": "b" * 40,
                "best_model_sha256": "c" * 64,
                "config_sha256": "d" * 64,
                "target_test_consumed": False,
            })
            for target, surrogate in ((a, b), (b, a)):
                p = request_root / f"{key}__target{target}__sur{surrogate}.json"
                p.write_text(json.dumps({
                    "schema": "padataset.l2o-directional-eval-request.v1",
                    "canonical_key": key,
                    "artifact_id": 3,
                    "artifact_digest": "sha256:" + "a" * 64,
                    "evaluation_target": target,
                    "evaluation_surrogate": surrogate,
                    "target_labels_used_for_tuning": False,
                }), encoding="utf-8")
        rows.append(row)

    matrix = {
        "schema": "padataset.l2o-canonical-backbone-matrix.v1",
        "canonical_backbone_count": 10,
        "directed_cell_count": 20,
        "completed_backbone_count": 2,
        "remaining_backbone_count": 8,
        "backbones": rows,
    }
    matrix_path = tmp_path / "matrix.json"
    matrix_path.write_text(json.dumps(matrix), encoding="utf-8")
    return matrix_path, request_root


def test_accepts_complete_canonical_matrix_and_requests(tmp_path):
    matrix, requests = _fixture(tmp_path)
    result = validate_canonical_matrix(matrix_path=matrix, request_root=requests)
    assert result == {
        "canonical_backbones": 10,
        "directed_cells": 20,
        "complete": 2,
        "remaining": 8,
    }


def test_rejects_missing_reverse_request(tmp_path):
    matrix, requests = _fixture(tmp_path)
    (requests / "PA1-PA2__targetPA2__surPA1.json").unlink()
    with pytest.raises(ValueError, match="missing frozen directional request"):
        validate_canonical_matrix(matrix_path=matrix, request_root=requests)


def test_rejects_known_complement_drift(tmp_path):
    matrix, requests = _fixture(tmp_path)
    payload = json.loads(matrix.read_text())
    payload["backbones"][0]["known_pas"] = ["PA3", "PA8", "PA4"]
    matrix.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="known_pas complement/order mismatch"):
        validate_canonical_matrix(matrix_path=matrix, request_root=requests)


def test_rejects_count_drift(tmp_path):
    matrix, requests = _fixture(tmp_path)
    payload = json.loads(matrix.read_text())
    payload["completed_backbone_count"] = 3
    matrix.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="completed_backbone_count drift"):
        validate_canonical_matrix(matrix_path=matrix, request_root=requests)
