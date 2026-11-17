from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from experiments.archb_artifact_rehydrate import _safe_extract
from experiments.archb_artifact_transport_contract import (
    validate_archb_artifact_transport,
)
from experiments.archb_eval_request_contract import resolve_archb_eval_request


REQUEST = Path(
    "manifests/configs/archb_cross_surrogate_v1/PA2_B0_softmax3.json"
)
B1_REQUEST = Path(
    "manifests/configs/archb_cross_surrogate_v1/PA2_B1_expanded5.json"
)


def _request(tmp_path: Path) -> dict:
    return json.loads(REQUEST.read_text(encoding="utf-8"))


def test_b0_request_resolves_exact_frozen_evaluator_args(tmp_path):
    out = resolve_archb_eval_request(
        request_path=REQUEST,
        run_dir=tmp_path / "run",
        out_dir=tmp_path / "out",
    )
    assert out.artifact_id == 14180249360
    assert out.workflow_run_id == 43751609944
    assert out.target_pa == "PA2"
    assert out.state_mode == "softmax3"
    args = list(out.evaluator_args)
    assert args[args.index("--checkpoint") + 1] == "best_model"
    assert args[args.index("--partition-seed") + 1] == "1701"
    assert args[args.index("--dqn-episodes") + 1] == "30"
    assert args[args.index("--known-budget") + 1] == "0.05"
    assert args[args.index("--state-mode") + 1] == "softmax3"
    assert "--mix-true-open" not in args


def test_b0_request_rejects_target_tuning_drift(tmp_path):
    data = _request(tmp_path)
    data["target_labels_used_for_candidate_selection"] = True
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="candidate_selection"):
        resolve_archb_eval_request(
            request_path=path,
            run_dir=tmp_path / "run",
            out_dir=tmp_path / "out",
        )


def test_b0_transport_accepts_only_exact_artifact_metadata(tmp_path):
    req = _request(tmp_path)
    src = req["source_backbone"]
    metadata = {
        "id": src["artifact_id"],
        "digest": src["artifact_digest"],
        "name": src["artifact_name"],
        "expired": False,
        "workflow_run": {"id": src["workflow_run_id"]},
    }
    path = tmp_path / "artifact.json"
    path.write_text(json.dumps(metadata), encoding="utf-8")
    out = validate_archb_artifact_transport(
        request_path=REQUEST,
        artifact_metadata_path=path,
    )
    assert out["artifact_id"] == 14180249360
    assert out["workflow_run_id"] == 43751609944


def test_b0_transport_rejects_digest_drift(tmp_path):
    req = _request(tmp_path)
    src = req["source_backbone"]
    metadata = {
        "id": src["artifact_id"],
        "digest": "sha256:" + "0" * 64,
        "name": src["artifact_name"],
        "expired": False,
        "workflow_run": {"id": src["workflow_run_id"]},
    }
    path = tmp_path / "artifact.json"
    path.write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(ValueError, match="digest"):
        validate_archb_artifact_transport(
            request_path=REQUEST,
            artifact_metadata_path=path,
        )


def test_b0_rehydration_rejects_zip_path_traversal(tmp_path):
    archive = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("../escape.txt", "nope")
    with pytest.raises(ValueError, match="unsafe ZIP member"):
        _safe_extract(archive, tmp_path / "out")


def test_b1_request_resolves_exact_predeclared_expanded5_args(tmp_path):
    out = resolve_archb_eval_request(
        request_path=B1_REQUEST,
        run_dir=tmp_path / "run",
        out_dir=tmp_path / "out",
    )
    assert out.artifact_id == 14180249360
    assert out.workflow_run_id == 43751609944
    assert out.target_pa == "PA2"
    assert out.state_mode == "expanded5"
    args = list(out.evaluator_args)
    assert args[args.index("--checkpoint") + 1] == "best_model"
    assert args[args.index("--partition-seed") + 1] == "1701"
    assert args[args.index("--dqn-episodes") + 1] == "30"
    assert args[args.index("--known-budget") + 1] == "0.05"
    assert args[args.index("--state-mode") + 1] == "expanded5"


def test_b1_request_rejects_b0_target_metric_parameterization(tmp_path):
    data = json.loads(B1_REQUEST.read_text(encoding="utf-8"))
    data["b0_target_metrics_used_for_b1_parameters"] = True
    path = tmp_path / "bad-b1.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="B0 target metrics"):
        resolve_archb_eval_request(
            request_path=path,
            run_dir=tmp_path / "run",
            out_dir=tmp_path / "out",
        )


def test_b1_request_rejects_state_mode_drift(tmp_path):
    data = json.loads(B1_REQUEST.read_text(encoding="utf-8"))
    data["state_mode"] = "softmax3"
    path = tmp_path / "bad-b1-state.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="B1 state mode drift"):
        resolve_archb_eval_request(
            request_path=path,
            run_dir=tmp_path / "run",
            out_dir=tmp_path / "out",
        )
