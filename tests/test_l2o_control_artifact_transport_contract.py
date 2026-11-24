from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.l2o_control_artifact_transport_contract import validate_control_artifact_transport


def _write(tmp_path: Path, *, artifact_id=123, digest="sha256:abc", expired=False):
    matrix = {
        "schema": "padataset.l2o-canonical-backbone-matrix.v1",
        "backbones": [{
            "canonical_key": "PA1-PA2",
            "status": "COMPLETE",
            "artifact_id": 123,
            "artifact_digest": "sha256:abc",
            "workflow_run_id": 456,
        }],
    }
    request = {
        "schema": "padataset.l2o-control-eval-request.v1",
        "canonical_key": "PA1-PA2",
        "artifact_id": artifact_id,
        "artifact_digest": digest,
    }
    artifact = {
        "id": 123,
        "digest": "sha256:abc",
        "expired": expired,
        "name": "padataset-scientific-456",
        "workflow_run": {"id": 456},
    }
    paths = {}
    for name, payload in [("matrix", matrix), ("request", request), ("artifact", artifact)]:
        p = tmp_path / f"{name}.json"
        p.write_text(json.dumps(payload), encoding="utf-8")
        paths[name] = p
    return paths


def _validate(paths):
    return validate_control_artifact_transport(
        request_path=paths["request"],
        matrix_path=paths["matrix"],
        artifact_metadata_path=paths["artifact"],
    )


def test_control_transport_binds_exact_frozen_artifact(tmp_path):
    b = _validate(_write(tmp_path))
    assert b.canonical_key == "PA1-PA2"
    assert b.artifact_id == 123
    assert b.workflow_run_id == 456


def test_control_transport_rejects_request_drift(tmp_path):
    with pytest.raises(ValueError, match="request artifact ID"):
        _validate(_write(tmp_path, artifact_id=999))


def test_control_transport_rejects_expired_artifact(tmp_path):
    with pytest.raises(ValueError, match="expired"):
        _validate(_write(tmp_path, expired=True))
