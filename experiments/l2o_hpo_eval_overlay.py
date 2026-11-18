#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _safe_extract(zip_path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            p = PurePosixPath(info.filename)
            if p.is_absolute() or ".." in p.parts:
                raise ValueError(f"unsafe ZIP member path: {info.filename!r}")
            mode = (info.external_attr >> 16) & 0xFFFF
            if stat.S_ISLNK(mode):
                raise ValueError(f"ZIP symlink rejected: {info.filename!r}")
        zf.extractall(destination)


def build_hpo_eval_overlay(
    *,
    base_matrix: dict[str, Any],
    canonical_key: str,
    finalist_config_path: str,
    artifact_id: int,
    artifact_digest: str,
    workflow_run_id: int,
    workflow_job_id: int,
    candidate_sha: str,
    artifact_root: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if base_matrix.get("schema") != "padataset.l2o-canonical-backbone-matrix.v1":
        raise ValueError("unsupported canonical matrix schema")
    rows = [r for r in base_matrix.get("backbones", []) if r.get("canonical_key") == canonical_key]
    if len(rows) != 1:
        raise ValueError("canonical key must resolve exactly once")
    row = rows[0]

    run_name = Path(finalist_config_path).stem
    run_dir = artifact_root / "scientific-results" / "backbone" / run_name
    receipt_path = artifact_root / "scientific-results" / "scientific-receipt.json"
    config_path = run_dir / "config.json"
    best_model_path = run_dir / "best_model.pt"
    summary_path = run_dir / "summary.json"
    for p in (receipt_path, config_path, best_model_path, summary_path):
        if not p.is_file():
            raise ValueError(f"required finalist artifact file missing: {p}")

    receipt = _load(receipt_path)
    cfg = _load(config_path)
    summary = _load(summary_path)
    meta = cfg.get("hpo_trial") or {}

    if receipt.get("schema") != "padataset.scientific-execution-receipt.v1":
        raise ValueError("scientific receipt schema mismatch")
    if receipt.get("decision") != "PASS" or receipt.get("operation") != "train_backbone":
        raise ValueError("finalist artifact is not a PASS train_backbone result")
    if receipt.get("candidate_sha") != candidate_sha:
        raise ValueError("candidate SHA mismatch")
    if meta.get("schema") != "padataset.l2o-hpo-trial.v2":
        raise ValueError("finalist config lacks HPO metadata")
    if meta.get("stage") != "finalist":
        raise ValueError("only finalist HPO artifacts may enter directional evaluation")
    if meta.get("canonical_pair") != canonical_key:
        raise ValueError("HPO finalist canonical pair mismatch")
    if meta.get("selection_evidence") != "known_validation_only":
        raise ValueError("HPO finalist was not selected from known validation only")
    if meta.get("target_metrics_allowed_for_selection") is not False:
        raise ValueError("HPO finalist permits target metrics for selection")
    if meta.get("test_metrics_allowed_for_selection") is not False:
        raise ValueError("HPO finalist permits test metrics for selection")
    if summary.get("target_test_consumed") is not False:
        raise ValueError("target test consumed before finalist freeze")

    target = cfg.get("target_unknown_pa")
    surrogate = cfg.get("surrogate_open_pa")
    if set((target, surrogate)) != set(row.get("canonical_pair") or []):
        raise ValueError("finalist target/surrogate topology differs from canonical pair")
    if list(cfg.get("known_pas_l2o") or []) != list(row.get("known_pas") or []):
        raise ValueError("finalist known PA topology differs from canonical matrix")
    if cfg.get("open_val_frac") != 0 or cfg.get("early_stopping_mode") != "known_only":
        raise ValueError("finalist target quarantine / checkpoint selection drift")
    if cfg.get("quarantine_target_until_test") is not True:
        raise ValueError("finalist target quarantine disabled")

    new_matrix = copy.deepcopy(base_matrix)
    new_row = next(r for r in new_matrix["backbones"] if r["canonical_key"] == canonical_key)
    new_row.update({
        "status": "COMPLETE",
        "canonical_w4_config": finalist_config_path,
        "training_direction": {"target": target, "surrogate": surrogate},
        "workflow_run_id": int(workflow_run_id),
        "workflow_job_id": int(workflow_job_id),
        "artifact_id": int(artifact_id),
        "artifact_digest": artifact_digest,
        "candidate_sha": candidate_sha,
        "best_model_sha256": _sha256(best_model_path),
        "config_sha256": _sha256(config_path),
        "best_epoch": int(summary["best_epoch"]),
        "best_val_macro_f1": float(summary["best_val_macro_f1"]),
        "target_test_consumed": False,
        "target_quarantine_status": summary.get("target_quarantine_status"),
        "hpo_finalist_trial_id": meta.get("trial_id"),
        "hpo_selection_evidence": "known_validation_only",
    })

    requests = []
    for cell in new_row["directed_cells"]:
        eval_target = str(cell["evaluation_target"])
        eval_surrogate = str(cell["evaluation_surrogate"])
        requests.append({
            "schema": "padataset.l2o-directional-eval-request.v1",
            "policy_id": "l2o_dqnguard_track_a_frozen_v1",
            "canonical_matrix": "manifests/l2o_canonical_backbone_matrix_v1.json",
            "evaluation_policy": "manifests/l2o_directional_eval_policy_v1.json",
            "canonical_key": canonical_key,
            "artifact_id": int(artifact_id),
            "artifact_digest": artifact_digest,
            "evaluation_target": eval_target,
            "evaluation_surrogate": eval_surrogate,
            "checkpoint": "best_model",
            "target_labels_used_for_tuning": False,
            "status": "READY_FOR_BOUNDED_EVALUATOR",
        })
    return new_matrix, requests


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-matrix", required=True)
    ap.add_argument("--canonical-key", required=True)
    ap.add_argument("--finalist-config-path", required=True)
    ap.add_argument("--artifact-id", required=True, type=int)
    ap.add_argument("--artifact-digest", required=True)
    ap.add_argument("--workflow-run-id", required=True, type=int)
    ap.add_argument("--workflow-job-id", required=True, type=int)
    ap.add_argument("--candidate-sha", required=True)
    ap.add_argument("--artifact-zip", required=True)
    ap.add_argument("--out-matrix", required=True)
    ap.add_argument("--out-request-root", required=True)
    args = ap.parse_args()

    with tempfile.TemporaryDirectory(prefix="l2o-hpo-eval-overlay-") as td:
        root = Path(td)
        _safe_extract(Path(args.artifact_zip), root)
        matrix, requests = build_hpo_eval_overlay(
            base_matrix=_load(Path(args.base_matrix)),
            canonical_key=args.canonical_key,
            finalist_config_path=args.finalist_config_path,
            artifact_id=args.artifact_id,
            artifact_digest=args.artifact_digest,
            workflow_run_id=args.workflow_run_id,
            workflow_job_id=args.workflow_job_id,
            candidate_sha=args.candidate_sha,
            artifact_root=root,
        )

    out_matrix = Path(args.out_matrix)
    out_matrix.parent.mkdir(parents=True, exist_ok=True)
    out_matrix.write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    request_root = Path(args.out_request_root)
    request_root.mkdir(parents=True, exist_ok=True)
    for request in requests:
        name = (
            f"{request['canonical_key']}__target{request['evaluation_target']}"
            f"__sur{request['evaluation_surrogate']}.json"
        )
        (request_root / name).write_text(json.dumps(request, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "canonical_key": args.canonical_key,
        "artifact_id": args.artifact_id,
        "requests": len(requests),
        "out_matrix": str(out_matrix),
        "out_request_root": str(request_root),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
