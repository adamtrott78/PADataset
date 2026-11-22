#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from evaluate import _make_setup_from_run_config, collect_split_outputs_from_loader
from prepData import build_data_from_setup
from osr_core import BackbonePayload, SplitOutputs, load_backbone_run, evaluate_osr_predictions
from experiments.l2o_directional_contract import resolve_directional_l2o_contract
from experiments.pa_eval_dqn_guard_surrogate_open import cap_split, make_method


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def save_split(path: Path, split: SplitOutputs) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("wb") as f:
        np.savez(
            f,
            split_name=np.asarray(split.split_name),
            y_true=split.y_true,
            logits=split.logits,
            features=split.features,
            probs=split.probs,
            closed_pred=split.closed_pred,
        )
    os.replace(tmp, path)


def load_split(path: Path) -> SplitOutputs:
    with np.load(path, allow_pickle=False) as z:
        return SplitOutputs(
            split_name=str(z["split_name"].item()),
            y_true=z["y_true"],
            logits=z["logits"],
            features=z["features"],
            probs=z["probs"],
            closed_pred=z["closed_pred"],
            sample_meta=None,
        )


def collect_and_cache(handle, loader, split_name: str, path: Path) -> SplitOutputs:
    if path.is_file():
        out = load_split(path)
        print(f"PAIR_CACHE | split={split_name} | status=HIT | n={len(out.y_true)}", flush=True)
        return out

    print(f"PAIR_CACHE | split={split_name} | status=COLLECT_START", flush=True)
    out = collect_split_outputs_from_loader(handle, loader, split_name)
    if out is None:
        raise RuntimeError(f"required split is empty: {split_name}")
    save_split(path, out)
    print(f"PAIR_CACHE | split={split_name} | status=COLLECT_DONE | n={len(out.y_true)} | path={path}", flush=True)
    return out


def build_data_for_cfg(cfg, data_root: str, batch_size: int, num_workers: int):
    setup = _make_setup_from_run_config(cfg, data_root=data_root)
    return build_data_from_setup(
        setup,
        batch_size=batch_size,
        num_workers=num_workers,
        pin_memory=True,
    )


def close_data(data) -> None:
    try:
        if hasattr(data.get("dataset", None), "close"):
            data["dataset"].close()
    finally:
        del data


def apply_score_threshold(split, base_pred, threshold, unknown_label: int):
    is_unknown = base_pred["unknown_score"] >= threshold
    final_pred = base_pred["closed_pred"].astype(int).copy()
    final_pred[is_unknown] = int(unknown_label)
    out = dict(base_pred)
    out["is_unknown"] = is_unknown.astype(bool)
    out["final_pred"] = final_pred.astype(int)
    return out


def evaluate_direction(
    *,
    handle,
    known_val,
    known_test,
    target_test,
    surrogate_val,
    target: str,
    surrogate: str,
    mode: str,
    decision_mode: str,
    max_known_reject_cal: float,
    known_cap: int,
    open_cap: int,
    out_dir: Path,
):
    seed = int(handle.config.get("seed", 0) or 0)
    known_cal = cap_split(known_val, known_cap, seed + 101, True, "cap_known")
    open_cal = cap_split(surrogate_val, open_cap, seed + 202, False, "cap_surrogate_open")

    payload = BackbonePayload(
        meta={
            "run_name": handle.run_name,
            "run_dir": handle.run_dir,
            "checkpoint_tag": handle.checkpoint_tag,
            "unknown_pas": [target],
            "class_names": handle.class_names,
            "num_classes": handle.num_classes,
            "cache_len": handle.config.get("cache_len"),
            "seed": handle.config.get("seed"),
            "epochs": handle.config.get("epochs"),
            "source_type": handle.config.get("source_type", "digital"),
            "source_name": handle.config.get("source_name", "pilot_noisy_torch"),
            "dataset_tag": handle.config.get("dataset_tag"),
            "noise_tag": handle.config.get("noise_tag"),
        },
        val_known=known_val,
        test_known=known_test,
        test_open=target_test,
    )

    method = make_method(mode)
    calibration = {
        "calibration_mode": f"surrogate_{surrogate}_{mode}_cap{open_cap}",
        "calibration_known": known_cal,
        "calibration_open": open_cal,
    }
    method.fit(payload, calibration=calibration)
    unknown_label = int(payload.meta["num_classes"])

    selected_threshold = None
    threshold_known_reject_cal = None
    threshold_open_recall_cal = None

    if decision_mode == "hard":
        known_pred = method.predict(known_test, unknown_label=unknown_label)
        open_pred = method.predict(target_test, unknown_label=unknown_label)
    else:
        cal_known_pred = method.predict(known_cal, unknown_label=unknown_label)
        cal_open_pred = method.predict(open_cal, unknown_label=unknown_label)

        budget = float(max_known_reject_cal)
        if not 0.0 <= budget <= 1.0:
            raise ValueError("max_known_reject_cal must be in [0,1]")
        selected_threshold = float(np.percentile(cal_known_pred["unknown_score"], 100.0 * (1.0 - budget)))
        threshold_known_reject_cal = float(np.mean(cal_known_pred["unknown_score"] >= selected_threshold))
        threshold_open_recall_cal = float(np.mean(cal_open_pred["unknown_score"] >= selected_threshold))

        known_base = method.predict(known_test, unknown_label=unknown_label)
        open_base = method.predict(target_test, unknown_label=unknown_label)
        known_pred = apply_score_threshold(known_test, known_base, selected_threshold, unknown_label)
        open_pred = apply_score_threshold(target_test, open_base, selected_threshold, unknown_label)

    metrics = evaluate_osr_predictions(
        known_split=known_test,
        open_split=target_test,
        known_pred=known_pred,
        open_pred=open_pred,
        known_class_names=handle.class_names,
        unknown_label_name="unknown",
    )
    fit_summary = (method.get_params().get("last_fit_summary") or {})

    row = {
        "run_name": handle.run_name,
        "run_dir": handle.run_dir,
        "checkpoint": handle.checkpoint_tag,
        "method": f"dqn_banded_guard_{mode}_surrogate_{surrogate}_{mode}_cap{open_cap}_softmax3",
        "target_unknown_pas": json.dumps([target]),
        "surrogate_open_pa": surrogate,
        "backbone_training_target": handle.config.get("target_unknown_pa"),
        "backbone_training_surrogate": handle.config.get("surrogate_open_pa"),
        "backbone_canonical_excluded_pair": json.dumps(sorted([target, surrogate])),
        "backbone_known_pas": json.dumps(list(handle.config.get("known_pas_l2o") or [])),
        "directional_reuse": target != handle.config.get("target_unknown_pa"),
        "target_labels_used_for_tuning": False,
        "mix_true_open": False,
        "surrogate_frac": 0.5,
        "band_accept_mode": mode,
        "decision_mode": decision_mode,
        "score_threshold": selected_threshold,
        "threshold_known_reject_cal": threshold_known_reject_cal,
        "max_known_reject_cal": float(max_known_reject_cal),
        "threshold_open_recall_cal": threshold_open_recall_cal,
        "dqn_n_known_calibration": int(len(known_cal.y_true)),
        "dqn_n_open_calibration": int(len(open_cal.y_true)),
        "dqn_n_states_total": fit_summary.get("n_states_total"),
        "dqn_n_anchor_high": fit_summary.get("n_anchor_high"),
        "dqn_n_anchor_low": fit_summary.get("n_anchor_low"),
        **metrics,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([row]).to_csv(out_dir / "osr_summary.csv", index=False)
    (out_dir / "pair_cached_result.json").write_text(json.dumps(row, indent=2, sort_keys=True, default=str) + "\n")
    print(
        "PAIR_OSR_RESULT "
        f"| direction={target}<-{surrogate} "
        f"| unknown_f1={row['unknown_f1']:.12f} "
        f"| unknown_auroc={row['unknown_auroc']:.12f} "
        f"| known_reject_rate={row['known_reject_rate']:.12f} "
        f"| osr_acc={row['osr_acc']:.12f}",
        flush=True,
    )
    return row


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--checkpoint", default="best_model")
    ap.add_argument("--pair-a", required=True)
    ap.add_argument("--pair-b", required=True)
    ap.add_argument("--cache-dir", required=True)
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--num-workers", type=int, default=0)
    ap.add_argument("--data-root", required=True)
    ap.add_argument("--mode", default="var_energy")
    ap.add_argument("--decision-mode", choices=["hard", "score_threshold"], default="score_threshold")
    ap.add_argument("--max-known-reject-cal", type=float, default=0.05)
    ap.add_argument("--known-cap", type=int, default=625)
    ap.add_argument("--open-cap", type=int, default=625)
    args = ap.parse_args()

    if args.device != "cpu":
        raise ValueError("pair-cached local evaluator currently requires --device cpu")
    if torch.cuda.is_available():
        raise RuntimeError("CUDA must be hidden for the local pair-cached CPU evaluator")

    pair = tuple(sorted((args.pair_a, args.pair_b)))
    if pair[0] == pair[1]:
        raise ValueError("pair members must differ")

    handle = load_backbone_run(args.run_dir, args.checkpoint, device="cpu")
    contract_ab = resolve_directional_l2o_contract(
        handle.config,
        evaluation_target=args.pair_a,
        evaluation_surrogate=args.pair_b,
        model_class_names=handle.class_names,
    )
    contract_ba = resolve_directional_l2o_contract(
        handle.config,
        evaluation_target=args.pair_b,
        evaluation_surrogate=args.pair_a,
        model_class_names=handle.class_names,
    )

    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    out_root = Path(args.out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    checkpoint_path = Path(handle.checkpoint_path)
    config_path = Path(handle.run_dir) / "config.json"
    provenance = {
        "schema": "padataset.l2o-pair-feature-cache.v1",
        "pair": list(pair),
        "checkpoint": handle.checkpoint_tag,
        "checkpoint_sha256": sha256_file(checkpoint_path),
        "config_sha256": sha256_file(config_path),
        "data_root": str(Path(args.data_root).resolve()),
        "batch_size": int(args.batch_size),
        "num_workers": int(args.num_workers),
        "device": "cpu",
        "target_partition_open_val_frac": 0.15,
        "surrogate_partition_open_val_frac": 0.15,
    }
    manifest_path = cache_dir / "manifest.json"
    if manifest_path.is_file():
        existing = json.loads(manifest_path.read_text())
        if existing != provenance:
            raise RuntimeError("pair cache provenance mismatch")
    else:
        manifest_path.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n")

    paths = {
        "val_known": cache_dir / "val_known.npz",
        "test_known": cache_dir / "test_known.npz",
        f"val_open_{args.pair_a}": cache_dir / f"val_open_{args.pair_a}.npz",
        f"test_open_{args.pair_a}": cache_dir / f"test_open_{args.pair_a}.npz",
        f"val_open_{args.pair_b}": cache_dir / f"val_open_{args.pair_b}.npz",
        f"test_open_{args.pair_b}": cache_dir / f"test_open_{args.pair_b}.npz",
    }

    # First pair member: collect shared known splits plus this PA's open splits.
    handle_a = copy.copy(handle)
    handle_a.config = contract_ab.target_config
    handle_a.setup = None
    handle_a.unknown_pas = [args.pair_a]
    data_a = build_data_for_cfg(handle_a.config, args.data_root, args.batch_size, args.num_workers)
    try:
        known_val = collect_and_cache(handle_a, data_a["val_loader"], "val_known", paths["val_known"])
        known_test = collect_and_cache(handle_a, data_a["test_known_loader"], "test_known", paths["test_known"])
        val_open_a = collect_and_cache(handle_a, data_a["val_open_loader"], f"val_open_{args.pair_a}", paths[f"val_open_{args.pair_a}"])
        test_open_a = collect_and_cache(handle_a, data_a["test_open_loader"], f"test_open_{args.pair_a}", paths[f"test_open_{args.pair_a}"])
    finally:
        close_data(data_a)

    # Second member: only its open splits; known outputs are identical and reused.
    handle_b = copy.copy(handle)
    handle_b.config = contract_ba.target_config
    handle_b.setup = None
    handle_b.unknown_pas = [args.pair_b]
    data_b = build_data_for_cfg(handle_b.config, args.data_root, args.batch_size, args.num_workers)
    try:
        val_open_b = collect_and_cache(handle_b, data_b["val_open_loader"], f"val_open_{args.pair_b}", paths[f"val_open_{args.pair_b}"])
        test_open_b = collect_and_cache(handle_b, data_b["test_open_loader"], f"test_open_{args.pair_b}", paths[f"test_open_{args.pair_b}"])
    finally:
        close_data(data_b)

    t0 = time.time()
    rows = []
    rows.append(evaluate_direction(
        handle=handle,
        known_val=known_val,
        known_test=known_test,
        target_test=test_open_a,
        surrogate_val=val_open_b,
        target=args.pair_a,
        surrogate=args.pair_b,
        mode=args.mode,
        decision_mode=args.decision_mode,
        max_known_reject_cal=args.max_known_reject_cal,
        known_cap=args.known_cap,
        open_cap=args.open_cap,
        out_dir=out_root / f"target{args.pair_a}_sur{args.pair_b}",
    ))
    rows.append(evaluate_direction(
        handle=handle,
        known_val=known_val,
        known_test=known_test,
        target_test=test_open_b,
        surrogate_val=val_open_a,
        target=args.pair_b,
        surrogate=args.pair_a,
        mode=args.mode,
        decision_mode=args.decision_mode,
        max_known_reject_cal=args.max_known_reject_cal,
        known_cap=args.known_cap,
        open_cap=args.open_cap,
        out_dir=out_root / f"target{args.pair_b}_sur{args.pair_a}",
    ))

    pd.DataFrame(rows).to_csv(out_root / "pair_osr_summary.csv", index=False)
    print(f"PAIR_OSR_COMPLETE | pair={pair[0]}-{pair[1]} | elapsed_postcache_sec={time.time()-t0:.3f}", flush=True)


if __name__ == "__main__":
    main()
