#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import stat
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Dict


@dataclass(frozen=True)
class RehydratedBackbone:
    canonical_key: str
    artifact_id: int
    run_dir: Path
    receipt: Dict[str, Any]
    config: Dict[str, Any]
    summary: Dict[str, Any]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _find_backbone(matrix: Dict[str, Any], canonical_key: str) -> Dict[str, Any]:
    rows = [x for x in matrix.get("backbones", []) if x.get("canonical_key") == canonical_key]
    if len(rows) != 1:
        raise ValueError(f"canonical_key must resolve exactly once: {canonical_key!r}")
    row = rows[0]
    if row.get("status") != "COMPLETE":
        raise ValueError(f"canonical backbone is not COMPLETE: {canonical_key}")
    return row


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


def rehydrate_canonical_backbone(
    *,
    matrix_path: Path,
    canonical_key: str,
    artifact_id: int,
    artifact_zip: Path,
    destination: Path,
) -> RehydratedBackbone:
    matrix = _load_json(matrix_path)
    if matrix.get("schema") != "padataset.l2o-canonical-backbone-matrix.v1":
        raise ValueError("unsupported canonical matrix schema")

    row = _find_backbone(matrix, canonical_key)
    expected_artifact_id = int(row["artifact_id"])
    if int(artifact_id) != expected_artifact_id:
        raise ValueError(
            f"artifact ID mismatch: manifest={expected_artifact_id}, supplied={artifact_id}"
        )

    if destination.exists() and any(destination.iterdir()):
        raise ValueError(f"rehydration destination must be empty: {destination}")
    _safe_extract(artifact_zip, destination)

    result_root = destination / "scientific-results"
    receipt_path = result_root / "scientific-receipt.json"
    if not receipt_path.is_file():
        raise ValueError("scientific execution receipt missing")

    receipt = _load_json(receipt_path)
    if receipt.get("schema") != "padataset.scientific-execution-receipt.v1":
        raise ValueError("scientific receipt schema mismatch")
    if receipt.get("decision") != "PASS":
        raise ValueError("scientific receipt decision is not PASS")
    if receipt.get("operation") != "train_backbone":
        raise ValueError("artifact is not a train_backbone result")
    if receipt.get("dataset_profile") != matrix.get("dataset_profile"):
        raise ValueError("dataset profile mismatch")
    if receipt.get("candidate_sha") != row.get("candidate_sha"):
        raise ValueError("candidate SHA mismatch")

    run_name = Path(row["canonical_w4_config"]).stem
    run_dir = result_root / "backbone" / run_name
    config_path = run_dir / "config.json"
    best_model_path = run_dir / "best_model.pt"
    summary_path = run_dir / "summary.json"
    for p in (config_path, best_model_path, summary_path):
        if not p.is_file():
            raise ValueError(f"required backbone artifact missing: {p.name}")

    receipt_files = {
        x["path"]: x
        for x in receipt.get("files", [])
        if isinstance(x, dict) and "path" in x
    }
    rel_prefix = f"backbone/{run_name}"
    expected = {
        f"{rel_prefix}/best_model.pt": row["best_model_sha256"],
        f"{rel_prefix}/config.json": row["config_sha256"],
    }
    actual_paths = {
        f"{rel_prefix}/best_model.pt": best_model_path,
        f"{rel_prefix}/config.json": config_path,
    }

    for rel, expected_sha in expected.items():
        receipt_entry = receipt_files.get(rel)
        if receipt_entry is None:
            raise ValueError(f"receipt missing required file: {rel}")
        if receipt_entry.get("sha256") != expected_sha:
            raise ValueError(f"receipt/manifest SHA mismatch for {rel}")
        actual_sha = _sha256(actual_paths[rel])
        if actual_sha != expected_sha:
            raise ValueError(f"rehydrated file SHA mismatch for {rel}")

    cfg = _load_json(config_path)
    summary = _load_json(summary_path)
    training = row.get("training_direction") or {}
    known = list(row.get("known_pas") or [])

    if cfg.get("run_name") != run_name:
        raise ValueError("run_name provenance mismatch")
    if cfg.get("target_unknown_pa") != training.get("target"):
        raise ValueError("training target provenance mismatch")
    if cfg.get("surrogate_open_pa") != training.get("surrogate"):
        raise ValueError("training surrogate provenance mismatch")
    if list(cfg.get("known_pas_l2o") or []) != known:
        raise ValueError("known PA provenance mismatch")
    if cfg.get("unknown_pas") != [training.get("target")]:
        raise ValueError("unknown_pas provenance mismatch")
    if list(cfg.get("pas") or []) != known + [training.get("target")]:
        raise ValueError("PA ordering provenance mismatch")
    if cfg.get("split_mode") != "open_pa":
        raise ValueError("split_mode provenance mismatch")
    if cfg.get("early_stopping_mode") != "known_only":
        raise ValueError("checkpoint selection is not known-only")
    if cfg.get("quarantine_target_until_test") is not True:
        raise ValueError("target quarantine was not enabled")
    if float(cfg.get("open_val_frac", -1)) != 0.0:
        raise ValueError("target-open validation was not disabled")
    if int(cfg.get("seed", -1)) != int(matrix.get("seed", -2)):
        raise ValueError("seed provenance mismatch")
    if int(cfg.get("cache_len", -1)) != int(matrix.get("cache_len", -2)):
        raise ValueError("cache length provenance mismatch")

    if summary.get("target_test_consumed") is not False:
        raise ValueError("target test was consumed before frozen evaluation")
    if summary.get("target_quarantine_status") != "PRESERVED_FOR_FINAL_FROZEN_EVALUATOR":
        raise ValueError("target quarantine status mismatch")
    if list(summary.get("class_names") or []) != known:
        raise ValueError("summary class ordering mismatch")
    if summary.get("unknown_pas") != [training.get("target")]:
        raise ValueError("summary target provenance mismatch")

    return RehydratedBackbone(
        canonical_key=canonical_key,
        artifact_id=int(artifact_id),
        run_dir=run_dir,
        receipt=receipt,
        config=cfg,
        summary=summary,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix", required=True)
    ap.add_argument("--canonical-key", required=True)
    ap.add_argument("--artifact-id", required=True, type=int)
    ap.add_argument("--artifact-zip", required=True)
    ap.add_argument("--destination", required=True)
    args = ap.parse_args()

    result = rehydrate_canonical_backbone(
        matrix_path=Path(args.matrix),
        canonical_key=args.canonical_key,
        artifact_id=args.artifact_id,
        artifact_zip=Path(args.artifact_zip),
        destination=Path(args.destination),
    )
    print(json.dumps({
        "canonical_key": result.canonical_key,
        "artifact_id": result.artifact_id,
        "run_dir": str(result.run_dir),
        "candidate_sha": result.receipt["candidate_sha"],
        "dataset_profile": result.receipt["dataset_profile"],
        "target_test_consumed": result.summary["target_test_consumed"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
