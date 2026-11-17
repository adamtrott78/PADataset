#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import stat
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Dict


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _load(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def rehydrate_archb_backbone(
    *,
    request_path: Path,
    artifact_id: int,
    artifact_zip: Path,
    destination: Path,
) -> Dict[str, Any]:
    req = _load(request_path)
    if req.get("schema") != "padataset.archb-cross-surrogate-eval-request.v1":
        raise ValueError("Architecture-B request schema mismatch")
    src = req.get("source_backbone") or {}
    if int(artifact_id) != int(src.get("artifact_id", -1)):
        raise ValueError("supplied artifact ID mismatch")

    if destination.exists() and any(destination.iterdir()):
        raise ValueError("rehydration destination must be empty")
    _safe_extract(artifact_zip, destination)

    result_root = destination / "scientific-results"
    receipt_path = result_root / "scientific-receipt.json"
    if not receipt_path.is_file():
        raise ValueError("scientific execution receipt missing")
    receipt = _load(receipt_path)

    if receipt.get("schema") != "padataset.scientific-execution-receipt.v1":
        raise ValueError("scientific receipt schema mismatch")
    if receipt.get("decision") != "PASS":
        raise ValueError("scientific receipt decision is not PASS")
    if receipt.get("operation") != "train_backbone":
        raise ValueError("source artifact is not a backbone training result")
    if receipt.get("candidate_sha") != src.get("candidate_sha"):
        raise ValueError("backbone candidate SHA mismatch")
    if receipt.get("dataset_profile") != src.get("dataset_profile"):
        raise ValueError("backbone dataset profile mismatch")
    if receipt.get("runtime_tree_sha256") != src.get("runtime_tree_sha256"):
        raise ValueError("backbone runtime tree mismatch")

    run_name = str(src["run_name"])
    run_dir = result_root / "backbone" / run_name
    config_path = run_dir / "config.json"
    model_path = run_dir / "best_model.pt"
    summary_path = run_dir / "summary.json"
    train_complete_path = run_dir / "train_complete.json"
    for p in (config_path, model_path, summary_path, train_complete_path):
        if not p.is_file():
            raise ValueError(f"required backbone file missing: {p.name}")

    receipt_files = {
        x["path"]: x
        for x in receipt.get("files", [])
        if isinstance(x, dict) and isinstance(x.get("path"), str)
    }
    rel_prefix = f"backbone/{run_name}"
    expected = {
        f"{rel_prefix}/config.json": (config_path, src["config_sha256"]),
        f"{rel_prefix}/best_model.pt": (model_path, src["best_model_sha256"]),
    }
    for rel, (path, expected_sha) in expected.items():
        row = receipt_files.get(rel)
        if row is None or row.get("sha256") != expected_sha:
            raise ValueError(f"receipt hash mismatch for {rel}")
        if _sha256(path) != expected_sha:
            raise ValueError(f"rehydrated file hash mismatch for {rel}")

    cfg = _load(config_path)
    summary = _load(summary_path)
    if cfg.get("run_name") != run_name:
        raise ValueError("backbone run_name mismatch")
    if cfg.get("unknown_pas") != ["PA2"]:
        raise ValueError("backbone held-out target mismatch")
    if set(cfg.get("pas") or []) != {"PA1", "PA2", "PA3", "PA4", "PA8"}:
        raise ValueError("backbone PA taxonomy mismatch")
    if cfg.get("early_stopping_mode") != "known_only":
        raise ValueError("backbone checkpoint selection is not known-only")
    if cfg.get("quarantine_target_until_test") is not True:
        raise ValueError("backbone target quarantine disabled")
    if float(cfg.get("open_val_frac", -1)) != 0.0:
        raise ValueError("backbone target-open validation was not disabled")
    if int(cfg.get("cache_len", -1)) != 16384:
        raise ValueError("backbone cache length mismatch")
    if cfg.get("source_type") != "ota":
        raise ValueError("backbone source type mismatch")
    if cfg.get("source_name") != "ota_core_high_run01":
        raise ValueError("backbone source name mismatch")
    if cfg.get("dataset_tag") != "ota_core_high_run01":
        raise ValueError("backbone dataset tag mismatch")
    if cfg.get("noise_tag") != "high_run01":
        raise ValueError("backbone noise tag mismatch")

    if summary.get("target_test_consumed") is not False:
        raise ValueError("backbone target test was consumed before B0")
    if summary.get("target_quarantine_status") != "PRESERVED_FOR_FINAL_FROZEN_EVALUATOR":
        raise ValueError("backbone quarantine status mismatch")
    if summary.get("unknown_pas") != ["PA2"]:
        raise ValueError("backbone summary target mismatch")
    if list(summary.get("class_names") or []) != ["PA1", "PA3", "PA4", "PA8"]:
        raise ValueError("backbone known class ordering mismatch")

    return {
        "artifact_id": int(src["artifact_id"]),
        "run_dir": str(run_dir),
        "candidate_sha": str(receipt["candidate_sha"]),
        "dataset_profile": str(receipt["dataset_profile"]),
        "target_test_consumed": bool(summary["target_test_consumed"]),
        "config_sha256": _sha256(config_path),
        "best_model_sha256": _sha256(model_path),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", required=True)
    ap.add_argument("--artifact-id", required=True, type=int)
    ap.add_argument("--artifact-zip", required=True)
    ap.add_argument("--destination", required=True)
    args = ap.parse_args()
    print(json.dumps(
        rehydrate_archb_backbone(
            request_path=Path(args.request),
            artifact_id=args.artifact_id,
            artifact_zip=Path(args.artifact_zip),
            destination=Path(args.destination),
        ),
        sort_keys=True,
    ))


if __name__ == "__main__":
    main()
