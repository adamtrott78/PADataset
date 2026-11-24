#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import gc
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import pandas as pd
import torch

from dqn_osr import DQNOSR
from evaluate import (
    build_osr_eval_bundle,
    collect_split_outputs_from_loader,
    _make_setup_from_run_config,
)
from osr_core import BackbonePayload, evaluate_osr_predictions, load_backbone_run
from prepData import build_data_from_setup
from varmax_osr import VarMaxOSR
from experiments.l2o_directional_contract import resolve_directional_l2o_contract
from experiments.pa_eval_dqn_guard_surrogate_open import build_surrogate_open_split, cap_split
from experiments.pa_eval_osr_one import make_calibration_builder


POLICY_SCHEMA = "padataset.l2o-control-eval-policy.v1"
POLICY_ID = "l2o_repaired_controls_frozen_v1"


def load_policy(path: Path) -> Dict[str, Any]:
    d = json.loads(path.read_text(encoding="utf-8"))
    if d.get("schema") != POLICY_SCHEMA:
        raise ValueError("control policy schema mismatch")
    if d.get("policy_id") != POLICY_ID:
        raise ValueError("control policy_id mismatch")
    if d.get("checkpoint") != "best_model":
        raise ValueError("matched controls require best_model")
    if d.get("target_labels_used_for_tuning") is not False:
        raise ValueError("control policy permits target-label tuning")
    if d.get("target_test_consumed_before_final_eval") is not False:
        raise ValueError("control policy permits pre-final target-test consumption")
    return d


def make_dqn_control(policy: Dict[str, Any]) -> DQNOSR:
    d = policy["controls"]["dqn_ids_style"]
    if d.get("method_id") != "dqn_ids_style_softmax3_external_surrogate_cap625_v1":
        raise ValueError("DQN control method_id drift")
    if d.get("state_mode") != "softmax3":
        raise ValueError("DQN control state drift")
    if d.get("final_decision") != "hard_dqn_argmax":
        raise ValueError("DQN control decision drift")
    if d.get("open_calibration_source") != "external_surrogate_validation":
        raise ValueError("DQN control open-calibration drift")
    return DQNOSR(
        state_mode="softmax3",
        gamma=float(d["gamma"]),
        epsilon=float(d["epsilon"]),
        epsilon_min=float(d["epsilon_min"]),
        epsilon_decay=float(d["epsilon_decay"]),
        learning_rate=float(d["learning_rate"]),
        memory_size=int(d["memory_size"]),
        batch_size=int(d["dqn_batch_size"]),
        episodes=int(d["episodes"]),
        anchor_fraction=float(d["anchor_fraction"]),
        train_subsample_size=int(d["train_subsample_size"]),
        centroid_update_threshold=float(d["centroid_update_threshold"]),
        seed=int(d["seed"]),
        device=str(d["device"]),
    )


def build_varmax_calibration(payload, extras, policy: Dict[str, Any]):
    d = policy["controls"]["varmax"]
    if d.get("method_id") != "varmax_surrogate_all_smoke_matched_l2o_v1":
        raise ValueError("VarMax control method_id drift")
    if d.get("calibration_mode") != "surrogate_all":
        raise ValueError("VarMax must remain surrogate_all")
    if d.get("sweep_grid") != "smoke":
        raise ValueError("VarMax must remain historical smoke sweep")
    if d.get("external_surrogate_consumed") is not False:
        raise ValueError("VarMax must not consume the external surrogate")
    calibration = make_calibration_builder("surrogate_all", "smoke")(payload, extras)
    if calibration.get("calibration_open") is not None:
        raise ValueError("VarMax surrogate_all unexpectedly received open calibration")
    if calibration.get("calibration_mode") != "surrogate_all":
        raise ValueError("VarMax calibration builder drift")
    return calibration


def make_varmax_control(policy: Dict[str, Any]) -> VarMaxOSR:
    d = policy["controls"]["varmax"]
    return VarMaxOSR(
        temperature=float(d["temperature"]),
        use_energy=bool(d["use_energy"]),
        fit_on=str(d["fit_on"]),
        min_samples_per_class=int(d["min_samples_per_class"]),
    )


def _payload_meta(handle):
    return {
        "run_name": handle.run_name,
        "run_dir": handle.run_dir,
        "checkpoint_tag": handle.checkpoint_tag,
        "unknown_pas": handle.unknown_pas,
        "class_names": handle.class_names,
        "num_classes": handle.num_classes,
        "cache_len": handle.config.get("cache_len"),
        "seed": handle.config.get("seed"),
        "epochs": handle.config.get("epochs"),
        "source_type": handle.config.get("source_type", "digital"),
        "source_name": handle.config.get("source_name", "pilot_noisy_torch"),
        "dataset_tag": handle.config.get("dataset_tag"),
        "noise_tag": handle.config.get("noise_tag"),
    }


def build_target_calibration_payload(
    handle,
    *,
    batch_size: int,
    num_workers: int,
    data_root: str | None,
):
    """Collect only known validation evidence; do not iterate target-test loaders."""
    setup = _make_setup_from_run_config(handle.config, data_root=data_root)
    data = build_data_from_setup(
        setup,
        batch_size=batch_size,
        num_workers=num_workers,
        pin_memory=True,
    )
    try:
        known = collect_split_outputs_from_loader(handle, data["val_loader"], "val_known_control_fit")
        balanced_loader = data.get("val_known_balanced_loader", None)
        balanced = (
            collect_split_outputs_from_loader(handle, balanced_loader, "val_known_balanced_control_fit")
            if balanced_loader is not None
            else None
        )
        payload = BackbonePayload(
            meta=_payload_meta(handle),
            val_known=known,
            test_known=None,
            test_open=None,
        )
        extras = {
            "val_known_balanced": balanced,
            "val_open": None,
            "val_open_balanced": None,
        }
        return payload, extras
    finally:
        try:
            if hasattr(data.get("dataset", None), "close"):
                data["dataset"].close()
        except Exception:
            pass
        del data
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


def _metrics(method, payload):
    unknown_label = int(payload.meta["num_classes"])
    known_pred = method.predict(payload.test_known, unknown_label=unknown_label)
    open_pred = method.predict(payload.test_open, unknown_label=unknown_label)
    return evaluate_osr_predictions(
        known_split=payload.test_known,
        open_split=payload.test_open,
        known_pred=known_pred,
        open_pred=open_pred,
        known_class_names=payload.meta["class_names"],
        unknown_label_name="unknown",
    )


def _scalar_metrics(metrics):
    names = (
        "known_reject_rate",
        "unknown_precision",
        "unknown_recall",
        "unknown_f1",
        "osr_acc",
        "osr_macro_f1",
        "unknown_auroc",
    )
    return {k: float(metrics[k]) for k in names}


def run_controls(
    *,
    run_dir: Path,
    checkpoint: str,
    out_dir: Path,
    policy_path: Path,
    target_open_pa: str,
    surrogate_open_pa: str,
    device: str,
    batch_size: int,
    num_workers: int,
    data_root: str | None,
):
    t0 = time.time()
    policy = load_policy(policy_path)
    if checkpoint != policy["checkpoint"]:
        raise ValueError("checkpoint differs from frozen control policy")
    if device != policy["evaluator_device"]:
        raise ValueError("evaluator device differs from frozen control policy")
    if int(batch_size) != int(policy["batch_size"]):
        raise ValueError("batch size differs from frozen control policy")
    if int(num_workers) != int(policy["num_workers"]):
        raise ValueError("num_workers differs from frozen control policy")

    handle = load_backbone_run(
        run_dir=str(run_dir),
        checkpoint_tag=checkpoint,
        device=device,
    )
    contract = resolve_directional_l2o_contract(
        handle.config,
        evaluation_target=target_open_pa,
        evaluation_surrogate=surrogate_open_pa,
        model_class_names=handle.class_names,
    )

    directional_handle = copy.copy(handle)
    directional_handle.config = contract.target_config
    directional_handle.setup = None
    directional_handle.unknown_pas = [contract.evaluation_target]

    calibration_payload, calibration_extras = build_target_calibration_payload(
        directional_handle,
        batch_size=batch_size,
        num_workers=num_workers,
        data_root=data_root,
    )

    surrogate_open = build_surrogate_open_split(
        handle=directional_handle,
        surrogate_pa=contract.evaluation_surrogate,
        batch_size=batch_size,
        num_workers=num_workers,
        data_root=data_root,
        config_override=contract.surrogate_config,
    )

    dqn_cfg = policy["controls"]["dqn_ids_style"]
    known_cap = int(dqn_cfg["known_cap"])
    open_cap = int(dqn_cfg["open_cap"])
    if len(calibration_payload.val_known.y_true) < known_cap:
        raise ValueError("insufficient known validation samples for exact DQN cap")
    if len(surrogate_open.y_true) < open_cap:
        raise ValueError("insufficient surrogate validation samples for exact DQN cap")

    seed = int(calibration_payload.meta.get("seed", 0) or 0)
    known_cal = cap_split(calibration_payload.val_known, known_cap, seed + 101, True, "control_cap_known")
    open_cal = cap_split(surrogate_open, open_cap, seed + 202, False, "control_cap_surrogate")
    if len(known_cal.y_true) != known_cap or len(open_cal.y_true) != open_cap:
        raise ValueError("DQN control calibration caps are not exact")

    # Freeze/finalize both controls before target-test evaluation.
    dqn = make_dqn_control(policy)
    dqn.fit(calibration_payload, calibration={
        "calibration_mode": "external_surrogate_cap625",
        "calibration_known": known_cal,
        "calibration_open": open_cal,
    })

    varmax = make_varmax_control(policy)
    varmax_cal = build_varmax_calibration(calibration_payload, calibration_extras, policy)
    varmax.fit(calibration_payload, calibration=varmax_cal)

    # TARGET_TEST_FIRST_CONSUMPTION_AFTER_BOTH_CONTROLS_FROZEN
    # Only now materialize target known/test-open outputs for final evaluation.
    evaluation_payload, _ = build_osr_eval_bundle(
        directional_handle,
        batch_size=batch_size,
        num_workers=num_workers,
        pin_memory=True,
        data_root=data_root,
    )
    if evaluation_payload.meta["class_names"] != calibration_payload.meta["class_names"]:
        raise ValueError("evaluation class ordering drift after control freeze")
    if evaluation_payload.meta["unknown_pas"] != calibration_payload.meta["unknown_pas"]:
        raise ValueError("evaluation target identity drift after control freeze")

    dqn_metrics = _metrics(dqn, evaluation_payload)
    varmax_metrics = _metrics(varmax, evaluation_payload)

    dqn_fit = copy.deepcopy(getattr(dqn, "last_fit_summary_", {}))
    vm_best = copy.deepcopy(getattr(varmax, "best_sweep_result_", None)) or {}

    common = {
        "policy_id": policy["policy_id"],
        "run_name": handle.run_name,
        "run_dir": str(run_dir),
        "checkpoint": checkpoint,
        "target_unknown_pas": json.dumps([contract.evaluation_target]),
        "external_surrogate": contract.evaluation_surrogate,
        "backbone_training_target": contract.backbone_training_target,
        "backbone_training_surrogate": contract.backbone_training_surrogate,
        "backbone_canonical_excluded_pair": json.dumps(list(contract.canonical_excluded_pair)),
        "backbone_known_pas": json.dumps(list(contract.known_pas)),
        "directional_reuse": bool(contract.directional_reuse),
        "target_labels_used_for_tuning": False,
        "target_test_consumed_before_final_eval": False,
        "target_test_consumed_for_final_eval": True,
    }

    rows = [
        {
            **common,
            "control_id": dqn_cfg["method_id"],
            "control_family": "dqn_ids_style",
            "calibration_source": "external_surrogate_validation",
            "external_surrogate_consumed": True,
            "known_calibration_n": int(len(known_cal.y_true)),
            "open_calibration_n": int(len(open_cal.y_true)),
            "final_decision": "hard_dqn_argmax",
            "dqn_state_mode": dqn_cfg["state_mode"],
            "dqn_n_states_total": dqn_fit.get("n_states_total"),
            "dqn_n_anchor_high": dqn_fit.get("n_anchor_high"),
            "dqn_n_anchor_low": dqn_fit.get("n_anchor_low"),
            **_scalar_metrics(dqn_metrics),
        },
        {
            **common,
            "control_id": policy["controls"]["varmax"]["method_id"],
            "control_family": "varmax",
            "calibration_source": "known_validation_surrogate_all",
            "external_surrogate_consumed": False,
            "known_calibration_n": int(len(varmax_cal["calibration_known"].y_true)),
            "open_calibration_n": 0,
            "final_decision": "historical_varmax_acceptance_rule",
            "varmax_calibration_mode": "surrogate_all",
            "varmax_sweep_grid": "smoke",
            "varmax_selected_spec": vm_best.get("spec_name"),
            "varmax_selected_heldout_class": vm_best.get("heldout_class_name"),
            "varmax_selected_feasible": vm_best.get("feasible"),
            "varmax_no_feasible_solution": bool(getattr(varmax, "no_feasible_solution_", False)),
            **_scalar_metrics(varmax_metrics),
        },
    ]

    out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = out_dir / "control_summary.csv"
    pd.DataFrame(rows).to_csv(summary_path, index=False)
    metadata = {
        "schema": "padataset.l2o-control-eval-metadata.v1",
        "policy_id": policy["policy_id"],
        "target": contract.evaluation_target,
        "external_surrogate": contract.evaluation_surrogate,
        "canonical_pair": list(contract.canonical_excluded_pair),
        "known_pas": list(contract.known_pas),
        "controls_fitted_before_target_test": True,
        "target_labels_used_for_tuning": False,
        "target_test_consumed_before_final_eval": False,
        "target_test_consumed_for_final_eval": True,
        "dqn_known_calibration_n": int(len(known_cal.y_true)),
        "dqn_open_calibration_n": int(len(open_cal.y_true)),
        "varmax_external_surrogate_consumed": False,
        "elapsed_sec": time.time() - t0,
    }
    (out_dir / "control_eval_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return rows, metadata


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--target-open-pa", required=True)
    ap.add_argument("--surrogate-open-pa", required=True)
    ap.add_argument("--device", required=True)
    ap.add_argument("--batch-size", type=int, required=True)
    ap.add_argument("--num-workers", type=int, required=True)
    ap.add_argument("--data-root", default=None)
    args = ap.parse_args()
    rows, _ = run_controls(
        run_dir=Path(args.run_dir),
        checkpoint=args.checkpoint,
        out_dir=Path(args.out_dir),
        policy_path=Path(args.policy),
        target_open_pa=args.target_open_pa,
        surrogate_open_pa=args.surrogate_open_pa,
        device=args.device,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
        data_root=args.data_root,
    )
    print(pd.DataFrame(rows)[[
        "control_id",
        "target_unknown_pas",
        "external_surrogate",
        "known_reject_rate",
        "unknown_f1",
        "osr_macro_f1",
        "unknown_auroc",
    ]].to_string(index=False))


if __name__ == "__main__":
    main()
