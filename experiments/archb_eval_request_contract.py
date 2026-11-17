#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class ArchBEvalRequest:
    artifact_id: int
    artifact_digest: str
    workflow_run_id: int
    run_name: str
    target_pa: str
    state_mode: str
    evaluator_args: Tuple[str, ...]


def _load(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_archb_eval_request(
    *,
    request_path: Path,
    run_dir: Path,
    out_dir: Path,
) -> ArchBEvalRequest:
    req = _load(request_path)

    if req.get("schema") != "padataset.archb-cross-surrogate-eval-request.v1":
        raise ValueError("Architecture-B request schema mismatch")
    if req.get("status") != "READY_FOR_BOUNDED_EVALUATOR":
        raise ValueError("Architecture-B request is not evaluator-ready")
    if req.get("task_id") != "mth602-final-multisurrogate-dqnguard-v1":
        raise ValueError("Architecture-B task identity mismatch")
    if req.get("architecture") != "B":
        raise ValueError("Architecture-B architecture drift")

    stage = req.get("stage")
    stage_policy = {
        "B0": {
            "policy_id": "mth602_archb_b0_frozen_v1",
            "state_mode": "softmax3",
            "class_conditional_bands": False,
            "tune_band_weights": False,
        },
        "B1": {
            "policy_id": "mth602_archb_b1_frozen_v1",
            "state_mode": "expanded5",
            "class_conditional_bands": False,
            "tune_band_weights": False,
        },
        "B2": {
            "policy_id": "mth602_archb_b2_frozen_v1",
            "state_mode": "softmax3",
            "class_conditional_bands": True,
            "tune_band_weights": False,
        },
        "B3": {
            "policy_id": "mth602_archb_b3_frozen_v1",
            "state_mode": "softmax3",
            "class_conditional_bands": True,
            "tune_band_weights": True,
        },
    }.get(stage)
    if stage_policy is None:
        raise ValueError("Architecture-B development stage drift")
    if req.get("policy_id") != stage_policy["policy_id"]:
        raise ValueError("Architecture-B policy_id drift")
    if req.get("target_pa") != "PA2":
        raise ValueError(f"{stage} requires PA2 as the held-out target")
    if req.get("state_mode") != stage_policy["state_mode"]:
        raise ValueError(f"{stage} state mode drift")
    if bool(req.get("class_conditional_bands", False)) != bool(
        stage_policy["class_conditional_bands"]
    ):
        raise ValueError(f"{stage} class-conditional band mode drift")
    if bool(req.get("tune_band_weights", False)) != bool(
        stage_policy["tune_band_weights"]
    ):
        raise ValueError(f"{stage} band-weight tuning mode drift")
    if req.get("checkpoint") != "best_model":
        raise ValueError(f"{stage} requires best_model checkpoint")
    if float(req.get("known_budget", -1)) != 0.05:
        raise ValueError(f"{stage} known-reject budget drift")
    if int(req.get("partition_seed", -1)) != 1701:
        raise ValueError(f"{stage} partition seed drift")
    if int(req.get("dqn_seed", -1)) != 42:
        raise ValueError(f"{stage} DQN seed drift")
    if int(req.get("dqn_episodes", -1)) != 30:
        raise ValueError(f"{stage} DQN episode count drift")
    if int(req.get("batch_size", -1)) != 128:
        raise ValueError(f"{stage} evaluator batch size drift")
    if int(req.get("num_workers", -1)) != 0:
        raise ValueError(f"{stage} evaluator worker count drift")
    if req.get("evaluator_device") != "cuda":
        raise ValueError(f"{stage} evaluator must use CUDA")

    if stage == "B1":
        if req.get("predeclared_stage_transition") is not True:
            raise ValueError("B1 must be a predeclared stage transition")
        if req.get("b0_target_metrics_used_for_b1_parameters") is not False:
            raise ValueError("B1 may not use B0 target metrics for parameters")
    if stage == "B2":
        if req.get("predeclared_stage_transition") is not True:
            raise ValueError("B2 must be a predeclared stage transition")
        if req.get("target_metrics_used_for_state_mode_selection") is not False:
            raise ValueError("B2 state-mode selection may not use target metrics")
        decision = req.get("state_mode_decision") or {}
        exact_decision = {
            "rule": "compare selected candidates by frozen off-diagonal lexicographic rule",
            "selected_state_mode": "softmax3",
            "b0_artifact_id": 14354747328,
            "b0_artifact_digest": "sha256:3863632fd9fc2ddb859eaa56616b9605e41ae1c53e4deacd1f73700148dc32f7",
            "b0_selected_worst_cross_unknown_f1": 0.003686635944700461,
            "b1_artifact_id": 14361967189,
            "b1_artifact_digest": "sha256:2b16a0edac525b17f7e238e3b302bda19ddd838550279967f12e964b40e71d08",
            "b1_selected_worst_cross_unknown_f1": 0.0,
        }
        if decision != exact_decision:
            raise ValueError("B2 state-mode decision provenance drift")
        band = req.get("band_policy") or {}
        exact_band = {
            "fit_role": "known_guard",
            "features": ["top2_gap", "logit_variance", "energy"],
            "percentiles": [5.0, 95.0],
            "normalization_fit_role": "known_norm",
            "guard_weight_rule": "positive_median_separation_else_uniform",
            "candidate_guard_training": "own_pseudo_surrogate_only",
            "guard_normalization": "empirical_known_cdf",
            "composite_score": "dqn_margin_plus_guard_cdf",
        }
        if band != exact_band:
            raise ValueError("B2 band policy drift")

    if stage == "B3":
        if req.get("predeclared_stage_transition") is not True:
            raise ValueError("B3 must be a predeclared stage transition")
        if req.get("target_metrics_used_for_b3_trigger_or_tuning") is not False:
            raise ValueError("B3 may not use target metrics for trigger or tuning")

        trigger = req.get("b3_trigger") or {}
        exact_trigger = {
            "rule": "B2 demonstrates complementary pseudo-open development value",
            "b0_artifact_id": 14354747328,
            "b0_selected_mean_cross_unknown_f1": 0.1102334,
            "b0_selected_mean_cross_osr_macro_f1": 0.7314352,
            "b0_selected_worst_cross_unknown_f1": 0.0036866,
            "b2_artifact_id": 14369751106,
            "b2_artifact_digest": "sha256:e5d76e4b8b90c101218a7c3603c9fd92d8e87b439eaffa36a9f46a1525e17d00",
            "b2_selected_mean_cross_unknown_f1": 0.12087985437740191,
            "b2_selected_mean_cross_osr_macro_f1": 0.7357077527296183,
            "b2_selected_worst_cross_unknown_f1": 0.0036101083032490976,
            "all_b2_candidate_guard_weights_uniform": True,
        }
        if trigger != exact_trigger:
            raise ValueError("B3 trigger provenance drift")

        search = req.get("b3_search_policy") or {}
        exact_search = {
            "weight_rules": [
                "uniform",
                "gap_only",
                "variance_only",
                "energy_only",
                "gap_variance_equal",
                "gap_energy_equal",
                "variance_energy_equal",
                "absolute_median_separation",
            ],
            "guard_scales": [0.5, 1.0, 2.0],
            "band_percentiles": [5.0, 95.0],
            "features": ["top2_gap", "logit_variance", "energy"],
            "selection_evidence": "off_diagonal_pseudo_open_only",
            "selection_rule": [
                "max worst off-diagonal unknown_f1",
                "max mean off-diagonal unknown_f1",
                "max mean off-diagonal osr_macro_f1",
                "min known_guard_reject_rate",
            ],
            "dqn_state_mode": "softmax3",
            "dqn_training_changed": False,
            "candidate_guard_training": "own_pseudo_surrogate_only",
            "threshold_source": "known_only",
            "known_budget": 0.05,
        }
        if search != exact_search:
            raise ValueError("B3 search policy drift")

    for field in (
        "target_labels_used_for_fitting",
        "target_labels_used_for_thresholding",
        "target_labels_used_for_candidate_selection",
    ):
        if req.get(field) is not False:
            raise ValueError(f"{field} must remain false")
    if req.get("target_first_consumed_after_winner_frozen") is not True:
        raise ValueError("target consumption ordering invariant drift")

    src = req.get("source_backbone") or {}
    exact = {
        "artifact_id": 14180249360,
        "artifact_digest": "sha256:f7de2637df85487b21903a448630815fc63c1247253b98ffc754b46586b9b39b",
        "artifact_name": "padataset-scientific-43751609944",
        "workflow_run_id": 43751609944,
        "candidate_sha": "befe383fd67c8bca8d8ce370344b33c7e13cd52f",
        "dataset_profile": "ota_core_high_run01_len16384_v1",
        "run_name": "mth602_archC_backbone_knownonly_unkPA2_c16384_seed0_detv2",
        "config_sha256": "a9c08353490f944ec1c5fb363002f41a8b32f875914251c30604cc2c03b35188",
        "best_model_sha256": "4fa0c67d1c0c619ab4cde058519ca603fa95d8afb8f58ebf8d564ebafb9989ef",
        "runtime_tree_sha256": "6922847a7ea87c318a36e1fd2cd3af5283e768ff06de90c4cb2558ea0d48cdaa",
    }
    for key, value in exact.items():
        if src.get(key) != value:
            raise ValueError(f"source backbone {key} drift")

    args = (
        "--run-dir", str(run_dir),
        "--checkpoint", "best_model",
        "--out-dir", str(out_dir),
        "--device", "cuda",
        "--batch-size", "128",
        "--num-workers", "0",
        "--partition-seed", "1701",
        "--dqn-episodes", "30",
        "--known-budget", "0.05",
        "--state-mode", str(req["state_mode"]),
    )
    if bool(req.get("class_conditional_bands", False)):
        args = (*args, "--class-conditional-bands")
    if bool(req.get("tune_band_weights", False)):
        args = (*args, "--tune-band-weights")

    return ArchBEvalRequest(
        artifact_id=int(src["artifact_id"]),
        artifact_digest=str(src["artifact_digest"]),
        workflow_run_id=int(src["workflow_run_id"]),
        run_name=str(src["run_name"]),
        target_pa=str(req["target_pa"]),
        state_mode=str(req["state_mode"]),
        evaluator_args=args,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", required=True)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    r = resolve_archb_eval_request(
        request_path=Path(args.request),
        run_dir=Path(args.run_dir),
        out_dir=Path(args.out_dir),
    )
    print(json.dumps({
        "artifact_id": r.artifact_id,
        "artifact_digest": r.artifact_digest,
        "workflow_run_id": r.workflow_run_id,
        "run_name": r.run_name,
        "target_pa": r.target_pa,
        "state_mode": r.state_mode,
        "evaluator_args": list(r.evaluator_args),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
