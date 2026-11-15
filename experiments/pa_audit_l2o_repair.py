#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
import torch


def per_class_f1_from_cm(cm: np.ndarray) -> list[float]:
    cm = np.asarray(cm, dtype=np.float64)
    out = []
    for i in range(cm.shape[0]):
        tp = cm[i, i]
        fp = cm[:, i].sum() - tp
        fn = cm[i, :].sum() - tp
        denom = 2.0 * tp + fp + fn
        out.append(float(0.0 if denom <= 0 else (2.0 * tp) / denom))
    return out


def audit_run(run_dir: Path, val_macro_gate: float, min_class_gate: float) -> dict:
    summary_path = run_dir / "summary.json"
    checkpoint_path = run_dir / "best_model.pt"
    if not summary_path.is_file() or not checkpoint_path.is_file():
        return {
            "run_dir": str(run_dir),
            "status": "MISSING",
            "missing_summary": not summary_path.is_file(),
            "missing_checkpoint": not checkpoint_path.is_file(),
        }

    summary = json.loads(summary_path.read_text())
    ckpt = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    val = ckpt.get("val_stats") or {}
    cm = np.asarray(val.get("confusion_matrix", []))
    class_names = list(ckpt.get("class_names") or summary.get("class_names") or [])

    if cm.ndim != 2 or cm.shape[0] == 0:
        return {
            "run_dir": str(run_dir),
            "run_name": summary.get("run_name"),
            "status": "INVALID",
            "reason": "best checkpoint lacks validation confusion matrix",
        }

    f1s = per_class_f1_from_cm(cm)
    val_macro = float(val.get("macro_f1", summary.get("best_val_macro_f1")))
    min_f1 = float(min(f1s))
    passed = val_macro >= val_macro_gate and min_f1 >= min_class_gate

    return {
        "run_dir": str(run_dir),
        "run_name": summary.get("run_name"),
        "status": "PASS" if passed else "HPO_REQUIRED",
        "best_epoch": int(summary.get("best_epoch")) if summary.get("best_epoch") is not None else None,
        "val_macro_f1": val_macro,
        "val_min_class_f1": min_f1,
        "val_per_class_f1": {
            (class_names[i] if i < len(class_names) else str(i)): float(v)
            for i, v in enumerate(f1s)
        },
        "test_known_macro_f1_report_only": summary.get("test_known_macro_f1"),
        "target_quarantine_status": summary.get("target_quarantine_status"),
        "target_test_consumed_during_training_finalization": summary.get("target_test_consumed"),
        "gate": {
            "val_macro_f1_min": float(val_macro_gate),
            "val_min_class_f1_min": float(min_class_gate),
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-root", default="results_pa_ota_l2o_repair")
    ap.add_argument("--manifest", default="manifests/l2o_surrogate_matrix_repair_v1.tsv")
    ap.add_argument("--out", default="local_artifacts/l2o_repair_audit.json")
    ap.add_argument("--val-macro-gate", type=float, default=0.95)
    ap.add_argument("--min-class-gate", type=float, default=0.90)
    args = ap.parse_args()

    results_root = Path(args.results_root)
    rows = list(csv.DictReader(Path(args.manifest).open(), delimiter="\t"))
    records = [
        audit_run(
            results_root / row["run_name"],
            val_macro_gate=args.val_macro_gate,
            min_class_gate=args.min_class_gate,
        )
        for row in rows
    ]

    payload = {
        "schema": "padataset.l2o-repair-audit.v1",
        "selection_policy": "known_validation_only",
        "test_metrics_used_for_retuning": False,
        "val_macro_gate": args.val_macro_gate,
        "min_class_gate": args.min_class_gate,
        "counts": {
            "total": len(records),
            "pass": sum(r.get("status") == "PASS" for r in records),
            "hpo_required": sum(r.get("status") == "HPO_REQUIRED" for r in records),
            "missing": sum(r.get("status") == "MISSING" for r in records),
            "invalid": sum(r.get("status") == "INVALID" for r in records),
        },
        "records": records,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload["counts"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
