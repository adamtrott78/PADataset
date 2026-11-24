#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd


RESULT_SCHEMA = "padataset.l2o-control-eval-result.v1"


def _load(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _bool(v) -> bool:
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in {"true", "1"}


def build_control_result_record(
    *,
    request_path: Path,
    matrix_path: Path,
    policy_path: Path,
    summary_csv: Path,
    metadata_path: Path,
    output_path: Path,
) -> Dict[str, Any]:
    request = _load(request_path)
    matrix = _load(matrix_path)
    policy = _load(policy_path)
    metadata = _load(metadata_path)

    if request.get("schema") != "padataset.l2o-control-eval-request.v1":
        raise ValueError("control request schema mismatch")
    if matrix.get("schema") != "padataset.l2o-canonical-backbone-matrix.v1":
        raise ValueError("canonical matrix schema mismatch")
    if policy.get("schema") != "padataset.l2o-control-eval-policy.v1":
        raise ValueError("control policy schema mismatch")
    if metadata.get("schema") != "padataset.l2o-control-eval-metadata.v1":
        raise ValueError("control metadata schema mismatch")
    if request.get("policy_id") != policy.get("policy_id") or metadata.get("policy_id") != policy.get("policy_id"):
        raise ValueError("control policy binding mismatch")

    rows = [x for x in matrix.get("backbones", []) if x.get("canonical_key") == request.get("canonical_key")]
    if len(rows) != 1:
        raise ValueError("canonical_key must resolve exactly once")
    backbone = rows[0]
    if backbone.get("status") != "COMPLETE":
        raise ValueError("backbone is not COMPLETE")
    if int(request.get("artifact_id", -1)) != int(backbone.get("artifact_id", -2)):
        raise ValueError("artifact ID mismatch")
    if request.get("artifact_digest") != backbone.get("artifact_digest"):
        raise ValueError("artifact digest mismatch")

    target = str(request["evaluation_target"])
    surrogate = str(request["evaluation_surrogate"])
    if metadata.get("target") != target or metadata.get("external_surrogate") != surrogate:
        raise ValueError("control metadata direction mismatch")
    if metadata.get("controls_fitted_before_target_test") is not True:
        raise ValueError("controls were not frozen before target test")
    if metadata.get("target_labels_used_for_tuning") is not False:
        raise ValueError("metadata reports target-label tuning")
    if metadata.get("target_test_consumed_before_final_eval") is not False:
        raise ValueError("metadata reports pre-final target-test consumption")

    df = pd.read_csv(summary_csv)
    expected_ids = [
        policy["controls"]["dqn_ids_style"]["method_id"],
        policy["controls"]["varmax"]["method_id"],
    ]
    if len(df) != 2 or list(df["control_id"]) != expected_ids:
        raise ValueError("control summary must contain exactly the two frozen controls in policy order")

    metric_names = [
        "known_reject_rate",
        "unknown_precision",
        "unknown_recall",
        "unknown_f1",
        "osr_acc",
        "osr_macro_f1",
        "unknown_auroc",
    ]
    controls = {}
    for _, row in df.iterrows():
        cid = str(row["control_id"])
        try:
            target_list = json.loads(str(row["target_unknown_pas"]))
        except Exception as exc:
            raise ValueError("target_unknown_pas is not valid JSON") from exc
        if target_list != [target] or str(row["external_surrogate"]) != surrogate:
            raise ValueError("control summary direction mismatch")
        if _bool(row["target_labels_used_for_tuning"]):
            raise ValueError("control summary reports target-label tuning")
        if _bool(row["target_test_consumed_before_final_eval"]):
            raise ValueError("control summary reports pre-final target-test use")
        metrics = {name: float(row[name]) for name in metric_names}
        if any(not (0.0 <= v <= 1.0) for v in metrics.values()):
            raise ValueError("control metric outside [0,1]")
        ext_consumed = _bool(row["external_surrogate_consumed"])
        if cid == policy["controls"]["dqn_ids_style"]["method_id"]:
            if not ext_consumed:
                raise ValueError("DQN control must consume external surrogate calibration")
            if int(row["known_calibration_n"]) != 625 or int(row["open_calibration_n"]) != 625:
                raise ValueError("DQN control calibration count drift")
        elif cid == policy["controls"]["varmax"]["method_id"]:
            if ext_consumed:
                raise ValueError("VarMax must not consume external surrogate")
            if str(row["varmax_calibration_mode"]) != "surrogate_all" or str(row["varmax_sweep_grid"]) != "smoke":
                raise ValueError("VarMax historical semantics drift")
        controls[cid] = {
            "calibration_source": str(row["calibration_source"]),
            "external_surrogate_consumed": ext_consumed,
            "known_calibration_n": int(row["known_calibration_n"]),
            "open_calibration_n": int(row["open_calibration_n"]),
            "metrics": metrics,
        }

    record = {
        "schema": RESULT_SCHEMA,
        "status": "COMPLETE",
        "policy_id": policy["policy_id"],
        "canonical_key": backbone["canonical_key"],
        "canonical_pair": list(backbone["canonical_pair"]),
        "known_pas": list(backbone["known_pas"]),
        "evaluation_target": target,
        "evaluation_surrogate": surrogate,
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
            "target_test_consumed_before_final_eval": False,
            "target_test_consumed_for_final_eval": True,
            "controls_fitted_before_target_test": True,
        },
        "controls": controls,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", required=True)
    ap.add_argument("--matrix", required=True)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--summary-csv", required=True)
    ap.add_argument("--metadata", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    record = build_control_result_record(
        request_path=Path(args.request),
        matrix_path=Path(args.matrix),
        policy_path=Path(args.policy),
        summary_csv=Path(args.summary_csv),
        metadata_path=Path(args.metadata),
        output_path=Path(args.output),
    )
    print(json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
