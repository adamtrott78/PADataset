from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.l2o_eval_request_contract import resolve_directional_eval_request


def _write(tmp_path: Path, *, target="PA1", surrogate="PA8", artifact_id=123, digest="sha256:abc", mix_true_open=False):
    matrix = {
        "schema": "padataset.l2o-canonical-backbone-matrix.v1",
        "backbones": [{
            "canonical_key": "PA1-PA8",
            "canonical_pair": ["PA1", "PA8"],
            "status": "COMPLETE",
            "artifact_id": 123,
            "artifact_digest": "sha256:abc",
            "directed_cells": [
                {"evaluation_target": "PA1", "evaluation_surrogate": "PA8"},
                {"evaluation_target": "PA8", "evaluation_surrogate": "PA1"},
            ],
        }],
    }
    policy = {
        "schema": "padataset.l2o-directional-eval-policy.v1",
        "policy_id": "l2o_dqnguard_track_a_frozen_v1",
        "checkpoint": "best_model",
        "band_accept_mode": "var_energy",
        "decision_mode": "score_threshold",
        "max_known_reject_cal": 0.05,
        "known_cap": 625,
        "open_cap": 625,
        "mix_true_open": mix_true_open,
        "dqn_state_mode": "softmax3",
        "evaluator_device": "cuda",
        "batch_size": 128,
        "num_workers": 0,
        "target_labels_used_for_tuning": False,
    }
    request = {
        "schema": "padataset.l2o-directional-eval-request.v1",
        "policy_id": "l2o_dqnguard_track_a_frozen_v1",
        "canonical_matrix": "manifests/l2o_canonical_backbone_matrix_v1.json",
        "evaluation_policy": "manifests/l2o_directional_eval_policy_v1.json",
        "canonical_key": "PA1-PA8",
        "artifact_id": artifact_id,
        "artifact_digest": digest,
        "evaluation_target": target,
        "evaluation_surrogate": surrogate,
        "checkpoint": "best_model",
        "target_labels_used_for_tuning": False,
        "status": "READY_FOR_BOUNDED_EVALUATOR",
    }
    paths = {}
    for name, payload in [("matrix", matrix), ("policy", policy), ("request", request)]:
        p = tmp_path / f"{name}.json"
        p.write_text(json.dumps(payload), encoding="utf-8")
        paths[name] = p
    return paths


def _resolve(tmp_path: Path, paths):
    return resolve_directional_eval_request(
        request_path=paths["request"],
        matrix_path=paths["matrix"],
        policy_path=paths["policy"],
        run_dir=tmp_path / "run",
        out_dir=tmp_path / "out",
    )


def test_resolves_frozen_surrogate_only_direction(tmp_path):
    r = _resolve(tmp_path, _write(tmp_path))
    assert r.canonical_key == "PA1-PA8"
    assert r.evaluation_target == "PA1"
    assert r.evaluation_surrogate == "PA8"
    assert "--mix-true-open" not in r.evaluator_args
    assert list(r.evaluator_args)[list(r.evaluator_args).index("--max-known-reject-cal") + 1] == "0.05"


def test_allows_reverse_declared_direction(tmp_path):
    r = _resolve(tmp_path, _write(tmp_path, target="PA8", surrogate="PA1"))
    assert r.evaluation_target == "PA8"
    assert r.evaluation_surrogate == "PA1"


def test_rejects_artifact_identity_drift(tmp_path):
    paths = _write(tmp_path, artifact_id=999)
    with pytest.raises(ValueError, match="artifact ID mismatch"):
        _resolve(tmp_path, paths)


def test_rejects_direction_outside_canonical_pair(tmp_path):
    paths = _write(tmp_path, target="PA1", surrogate="PA4")
    with pytest.raises(ValueError, match="canonical excluded pair"):
        _resolve(tmp_path, paths)


def test_rejects_true_target_mixing_policy(tmp_path):
    paths = _write(tmp_path, mix_true_open=True)
    with pytest.raises(ValueError, match="surrogate-only"):
        _resolve(tmp_path, paths)
