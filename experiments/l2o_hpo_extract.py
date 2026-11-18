#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

PA_ORDER = ["PA1", "PA2", "PA3", "PA4", "PA8"]


def per_class_f1_from_confusion(cm: list[list[float]]) -> list[float]:
    n = len(cm)
    if n == 0 or any(len(row) != n for row in cm):
        raise ValueError("validation confusion matrix must be non-empty and square")
    out = []
    for i in range(n):
        tp = float(cm[i][i])
        fp = sum(float(cm[r][i]) for r in range(n) if r != i)
        fn = sum(float(cm[i][c]) for c in range(n) if c != i)
        denom = 2.0 * tp + fp + fn
        out.append(0.0 if denom <= 0 else (2.0 * tp) / denom)
    return out


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def record_from_payloads(
    config: dict[str, Any],
    summary: dict[str, Any],
    checkpoint: dict[str, Any],
    *,
    config_path: str,
    repo_config_sha256: str | None = None,
) -> dict[str, Any]:
    meta = config.get("hpo_trial") or {}
    required = {
        "trial_id",
        "canonical_pair",
        "stage",
        "selection_evidence",
        "target_metrics_allowed_for_selection",
        "test_metrics_allowed_for_selection",
    }
    missing = required - set(meta)
    if missing:
        raise ValueError(f"HPO trial metadata missing: {sorted(missing)}")
    if meta["selection_evidence"] != "known_validation_only":
        raise ValueError("HPO trial selection evidence drift")
    if meta["target_metrics_allowed_for_selection"] is not False:
        raise ValueError("target metrics must be forbidden for HPO selection")
    if meta["test_metrics_allowed_for_selection"] is not False:
        raise ValueError("test metrics must be forbidden for HPO selection")
    if summary.get("target_test_consumed") is not False:
        raise ValueError("HPO artifact consumed target test before freeze")

    val = checkpoint.get("val_stats")
    if not isinstance(val, dict):
        raise ValueError("best checkpoint lacks val_stats")
    cm = val.get("confusion_matrix")
    if hasattr(cm, "tolist"):
        cm = cm.tolist()
    if not isinstance(cm, list):
        raise ValueError("best checkpoint lacks validation confusion matrix")
    f1s = per_class_f1_from_confusion(cm)

    class_names = list(checkpoint.get("class_names") or summary.get("class_names") or [])
    if len(class_names) != len(f1s):
        raise ValueError("class_names / confusion-matrix size mismatch")

    val_macro = float(val.get("macro_f1", summary.get("best_val_macro_f1")))
    if not (0.0 <= val_macro <= 1.0):
        raise ValueError("invalid validation macro-F1")
    per_class = {class_names[i]: float(f1s[i]) for i in range(len(f1s))}
    min_class = min(per_class.values())

    record = {
        "trial_id": str(meta["trial_id"]),
        "canonical_pair": str(meta["canonical_pair"]),
        "stage": str(meta["stage"]),
        "config_path": config_path,
        "status": "COMPLETE",
        "best_epoch": int(summary["best_epoch"]),
        "val_macro_f1": val_macro,
        "val_min_class_f1": float(min_class),
        "val_per_class_f1": per_class,
    }
    if repo_config_sha256 is not None:
        record["config_sha256"] = repo_config_sha256
    return record


def extract_run_dir(run_dir: Path, *, config_path: str, repo_config_sha256: str | None) -> dict[str, Any]:
    config_file = run_dir / "config.json"
    summary_file = run_dir / "summary.json"
    checkpoint_file = run_dir / "best_model.pt"
    for p in (config_file, summary_file, checkpoint_file):
        if not p.is_file():
            raise FileNotFoundError(p)

    config = json.loads(config_file.read_text(encoding="utf-8"))
    summary = json.loads(summary_file.read_text(encoding="utf-8"))

    import torch

    checkpoint = torch.load(checkpoint_file, map_location="cpu", weights_only=False)
    return record_from_payloads(
        config,
        summary,
        checkpoint,
        config_path=config_path,
        repo_config_sha256=repo_config_sha256,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", action="append", required=True)
    ap.add_argument("--config-path", action="append", required=True)
    ap.add_argument("--config-sha256", action="append")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    if len(args.run_dir) != len(args.config_path):
        raise SystemExit("--run-dir and --config-path counts must match")
    sha_values = args.config_sha256 or [None] * len(args.run_dir)
    if len(sha_values) != len(args.run_dir):
        raise SystemExit("--config-sha256 count must match --run-dir")

    records = [
        extract_run_dir(Path(run_dir), config_path=config_path, repo_config_sha256=sha)
        for run_dir, config_path, sha in zip(args.run_dir, args.config_path, sha_values)
    ]
    payload = {
        "schema": "padataset.l2o-hpo-known-validation-results.v2",
        "selection_evidence": "known_validation_only",
        "target_metrics_used": False,
        "test_metrics_used": False,
        "records": records,
    }
    Path(args.out).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"records": len(records), "out": args.out}, sort_keys=True))


if __name__ == "__main__":
    main()
