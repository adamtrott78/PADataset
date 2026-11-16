#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

RESULT_SCHEMA = "padataset.l2o-directional-eval-result.v1"
MATRIX_SCHEMA = "padataset.l2o-directional-eval-matrix.v1"


def _load(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def aggregate_directional_results(
    *,
    canonical_matrix_path: Path,
    policy_path: Path,
    results_root: Path,
    output_json: Path,
    output_csv: Path,
) -> Dict[str, Any]:
    matrix = _load(canonical_matrix_path)
    policy = _load(policy_path)

    if matrix.get("schema") != "padataset.l2o-canonical-backbone-matrix.v1":
        raise ValueError("canonical matrix schema mismatch")
    if policy.get("schema") != "padataset.l2o-directional-eval-policy.v1":
        raise ValueError("policy schema mismatch")
    if int(matrix.get("completed_backbone_count", -1)) != 10:
        raise ValueError("all 10 canonical backbones must be COMPLETE before aggregation")
    if int(matrix.get("remaining_backbone_count", -1)) != 0:
        raise ValueError("canonical matrix still has remaining backbones")

    expected: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for backbone in matrix.get("backbones", []):
        if backbone.get("status") != "COMPLETE":
            raise ValueError(f"backbone not COMPLETE: {backbone.get('canonical_key')}")
        for cell in backbone.get("directed_cells", []):
            key = (
                str(cell["evaluation_target"]),
                str(cell["evaluation_surrogate"]),
            )
            if key in expected:
                raise ValueError(f"duplicate expected directional cell: {key}")
            expected[key] = backbone

    if len(expected) != 20:
        raise ValueError(f"expected 20 directional cells, got {len(expected)}")

    files = sorted(results_root.rglob("result_record.json"))
    if len(files) != 20:
        raise ValueError(f"expected exactly 20 result_record.json files, got {len(files)}")

    seen: Dict[Tuple[str, str], Path] = {}
    records: List[Dict[str, Any]] = []

    for path in files:
        record = _load(path)
        if record.get("schema") != RESULT_SCHEMA:
            raise ValueError(f"result schema mismatch: {path}")
        if record.get("status") != "COMPLETE":
            raise ValueError(f"result not COMPLETE: {path}")
        if record.get("policy_id") != policy.get("policy_id"):
            raise ValueError(f"policy_id mismatch: {path}")

        key = (
            str(record.get("evaluation_target")),
            str(record.get("evaluation_surrogate")),
        )
        if key in seen:
            raise ValueError(f"duplicate directional result for {key}: {seen[key]} and {path}")
        if key not in expected:
            raise ValueError(f"unexpected directional result: {key}")

        backbone = expected[key]
        if record.get("canonical_key") != backbone.get("canonical_key"):
            raise ValueError(f"canonical key mismatch for {key}")
        if list(record.get("canonical_pair") or []) != list(backbone.get("canonical_pair") or []):
            raise ValueError(f"canonical pair mismatch for {key}")
        if list(record.get("known_pas") or []) != list(backbone.get("known_pas") or []):
            raise ValueError(f"known PA mismatch for {key}")
        if record.get("checkpoint") != policy.get("checkpoint"):
            raise ValueError(f"checkpoint drift for {key}")

        artifact = record.get("artifact") or {}
        checks = {
            "id": int(backbone["artifact_id"]),
            "digest": backbone["artifact_digest"],
            "workflow_run_id": int(backbone["workflow_run_id"]),
            "workflow_job_id": int(backbone["workflow_job_id"]),
            "candidate_sha": backbone["candidate_sha"],
            "best_model_sha256": backbone["best_model_sha256"],
            "config_sha256": backbone["config_sha256"],
        }
        for field, expected_value in checks.items():
            actual = artifact.get(field)
            if field in {"id", "workflow_run_id", "workflow_job_id"}:
                actual = int(actual)
            if actual != expected_value:
                raise ValueError(f"artifact provenance mismatch for {key}: {field}")

        provenance = record.get("provenance") or {}
        if provenance.get("target_labels_used_for_tuning") is not False:
            raise ValueError(f"target tuning detected for {key}")
        if provenance.get("mix_true_open") is not False:
            raise ValueError(f"true target mixed into calibration for {key}")
        if provenance.get("threshold_source") != "known_only":
            raise ValueError(f"threshold source drift for {key}")
        if provenance.get("surrogate_only_open_calibration") is not True:
            raise ValueError(f"surrogate-only calibration proof missing for {key}")

        metrics = record.get("metrics") or {}
        required_metrics = (
            "known_reject_rate",
            "unknown_precision",
            "unknown_recall",
            "unknown_f1",
            "osr_acc",
            "osr_macro_f1",
            "unknown_auroc",
        )
        for name in required_metrics:
            value = float(metrics[name])
            if not (0.0 <= value <= 1.0):
                raise ValueError(f"metric out of [0,1] range for {key}: {name}={value}")

        seen[key] = path
        records.append(record)

    missing = sorted(set(expected) - set(seen))
    if missing:
        raise ValueError(f"missing directional results: {missing}")

    rows = []
    for record in sorted(
        records,
        key=lambda r: (str(r["evaluation_target"]), str(r["evaluation_surrogate"])),
    ):
        row = {
            "canonical_key": record["canonical_key"],
            "evaluation_target": record["evaluation_target"],
            "evaluation_surrogate": record["evaluation_surrogate"],
            "directional_reuse": bool(record["directional_reuse"]),
            **{k: float(v) for k, v in record["metrics"].items()},
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)

    summary = {
        "schema": MATRIX_SCHEMA,
        "status": "COMPLETE",
        "policy_id": policy["policy_id"],
        "canonical_backbones": 10,
        "directed_cells": 20,
        "provenance": {
            "target_labels_used_for_tuning": False,
            "mix_true_open": False,
            "threshold_source": "known_only",
            "surrogate_only_open_calibration": True,
        },
        "aggregate_metrics": {
            "mean_unknown_f1": float(df["unknown_f1"].mean()),
            "worst_unknown_f1": float(df["unknown_f1"].min()),
            "mean_osr_macro_f1": float(df["osr_macro_f1"].mean()),
            "worst_osr_macro_f1": float(df["osr_macro_f1"].min()),
            "mean_unknown_auroc": float(df["unknown_auroc"].mean()),
            "mean_known_reject_rate": float(df["known_reject_rate"].mean()),
        },
        "cells": rows,
    }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix", required=True)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--results-root", required=True)
    ap.add_argument("--output-json", required=True)
    ap.add_argument("--output-csv", required=True)
    args = ap.parse_args()

    result = aggregate_directional_results(
        canonical_matrix_path=Path(args.matrix),
        policy_path=Path(args.policy),
        results_root=Path(args.results_root),
        output_json=Path(args.output_json),
        output_csv=Path(args.output_csv),
    )
    print(json.dumps(result["aggregate_metrics"], sort_keys=True))


if __name__ == "__main__":
    main()
