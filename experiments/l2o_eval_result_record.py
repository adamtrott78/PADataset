#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd


RESULT_SCHEMA = "padataset.l2o-directional-eval-result.v1"


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_result_record(
    *,
    request_path: Path,
    matrix_path: Path,
    policy_path: Path,
    summary_csv: Path,
    output_path: Path,
) -> Dict[str, Any]:
    request = _load_json(request_path)
    matrix = _load_json(matrix_path)
    policy = _load_json(policy_path)

    if request.get("schema") != "padataset.l2o-directional-eval-request.v1":
        raise ValueError("request schema mismatch")
    if matrix.get("schema") != "padataset.l2o-canonical-backbone-matrix.v1":
        raise ValueError("matrix schema mismatch")
    if policy.get("schema") != "padataset.l2o-directional-eval-policy.v1":
        raise ValueError("policy schema mismatch")
    if request.get("policy_id") != policy.get("policy_id"):
        raise ValueError("policy_id mismatch")
    if request.get("target_labels_used_for_tuning") is not False:
        raise ValueError("request permits target-label tuning")
    if policy.get("target_labels_used_for_tuning") is not False:
        raise ValueError("policy permits target-label tuning")
    if policy.get("mix_true_open") is not False:
        raise ValueError("Track-A policy must remain surrogate-only")

    rows = [
        x for x in matrix.get("backbones", [])
        if x.get("canonical_key") == request.get("canonical_key")
    ]
    if len(rows) != 1:
        raise ValueError("canonical_key must resolve exactly once")
    backbone = rows[0]
    if backbone.get("status") != "COMPLETE":
        raise ValueError("backbone is not COMPLETE")
    if int(request.get("artifact_id", -1)) != int(backbone.get("artifact_id", -2)):
        raise ValueError("artifact ID mismatch")
    if request.get("artifact_digest") != backbone.get("artifact_digest"):
        raise ValueError("artifact digest mismatch")

    df = pd.read_csv(summary_csv)

    target = str(request["evaluation_target"])
    surrogate = str(request["evaluation_surrogate"])
    analysis_mode = request.get("analysis_mode")

    if analysis_mode == "selector_geometry_pair_v1":
        if len(df) != 2:
            raise ValueError(f"selector geometry requires exactly two directional rows, got {len(df)}")
        if set(df.get("analysis_mode", [])) != {"selector_geometry_pair_v1"}:
            raise ValueError("selector geometry analysis_mode mismatch")
        got = set(zip(df["target"].astype(str), df["surrogate"].astype(str)))
        expected = {(target, surrogate), (surrogate, target)}
        if got != expected:
            raise ValueError(f"selector geometry directions mismatch: got={got!r} expected={expected!r}")
        required = [
            "known_p1_mean", "sur_p1_mean", "p1_drop_known_minus_sur",
            "known_gap_mean", "sur_gap_mean", "gap_drop_known_minus_sur",
            "known_entropy_mean", "sur_entropy_mean", "entropy_rise_sur_minus_known",
            "confidence_geometry_score", "sur_centroid_margin_median",
            "surrogate_known_distance_ratio", "feature_distance_score",
            "feature_boundary_score", "target_labels_used_for_tuning",
        ]
        missing = [name for name in required if name not in df.columns]
        if missing:
            raise ValueError(f"selector geometry fields missing: {missing!r}")
        for value in df["target_labels_used_for_tuning"]:
            if str(value).strip().lower() not in {"false", "0"}:
                raise ValueError("selector geometry reports target-label tuning")
        record = {
            "schema": "padataset.l2o-selector-geometry-result.v1",
            "status": "COMPLETE",
            "analysis_mode": analysis_mode,
            "policy_id": policy["policy_id"],
            "canonical_key": backbone["canonical_key"],
            "canonical_pair": list(backbone["canonical_pair"]),
            "known_pas": list(backbone["known_pas"]),
            "artifact": {
                "id": int(backbone["artifact_id"]),
                "digest": backbone["artifact_digest"],
                "workflow_run_id": int(backbone["workflow_run_id"]),
                "workflow_job_id": int(backbone["workflow_job_id"]),
                "candidate_sha": backbone["candidate_sha"],
                "best_model_sha256": backbone["best_model_sha256"],
                "config_sha256": backbone["config_sha256"],
            },
            "checkpoint": request["checkpoint"],
            "provenance": {
                "target_labels_used_for_tuning": False,
                "target_test_consumed": False,
                "frozen_historical_formulas": True,
                "known_cap": int(policy["known_cap"]),
                "open_cap": int(policy["open_cap"]),
            },
            "rows": df.to_dict(orient="records"),
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return record

    if analysis_mode is not None:
        raise ValueError(f"unsupported analysis_mode: {analysis_mode!r}")
    if len(df) != 1:
        raise ValueError(f"expected exactly one evaluator summary row, got {len(df)}")
    row = df.iloc[0].to_dict()

    if str(row.get("surrogate_open_pa")) != surrogate:
        raise ValueError("evaluator surrogate mismatch")

    try:
        target_list = json.loads(str(row.get("target_unknown_pas")))
    except Exception as exc:
        raise ValueError("target_unknown_pas is not valid JSON") from exc
    if target_list != [target]:
        raise ValueError("evaluator target mismatch")

    try:
        pair = json.loads(str(row.get("backbone_canonical_excluded_pair")))
    except Exception as exc:
        raise ValueError("backbone canonical pair is not valid JSON") from exc
    if pair != list(backbone.get("canonical_pair") or []):
        raise ValueError("evaluator canonical pair mismatch")

    if bool(row.get("target_labels_used_for_tuning")) is not False:
        # CSV booleans can arrive as strings; normalize explicitly below.
        v = str(row.get("target_labels_used_for_tuning")).strip().lower()
        if v not in {"false", "0"}:
            raise ValueError("evaluator reports target-label tuning")

    if str(row.get("decision_mode")) != str(policy.get("decision_mode")):
        raise ValueError("decision mode drift")
    if abs(float(row.get("max_known_reject_cal")) - float(policy.get("max_known_reject_cal"))) > 1e-12:
        raise ValueError("known-reject budget drift")
    if str(row.get("band_accept_mode")) != str(policy.get("band_accept_mode")):
        raise ValueError("band mode drift")

    metric_names = [
        "known_reject_rate",
        "unknown_precision",
        "unknown_recall",
        "unknown_f1",
        "osr_acc",
        "osr_macro_f1",
        "unknown_auroc",
    ]
    metrics = {}
    for name in metric_names:
        if name not in row:
            raise ValueError(f"required metric missing: {name}")
        metrics[name] = float(row[name])

    record = {
        "schema": RESULT_SCHEMA,
        "status": "COMPLETE",
        "policy_id": policy["policy_id"],
        "canonical_key": backbone["canonical_key"],
        "canonical_pair": list(backbone["canonical_pair"]),
        "known_pas": list(backbone["known_pas"]),
        "evaluation_target": target,
        "evaluation_surrogate": surrogate,
        "directional_reuse": str(row.get("directional_reuse")).strip().lower() in {"true", "1"},
        "artifact": {
            "id": int(backbone["artifact_id"]),
            "digest": backbone["artifact_digest"],
            "workflow_run_id": int(backbone["workflow_run_id"]),
            "workflow_job_id": int(backbone["workflow_job_id"]),
            "candidate_sha": backbone["candidate_sha"],
            "best_model_sha256": backbone["best_model_sha256"],
            "config_sha256": backbone["config_sha256"],
        },
        "checkpoint": request["checkpoint"],
        "provenance": {
            "target_labels_used_for_tuning": False,
            "mix_true_open": False,
            "threshold_source": "known_only",
            "surrogate_only_open_calibration": True,
        },
        "metrics": metrics,
        "threshold": {
            "score_threshold": None if pd.isna(row.get("score_threshold")) else float(row.get("score_threshold")),
            "known_reject_cal": None if pd.isna(row.get("threshold_known_reject_cal")) else float(row.get("threshold_known_reject_cal")),
            "open_recall_cal_diagnostic_only": None if pd.isna(row.get("threshold_open_recall_cal")) else float(row.get("threshold_open_recall_cal")),
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", required=True)
    ap.add_argument("--matrix", required=True)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--summary-csv", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    record = build_result_record(
        request_path=Path(args.request),
        matrix_path=Path(args.matrix),
        policy_path=Path(args.policy),
        summary_csv=Path(args.summary_csv),
        output_path=Path(args.output),
    )
    print(json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
