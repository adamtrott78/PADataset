#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple


@dataclass(frozen=True)
class DirectionalEvalRequest:
    canonical_key: str
    artifact_id: int
    artifact_digest: str
    evaluation_target: str
    evaluation_surrogate: str
    checkpoint: str
    analysis_mode: str | None
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


def resolve_directional_eval_request(
    *,
    request_path: Path,
    matrix_path: Path,
    policy_path: Path,
    run_dir: Path,
    out_dir: Path,
) -> DirectionalEvalRequest:
    request = _load(request_path)
    matrix = _load(matrix_path)
    policy = _load(policy_path)

    if request.get("schema") != "padataset.l2o-directional-eval-request.v1":
        raise ValueError("directional eval request schema mismatch")
    if matrix.get("schema") != "padataset.l2o-canonical-backbone-matrix.v1":
        raise ValueError("canonical matrix schema mismatch")
    if policy.get("schema") != "padataset.l2o-directional-eval-policy.v1":
        raise ValueError("directional eval policy schema mismatch")

    if request.get("canonical_matrix") != "manifests/l2o_canonical_backbone_matrix_v1.json":
        raise ValueError("request canonical matrix path drift")
    if request.get("evaluation_policy") != "manifests/l2o_directional_eval_policy_v1.json":
        raise ValueError("request policy path drift")
    if request.get("policy_id") != policy.get("policy_id"):
        raise ValueError("request policy_id mismatch")
    if request.get("status") != "READY_FOR_BOUNDED_EVALUATOR":
        raise ValueError("request is not ready for bounded evaluator")
    if request.get("target_labels_used_for_tuning") is not False:
        raise ValueError("request must prohibit target labels for tuning")
    analysis_mode = request.get("analysis_mode")
    if analysis_mode not in {None, "selector_geometry_pair_v1"}:
        raise ValueError(f"unsupported analysis_mode: {analysis_mode!r}")

    row = _find_row(matrix, str(request.get("canonical_key")))
    if int(request.get("artifact_id", -1)) != int(row.get("artifact_id", -2)):
        raise ValueError("request artifact ID mismatch")
    if request.get("artifact_digest") != row.get("artifact_digest"):
        raise ValueError("request artifact digest mismatch")
    if request.get("checkpoint") != policy.get("checkpoint"):
        raise ValueError("request checkpoint differs from frozen policy")

    target = str(request.get("evaluation_target"))
    surrogate = str(request.get("evaluation_surrogate"))
    if target == surrogate:
        raise ValueError("evaluation target and surrogate must be distinct")
    if set((target, surrogate)) != set(row.get("canonical_pair") or []):
        raise ValueError("direction does not match canonical excluded pair")

    allowed = {
        (str(x.get("evaluation_target")), str(x.get("evaluation_surrogate")))
        for x in row.get("directed_cells", [])
    }
    if (target, surrogate) not in allowed:
        raise ValueError("directional cell is not declared in canonical matrix")

    if policy.get("mix_true_open") is not False:
        raise ValueError("frozen Track-A policy must remain surrogate-only")
    if policy.get("target_labels_used_for_tuning") is not False:
        raise ValueError("frozen policy permits target tuning")
    if policy.get("decision_mode") != "score_threshold":
        raise ValueError("frozen Track-A policy requires score_threshold")
    if float(policy.get("max_known_reject_cal", -1)) != 0.05:
        raise ValueError("frozen known-reject budget drift")
    if policy.get("dqn_state_mode") != "softmax3":
        raise ValueError("frozen Track-A policy requires softmax3")

    args: List[str] = [
        "--run-dir", str(run_dir),
        "--checkpoint", str(policy["checkpoint"]),
        "--out-dir", str(out_dir),
        "--target-open-pa", target,
        "--surrogate-open-pa", surrogate,
        "--mode", str(policy["band_accept_mode"]),
        "--decision-mode", str(policy["decision_mode"]),
        "--max-known-reject-cal", str(policy["max_known_reject_cal"]),
        "--known-cap", str(int(policy["known_cap"])),
        "--open-cap", str(int(policy["open_cap"])),
        "--device", str(policy["evaluator_device"]),
        "--batch-size", str(int(policy["batch_size"])),
        "--num-workers", str(int(policy["num_workers"])),
    ]
    if analysis_mode == "selector_geometry_pair_v1":
        args.append("--selector-geometry-pair-only")

    # Deliberately never add --mix-true-open. Target-open examples are final
    # evaluation evidence only; they are forbidden from DQN fitting/thresholding.
    return DirectionalEvalRequest(
        canonical_key=row["canonical_key"],
        artifact_id=int(row["artifact_id"]),
        artifact_digest=str(row["artifact_digest"]),
        evaluation_target=target,
        evaluation_surrogate=surrogate,
        checkpoint=str(policy["checkpoint"]),
        analysis_mode=analysis_mode,
        evaluator_args=tuple(args),
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", required=True)
    ap.add_argument("--matrix", required=True)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    resolved = resolve_directional_eval_request(
        request_path=Path(args.request),
        matrix_path=Path(args.matrix),
        policy_path=Path(args.policy),
        run_dir=Path(args.run_dir),
        out_dir=Path(args.out_dir),
    )
    print(json.dumps({
        "canonical_key": resolved.canonical_key,
        "artifact_id": resolved.artifact_id,
        "artifact_digest": resolved.artifact_digest,
        "evaluation_target": resolved.evaluation_target,
        "evaluation_surrogate": resolved.evaluation_surrogate,
        "checkpoint": resolved.checkpoint,
        "analysis_mode": resolved.analysis_mode,
        "evaluator_args": list(resolved.evaluator_args),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
