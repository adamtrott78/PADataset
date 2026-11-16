from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from experiments.l2o_artifact_rehydrate import rehydrate_canonical_backbone


RUN_NAME = "l2o_repair_ref_ent005_lr2e4_tgtPA1_surPA8_c16384_seed0_detv2_w4"
CANONICAL_KEY = "PA1-PA8"
ARTIFACT_ID = 12345
CANDIDATE_SHA = "d1fd5b6d414e7b88675485f576732a424504455f"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fixture(tmp_path: Path, *, candidate_sha=CANDIDATE_SHA, target_consumed=False, best_bytes=b"checkpoint"):
    config = {
        "run_name": RUN_NAME,
        "target_unknown_pa": "PA1",
        "surrogate_open_pa": "PA8",
        "known_pas_l2o": ["PA2", "PA3", "PA4"],
        "unknown_pas": ["PA1"],
        "pas": ["PA2", "PA3", "PA4", "PA1"],
        "split_mode": "open_pa",
        "early_stopping_mode": "known_only",
        "quarantine_target_until_test": True,
        "open_val_frac": 0,
        "seed": 0,
        "cache_len": 16384,
    }
    summary = {
        "target_test_consumed": bool(target_consumed),
        "target_quarantine_status": (
            "CONSUMED" if target_consumed else "PRESERVED_FOR_FINAL_FROZEN_EVALUATOR"
        ),
        "class_names": ["PA2", "PA3", "PA4"],
        "unknown_pas": ["PA1"],
    }
    config_bytes = (json.dumps(config, sort_keys=True) + "\n").encode()
    summary_bytes = (json.dumps(summary, sort_keys=True) + "\n").encode()

    best_sha = _sha(best_bytes)
    config_sha = _sha(config_bytes)
    prefix = f"backbone/{RUN_NAME}"
    receipt = {
        "schema": "padataset.scientific-execution-receipt.v1",
        "decision": "PASS",
        "operation": "train_backbone",
        "dataset_profile": "ota_core_high_run01_len16384_v1",
        "candidate_sha": candidate_sha,
        "files": [
            {"path": f"{prefix}/best_model.pt", "sha256": best_sha, "bytes": len(best_bytes)},
            {"path": f"{prefix}/config.json", "sha256": config_sha, "bytes": len(config_bytes)},
        ],
    }
    receipt_bytes = (json.dumps(receipt, sort_keys=True) + "\n").encode()

    matrix = {
        "schema": "padataset.l2o-canonical-backbone-matrix.v1",
        "dataset_profile": "ota_core_high_run01_len16384_v1",
        "seed": 0,
        "cache_len": 16384,
        "backbones": [{
            "canonical_key": CANONICAL_KEY,
            "status": "COMPLETE",
            "canonical_w4_config": f"manifests/configs/x/{RUN_NAME}.json",
            "artifact_id": ARTIFACT_ID,
            "candidate_sha": CANDIDATE_SHA,
            "best_model_sha256": best_sha,
            "config_sha256": config_sha,
            "training_direction": {"target": "PA1", "surrogate": "PA8"},
            "known_pas": ["PA2", "PA3", "PA4"],
        }],
    }
    matrix_path = tmp_path / "matrix.json"
    matrix_path.write_text(json.dumps(matrix), encoding="utf-8")

    zip_path = tmp_path / "artifact.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        base = f"scientific-results/backbone/{RUN_NAME}"
        zf.writestr(f"{base}/best_model.pt", best_bytes)
        zf.writestr(f"{base}/config.json", config_bytes)
        zf.writestr(f"{base}/summary.json", summary_bytes)
        zf.writestr("scientific-results/scientific-receipt.json", receipt_bytes)

    return matrix_path, zip_path


def test_rehydrates_exact_completed_backbone(tmp_path):
    matrix, artifact = _fixture(tmp_path)
    out = rehydrate_canonical_backbone(
        matrix_path=matrix,
        canonical_key=CANONICAL_KEY,
        artifact_id=ARTIFACT_ID,
        artifact_zip=artifact,
        destination=tmp_path / "out",
    )
    assert out.canonical_key == CANONICAL_KEY
    assert out.run_dir.name == RUN_NAME
    assert out.summary["target_test_consumed"] is False


def test_rejects_wrong_artifact_id(tmp_path):
    matrix, artifact = _fixture(tmp_path)
    with pytest.raises(ValueError, match="artifact ID mismatch"):
        rehydrate_canonical_backbone(
            matrix_path=matrix,
            canonical_key=CANONICAL_KEY,
            artifact_id=ARTIFACT_ID + 1,
            artifact_zip=artifact,
            destination=tmp_path / "out",
        )


def test_rejects_candidate_sha_drift(tmp_path):
    matrix, artifact = _fixture(tmp_path, candidate_sha="0" * 40)
    with pytest.raises(ValueError, match="candidate SHA mismatch"):
        rehydrate_canonical_backbone(
            matrix_path=matrix,
            canonical_key=CANONICAL_KEY,
            artifact_id=ARTIFACT_ID,
            artifact_zip=artifact,
            destination=tmp_path / "out",
        )


def test_rejects_checkpoint_hash_tamper(tmp_path):
    matrix, artifact = _fixture(tmp_path)
    rewritten = tmp_path / "tampered.zip"
    with zipfile.ZipFile(artifact) as src, zipfile.ZipFile(rewritten, "w") as dst:
        for info in src.infolist():
            data = src.read(info.filename)
            if info.filename.endswith("/best_model.pt"):
                data = b"tampered-checkpoint"
            dst.writestr(info, data)

    with pytest.raises(ValueError, match="rehydrated file SHA mismatch"):
        rehydrate_canonical_backbone(
            matrix_path=matrix,
            canonical_key=CANONICAL_KEY,
            artifact_id=ARTIFACT_ID,
            artifact_zip=rewritten,
            destination=tmp_path / "out",
        )


def test_rejects_preconsumed_target(tmp_path):
    matrix, artifact = _fixture(tmp_path, target_consumed=True)
    with pytest.raises(ValueError, match="target test was consumed"):
        rehydrate_canonical_backbone(
            matrix_path=matrix,
            canonical_key=CANONICAL_KEY,
            artifact_id=ARTIFACT_ID,
            artifact_zip=artifact,
            destination=tmp_path / "out",
        )


def test_rejects_zip_path_escape(tmp_path):
    matrix, _ = _fixture(tmp_path)
    artifact = tmp_path / "escape.zip"
    with zipfile.ZipFile(artifact, "w") as zf:
        zf.writestr("../escape", b"x")

    with pytest.raises(ValueError, match="unsafe ZIP member path"):
        rehydrate_canonical_backbone(
            matrix_path=matrix,
            canonical_key=CANONICAL_KEY,
            artifact_id=ARTIFACT_ID,
            artifact_zip=artifact,
            destination=tmp_path / "out",
        )
