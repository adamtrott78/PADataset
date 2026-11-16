from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.l2o_artifact_transport_contract import validate_artifact_transport


def _paths(tmp_path: Path, *, artifact_id=123, digest="sha256:abc", expired=False, workflow_run_id=456):
    request = {
        "schema": "padataset.l2o-directional-eval-request.v1",
        "canonical_key": "PA1-PA8",
        "artifact_id": 123,
        "artifact_digest": "sha256:abc",
    }
    matrix = {
        "schema": "padataset.l2o-canonical-backbone-matrix.v1",
        "backbones": [{
            "canonical_key": "PA1-PA8",
            "status": "COMPLETE",
            "artifact_id": 123,
            "artifact_digest": "sha256:abc",
            "workflow_run_id": 456,
        }],
    }
    artifact = {
        "id": artifact_id,
        "name": "padataset-scientific-123",
        "digest": digest,
        "expired": expired,
        "workflow_run": {"id": workflow_run_id},
    }
    out = {}
    for name, payload in [("request", request), ("matrix", matrix), ("artifact", artifact)]:
        p = tmp_path / f"{name}.json"
        p.write_text(json.dumps(payload), encoding="utf-8")
        out[name] = p
    return out


def _validate(paths):
    return validate_artifact_transport(
        request_path=paths["request"],
        matrix_path=paths["matrix"],
        artifact_metadata_path=paths["artifact"],
    )


def test_accepts_exact_github_artifact_binding(tmp_path):
    b = _validate(_paths(tmp_path))
    assert b.artifact_id == 123
    assert b.artifact_digest == "sha256:abc"
    assert b.workflow_run_id == 456


def test_rejects_github_artifact_id_drift(tmp_path):
    with pytest.raises(ValueError, match="artifact ID mismatch"):
        _validate(_paths(tmp_path, artifact_id=999))


def test_rejects_github_artifact_digest_drift(tmp_path):
    with pytest.raises(ValueError, match="artifact digest mismatch"):
        _validate(_paths(tmp_path, digest="sha256:wrong"))


def test_rejects_expired_artifact(tmp_path):
    with pytest.raises(ValueError, match="expired"):
        _validate(_paths(tmp_path, expired=True))


def test_rejects_wrong_workflow_run(tmp_path):
    with pytest.raises(ValueError, match="workflow run mismatch"):
        _validate(_paths(tmp_path, workflow_run_id=999))
