#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import time
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import numpy as np
import pandas as pd
import torch

from osr_core import load_backbone_run, evaluate_osr_predictions
from evaluate import (
    build_osr_eval_bundle,
    collect_split_outputs_from_loader,
    _make_setup_from_run_config,
)
from prepData import build_data_from_setup
from dqn_osr import BandedGuardDQNOSR


def cap_split(split, cap: int, seed: int, stratify: bool, suffix: str):
    n = int(len(split.y_true))
    if cap <= 0 or n <= cap:
        return split

    rng = np.random.default_rng(seed)
    y = np.asarray(split.y_true)

    if stratify:
        classes = sorted([int(c) for c in np.unique(y) if int(c) >= 0])
        if len(classes) > 1:
            base = cap // len(classes)
            rem = cap % len(classes)
            idxs = []
            for j, cls in enumerate(classes):
                cls_idx = np.where(y == cls)[0]
                take = min(len(cls_idx), base + (1 if j < rem else 0))
                idxs.append(rng.choice(cls_idx, size=take, replace=False))
            idx = np.concatenate(idxs)
            if len(idx) < cap:
                remaining = np.setdiff1d(np.arange(n), idx, assume_unique=False)
                extra = rng.choice(remaining, size=cap - len(idx), replace=False)
                idx = np.concatenate([idx, extra])
            rng.shuffle(idx)
        else:
            idx = rng.choice(n, size=cap, replace=False)
    else:
        idx = rng.choice(n, size=cap, replace=False)

    idx = np.asarray(idx, dtype=int)

    meta = None
    if getattr(split, "sample_meta", None) is not None:
        meta = [split.sample_meta[int(i)] for i in idx]

    return split.__class__(
        split_name=f"{split.split_name}_{suffix}",
        y_true=split.y_true[idx],
        logits=split.logits[idx],
        features=split.features[idx],
        closed_pred=split.closed_pred[idx],
        probs=split.probs[idx],
        sample_meta=meta,
    )


def concat_splits(split_a, split_b, suffix: str):
    if split_a is None:
        return split_b
    if split_b is None:
        return split_a

    meta = None
    if getattr(split_a, "sample_meta", None) is not None or getattr(split_b, "sample_meta", None) is not None:
        meta_a = getattr(split_a, "sample_meta", None) or [None] * len(split_a.y_true)
        meta_b = getattr(split_b, "sample_meta", None) or [None] * len(split_b.y_true)
        meta = list(meta_a) + list(meta_b)

    return split_a.__class__(
        split_name=f"{split_a.split_name}_{split_b.split_name}_{suffix}",
        y_true=np.concatenate([split_a.y_true, split_b.y_true], axis=0),
        logits=np.concatenate([split_a.logits, split_b.logits], axis=0),
        features=np.concatenate([split_a.features, split_b.features], axis=0),
        closed_pred=np.concatenate([split_a.closed_pred, split_b.closed_pred], axis=0),
        probs=np.concatenate([split_a.probs, split_b.probs], axis=0),
        sample_meta=meta,
    )


def build_surrogate_open_split(handle, surrogate_pa: str, batch_size: int, num_workers: int, data_root=None):
    cfg = copy.deepcopy(handle.config)
    cfg["unknown_pas"] = [surrogate_pa]

    pas = cfg.get("pas", None)
    if pas is not None:
        cfg["pas"] = list(dict.fromkeys(list(pas) + [surrogate_pa]))

    setup = _make_setup_from_run_config(cfg, data_root=data_root)
    data = build_data_from_setup(
        setup,
        batch_size=batch_size,
        num_workers=num_workers,
        pin_memory=True,
    )

    try:
        loader = data.get("val_open_loader", None)
        if loader is None:
            raise RuntimeError("No val_open_loader produced for surrogate open split")

        return collect_split_outputs_from_loader(
            handle,
            loader,
            split_name=f"val_open_surrogate_{surrogate_pa}",
        )
    finally:
        try:
            if hasattr(data.get("dataset", None), "close"):
                data["dataset"].close()
        except Exception:
            pass
        del data
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


def make_method(mode: str):
    mode_map = {
        "var_energy": "var_energy",
        "all": "all",
        "two_of_three": "two_of_three",
        "any": "any",
    }
    if mode not in mode_map:
        raise ValueError(f"Unsupported mode={mode!r}; use var_energy, all, two_of_three, any")

    return BandedGuardDQNOSR(
        state_mode="softmax3",
        gamma=0.95,
        epsilon=1.0,
        epsilon_min=0.05,
        epsilon_decay=0.99,
        learning_rate=1e-3,
        memory_size=2000,
        batch_size=32,
        episodes=30,
        anchor_fraction=0.05,
        train_subsample_size=1250,
        centroid_update_threshold=0.75,
        seed=42,
        device="cpu",
        band_percentiles=(5.0, 95.0),
        top2_band_percentiles=(5.0, 95.0),
        band_accept_mode=mode_map[mode],
        band_weight=1.0,
        min_samples_per_class=5,
        fit_bands_on="predicted_class",
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--checkpoint", default="best_model")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--surrogate-open-pa", default="PA1")
    ap.add_argument("--mix-true-open", action="store_true")
    ap.add_argument("--surrogate-frac", type=float, default=0.5)
    ap.add_argument("--mode", default="var_energy")
    ap.add_argument("--decision-mode", choices=["hard", "score_threshold"], default="hard",
                    help="hard uses DQNGuard's built-in final decision; score_threshold sweeps unknown_score on calibration.")
    ap.add_argument("--max-known-reject-cal", type=float, default=0.25,
                    help="Known-only threshold budget. Cutoff is selected from known calibration scores only.")
    ap.add_argument("--known-cap", type=int, default=625)
    ap.add_argument("--open-cap", type=int, default=625)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--num-workers", type=int, default=0)
    ap.add_argument("--data-root", default=None)
    args = ap.parse_args()

    t0 = time.time()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    handle = load_backbone_run(
        run_dir=args.run_dir,
        checkpoint_tag=args.checkpoint,
        device=args.device,
    )

    payload, extras = build_osr_eval_bundle(
        handle,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
        pin_memory=True,
        data_root=args.data_root,
    )

    known_cal = payload.val_known
    surrogate_open = build_surrogate_open_split(
        handle=handle,
        surrogate_pa=args.surrogate_open_pa,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
        data_root=args.data_root,
    )

    seed = int(payload.meta.get("seed", 0) or 0)
    known_cal = cap_split(known_cal, args.known_cap, seed + 101, True, "cap_known")

    if args.mix_true_open:
        surrogate_n = int(round(float(args.open_cap) * float(args.surrogate_frac)))
        surrogate_n = max(0, min(int(args.open_cap), surrogate_n))
        true_n = int(args.open_cap) - surrogate_n

        surrogate_part = cap_split(
            surrogate_open,
            surrogate_n,
            seed + 202,
            False,
            f"cap_surrogate_{surrogate_n}",
        )
        true_part = cap_split(
            extras["val_open"],
            true_n,
            seed + 303,
            False,
            f"cap_trueopen_{true_n}",
        )
        open_cal = concat_splits(surrogate_part, true_part, "mixed_open")
        calibration_label = f"mixed_{args.surrogate_open_pa}_{surrogate_n}_true_{true_n}_{args.mode}_cap{args.open_cap}"
    else:
        open_cal = cap_split(surrogate_open, args.open_cap, seed + 202, False, "cap_surrogate_open")
        calibration_label = f"surrogate_{args.surrogate_open_pa}_{args.mode}_cap{args.open_cap}"

    method = make_method(args.mode)

    calibration = {
        "calibration_mode": calibration_label,
        "calibration_known": known_cal,
        "calibration_open": open_cal,
    }

    method.fit(payload, calibration=calibration)

    unknown_label = int(payload.meta["num_classes"])

    if args.decision_mode == "hard":
        known_pred = method.predict(payload.test_known, unknown_label=unknown_label)
        open_pred = method.predict(payload.test_open, unknown_label=unknown_label)
        selected_threshold = None
        threshold_known_reject_cal = None
        threshold_open_recall_cal = None

    else:
        # Use calibration data to pick an unknown_score threshold.
        cal_known_pred = method.predict(known_cal, unknown_label=unknown_label)
        cal_open_pred = method.predict(open_cal, unknown_label=unknown_label)

        cal_known_scores = cal_known_pred["unknown_score"]
        cal_open_scores = cal_open_pred["unknown_score"]

        # Deterministic known-only threshold.
        # No surrogate/open/target-unknown scores are used to choose this cutoff.
        budget = float(args.max_known_reject_cal)
        if not (0.0 <= budget <= 1.0):
            raise ValueError(f"--max-known-reject-cal must be in [0,1], got {budget}")

        q = 100.0 * (1.0 - budget)
        selected_threshold = float(np.percentile(cal_known_scores, q))
        threshold_known_reject_cal = float(np.mean(cal_known_scores >= selected_threshold))

        # Diagnostic only. This does not determine the threshold.
        threshold_open_recall_cal = float(np.mean(cal_open_scores >= selected_threshold))

        known_base = method.predict(payload.test_known, unknown_label=unknown_label)
        open_base = method.predict(payload.test_open, unknown_label=unknown_label)

        def apply_score_threshold(split, base_pred, thr):
            is_unknown = base_pred["unknown_score"] >= thr
            final_pred = base_pred["closed_pred"].astype(int).copy()
            final_pred[is_unknown] = int(unknown_label)
            out = dict(base_pred)
            out["is_unknown"] = is_unknown.astype(bool)
            out["final_pred"] = final_pred.astype(int)
            return out

        known_pred = apply_score_threshold(payload.test_known, known_base, selected_threshold)
        open_pred = apply_score_threshold(payload.test_open, open_base, selected_threshold)

    metrics = evaluate_osr_predictions(
        known_split=payload.test_known,
        open_split=payload.test_open,
        known_pred=known_pred,
        open_pred=open_pred,
        known_class_names=payload.meta["class_names"],
        unknown_label_name="unknown",
    )

    params = method.get_params()
    fit_summary = params.get("last_fit_summary", {}) or {}

    row = {
        "run_name": handle.run_name,
        "run_dir": args.run_dir,
        "checkpoint": args.checkpoint,
        "method": f"dqn_banded_guard_{args.mode}_{calibration_label}_softmax3",
        "target_unknown_pas": json.dumps(handle.config.get("unknown_pas", [])),
        "surrogate_open_pa": args.surrogate_open_pa,
        "mix_true_open": bool(args.mix_true_open),
        "surrogate_frac": float(args.surrogate_frac),
        "band_accept_mode": args.mode,
        "decision_mode": args.decision_mode,
        "score_threshold": selected_threshold,
        "threshold_known_reject_cal": threshold_known_reject_cal,
        "max_known_reject_cal": float(args.max_known_reject_cal),
        "threshold_open_recall_cal": threshold_open_recall_cal,
        "dqn_n_known_calibration": int(len(known_cal.y_true)),
        "dqn_n_open_calibration": int(len(open_cal.y_true)),
        "dqn_n_states_total": fit_summary.get("n_states_total"),
        "dqn_n_anchor_high": fit_summary.get("n_anchor_high"),
        "dqn_n_anchor_low": fit_summary.get("n_anchor_low"),
        **metrics,
        "elapsed_sec": time.time() - t0,
    }

    df = pd.DataFrame([row])
    csv_path = out_dir / "osr_summary.csv"
    df.to_csv(csv_path, index=False)

    print(df[[
        "method",
        "target_unknown_pas",
        "surrogate_open_pa",
        "mix_true_open",
        "surrogate_frac",
        "dqn_n_known_calibration",
        "dqn_n_open_calibration",
        "known_reject_rate",
        "unknown_precision",
        "unknown_recall",
        "unknown_f1",
        "osr_acc",
        "osr_macro_f1",
        "unknown_auroc",
    ]].to_string(index=False))

    print("\nconfusion:")
    print(row["osr_confusion_matrix"])
    print("\nWrote:", csv_path)


if __name__ == "__main__":
    main()
