#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple


REQUEST_SCHEMA = "padataset.l2o-control-eval-request.v1"
POLICY_SCHEMA = "padataset.l2o-control-eval-policy.v1"
PLAN_SCHEMA = "padataset.l2o-control-matrix-plan.v1"


@dataclass(frozen=True)
class ControlEvalRequest:
    canonical_key: str
    artifact_id: int
    artifact_digest: str
    evaluation_target: str
    evaluation_surrogate: str
    checkpoint: str
    evaluator_args: Tuple[str, ...]


def _load(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _find_row(matrix: Dict[str, Any], key: str) -> Dict[str, Any]:
    rows = [x for x in matrix.get("backbones", []) if x.get("canonical_key") == key]
    if len(rows) != 1:
        raise ValueError(f"canonical_key must resolve exactly once: {key!r}")
    row = rows[0]
    if row.get("status") != "COMPLETE":
        raise ValueError(f"canonical backbone is not COMPLETE: {key}")
    return row


def resolve_control_eval_request(
    *,
    request_path: Path,
    matrix_path: Path,
    plan_path: Path,
    policy_path: Path,
    run_dir: Path,
    out_dir: Path,
) -> ControlEvalRequest:
    request = _load(request_path)
    matrix = _load(matrix_path)
    plan = _load(plan_path)
    policy = _load(policy_path)

    if request.get("schema") != REQUEST_SCHEMA:
        raise ValueError("control eval request schema mismatch")
    if matrix.get("schema") != "padataset.l2o-canonical-backbone-matrix.v1":
        raise ValueError("canonical matrix schema mismatch")
    if plan.get("schema") != PLAN_SCHEMA or plan.get("status") != "FROZEN_PLAN_NO_EXECUTION":
        raise ValueError("control plan is not frozen")
    if policy.get("schema") != POLICY_SCHEMA:
        raise ValueError("control policy schema mismatch")
    if request.get("policy_id") != policy.get("policy_id"):
        raise ValueError("control request policy_id mismatch")
    if request.get("canonical_matrix") != "manifests/l2o_canonical_backbone_matrix_v1.json":
        raise ValueError("control request canonical matrix path drift")
    if request.get("control_plan") != "manifests/l2o_control_matrix_plan_v1.json":
        raise ValueError("control request plan path drift")
    if request.get("evaluation_policy") != "manifests/l2o_control_eval_policy_v1.json":
        raise ValueError("control request policy path drift")
    if request.get("status") != "READY_FOR_BOUNDED_CONTROL_EVALUATOR":
        raise ValueError("control request is not ready")
    if request.get("target_labels_used_for_tuning") is not False:
        raise ValueError("control request permits target-label tuning")
    if request.get("target_test_consumed_before_final_eval") is not False:
        raise ValueError("control request permits pre-final target test")

    expected_controls = [
        policy["controls"]["dqn_ids_style"]["method_id"],
        policy["controls"]["varmax"]["method_id"],
    ]
    if request.get("controls") != expected_controls:
        raise ValueError("control request method set/order drift")

    row = _find_row(matrix, str(request.get("canonical_key")))
    if int(request.get("artifact_id", -1)) != int(row.get("artifact_id", -2)):
        raise ValueError("control request artifact ID mismatch")
    if request.get("artifact_digest") != row.get("artifact_digest"):
        raise ValueError("control request artifact digest mismatch")
    if request.get("checkpoint") != policy.get("checkpoint"):
        raise ValueError("control request checkpoint drift")

    target = str(request.get("evaluation_target"))
    surrogate = str(request.get("evaluation_surrogate"))
    if target == surrogate:
        raise ValueError("control target and surrogate must be distinct")
    if set((target, surrogate)) != set(row.get("canonical_pair") or []):
        raise ValueError("control direction outside canonical pair")
    allowed = {
        (str(x.get("evaluation_target")), str(x.get("evaluation_surrogate")))
        for x in row.get("directed_cells", [])
    }
    if (target, surrogate) not in allowed:
        raise ValueError("control directional cell is undeclared")

    plan_rows = [
        c for c in plan.get("cells", [])
        if c.get("canonical_key") == row["canonical_key"]
        and c.get("target") == target
        and c.get("external_surrogate") == surrogate
    ]
    if len(plan_rows) != 1:
        raise ValueError("control request does not resolve exactly once in frozen plan")
    plan_row = plan_rows[0]
    if int(plan_row.get("backbone_artifact_id", -1)) != int(row["artifact_id"]):
        raise ValueError("control plan artifact ID drift")
    if plan_row.get("backbone_artifact_digest") != row.get("artifact_digest"):
        raise ValueError("control plan artifact digest drift")
    if plan_row.get("best_model_sha256") != row.get("best_model_sha256"):
        raise ValueError("control plan checkpoint digest drift")

    dqn = policy["controls"]["dqn_ids_style"]
    varmax = policy["controls"]["varmax"]
    if dqn.get("state_mode") != "softmax3" or dqn.get("final_decision") != "hard_dqn_argmax":
        raise ValueError("DQN control semantics drift")
    if int(dqn.get("known_cap", -1)) != 625 or int(dqn.get("open_cap", -1)) != 625:
        raise ValueError("DQN control cap drift")
    if dqn.get("open_calibration_source") != "external_surrogate_validation":
        raise ValueError("DQN control calibration source drift")
    if varmax.get("calibration_mode") != "surrogate_all" or varmax.get("sweep_grid") != "smoke":
        raise ValueError("VarMax historical semantics drift")
    if varmax.get("external_surrogate_consumed") is not False:
        raise ValueError("VarMax external surrogate must remain unused")
    if policy.get("target_labels_used_for_tuning") is not False:
        raise ValueError("control policy permits target-label tuning")
    if policy.get("target_test_consumed_before_final_eval") is not False:
        raise ValueError("control policy permits pre-final target test")

    args: List[str] = [
        "--run-dir", str(run_dir),
        "--checkpoint", str(policy["checkpoint"]),
        "--out-dir", str(out_dir),
        "--policy", str(policy_path),
        "--target-open-pa", target,
        "--surrogate-open-pa", surrogate,
        "--device", str(policy["evaluator_device"]),
        "--batch-size", str(int(policy["batch_size"])),
        "--num-workers", str(int(policy["num_workers"])),
    ]
    return ControlEvalRequest(
        canonical_key=row["canonical_key"],
        artifact_id=int(row["artifact_id"]),
        artifact_digest=str(row["artifact_digest"]),
        evaluation_target=target,
        evaluation_surrogate=surrogate,
        checkpoint=str(policy["checkpoint"]),
        evaluator_args=tuple(args),
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", required=True)
    ap.add_argument("--matrix", required=True)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    r = resolve_control_eval_request(
        request_path=Path(args.request),
        matrix_path=Path(args.matrix),
        plan_path=Path(args.plan),
        policy_path=Path(args.policy),
        run_dir=Path(args.run_dir),
        out_dir=Path(args.out_dir),
    )
    print(json.dumps({
        "canonical_key": r.canonical_key,
        "artifact_id": r.artifact_id,
        "artifact_digest": r.artifact_digest,
        "evaluation_target": r.evaluation_target,
        "evaluation_surrogate": r.evaluation_surrogate,
        "checkpoint": r.checkpoint,
        "evaluator_args": list(r.evaluator_args),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
