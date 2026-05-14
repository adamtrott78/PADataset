#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np
import pandas as pd
import tensorflow as tf

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from osr_core import SplitOutputs, BackbonePayload, _make_setup_from_config, evaluate_osr_predictions
from prepData import build_data_from_setup
from dqn_osr import BandedGuardDQNOSR


def load_shreyash_module():
    path = REPO_ROOT / "experiments" / "train_shreyash_keras_pa_stream.py"
    spec = importlib.util.spec_from_file_location("shreyash_stream", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def cap_split(split, cap: int, seed: int, stratify: bool, suffix: str):
    n = int(len(split.y_true))
    if cap <= 0 or n <= cap:
        return split

    rng = np.random.default_rng(seed)
    y = np.asarray(split.y_true)

    if stratify:
        classes = sorted([int(c) for c in np.unique(y) if int(c) >= 0])
        base = cap // max(1, len(classes))
        rem = cap % max(1, len(classes))
        idxs = []
        for j, cls in enumerate(classes):
            cls_idx = np.where(y == cls)[0]
            take = min(len(cls_idx), base + (1 if j < rem else 0))
            idxs.append(rng.choice(cls_idx, size=take, replace=False))
        idx = np.concatenate(idxs) if idxs else np.array([], dtype=int)
        if len(idx) < cap:
            remaining = np.setdiff1d(np.arange(n), idx, assume_unique=False)
            extra = rng.choice(remaining, size=min(cap - len(idx), len(remaining)), replace=False)
            idx = np.concatenate([idx, extra])
        rng.shuffle(idx)
    else:
        idx = rng.choice(n, size=min(cap, n), replace=False)

    idx = np.asarray(idx, dtype=int)
    return SplitOutputs(
        split_name=f"{split.split_name}_{suffix}",
        y_true=split.y_true[idx],
        logits=split.logits[idx],
        features=split.features[idx],
        closed_pred=split.closed_pred[idx],
        probs=split.probs[idx],
        sample_meta=None if split.sample_meta is None else [split.sample_meta[int(i)] for i in idx],
    )


def make_method():
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
        band_accept_mode="var_energy",
        band_weight=1.0,
        min_samples_per_class=5,
        fit_bands_on="predicted_class",
    )


def build_data(cfg, data_root, batch_size):
    cfg = copy.deepcopy(cfg)
    if data_root is not None:
        cfg["root"] = data_root
    setup = _make_setup_from_config(cfg, return_metadata=False)
    data = build_data_from_setup(
        setup,
        batch_size=batch_size,
        num_workers=0,
        pin_memory=False,
    )
    return data


def close_data(data):
    try:
        if hasattr(data.get("dataset", None), "close"):
            data["dataset"].close()
    except Exception:
        pass


def make_logit_probe(model):
    softmax_layer = model.get_layer("softmax")
    pre_softmax_model = tf.keras.Model(inputs=model.input, outputs=softmax_layer.input)
    W, b = softmax_layer.get_weights()
    return pre_softmax_model, W.astype("float32"), b.astype("float32")


def collect_split(model, pre_model, W, b, dataset, split_name, num_classes, batch_size, shrey):
    seq_x = shrey.TorchDatasetSequence(
        dataset=dataset,
        batch_size=batch_size,
        num_classes=num_classes,
        shuffle=False,
        return_y=False,
    )
    probs = model.predict(seq_x, verbose=1).astype("float32")
    features = pre_model.predict(seq_x, verbose=0).astype("float32")
    logits = (features @ W + b).astype("float32")

    seq_y = shrey.TorchDatasetSequence(
        dataset=dataset,
        batch_size=batch_size,
        num_classes=num_classes,
        shuffle=False,
        return_y=True,
    )
    y = seq_y.labels()

    return SplitOutputs(
        split_name=split_name,
        y_true=y.astype(int),
        logits=logits,
        features=features,
        closed_pred=np.argmax(probs, axis=1).astype(int),
        probs=probs,
        sample_meta=None,
    )


def apply_score_threshold(base_pred, threshold, unknown_label):
    is_unknown = base_pred["unknown_score"] >= threshold
    final_pred = base_pred["closed_pred"].astype(int).copy()
    final_pred[is_unknown] = int(unknown_label)

    out = dict(base_pred)
    out["is_unknown"] = is_unknown.astype(bool)
    out["final_pred"] = final_pred.astype(int)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--model-file", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--surrogate-open-pa", default="PA1")
    ap.add_argument("--known-cap", type=int, default=625)
    ap.add_argument("--open-cap", type=int, default=625)
    ap.add_argument("--max-known-reject-cal", type=float, default=0.05)
    ap.add_argument("--batch-size", type=int, default=512)
    ap.add_argument("--data-root", default=None)
    args = ap.parse_args()

    t0 = time.time()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    shrey = load_shreyash_module()

    run_dir = Path(args.run_dir)
    cfg = json.loads((run_dir / "config.json").read_text())
    run_name = cfg.get("run_name", run_dir.name)

    model = tf.keras.models.load_model(
        args.model_file,
        custom_objects={"custom_loss_with_entropy": shrey.custom_loss_with_entropy},
    )
    pre_model, W, b = make_logit_probe(model)

    data = build_data(cfg, args.data_root, args.batch_size)
    try:
        class_names = list(data["meta"]["class_names"])
        num_classes = int(data["meta"]["num_classes"])

        val_known = collect_split(model, pre_model, W, b, data["val_ds"], "val_known", num_classes, args.batch_size, shrey)
        test_known = collect_split(model, pre_model, W, b, data["test_known_ds"], "test_known", num_classes, args.batch_size, shrey)
        test_open = collect_split(model, pre_model, W, b, data["test_open_ds"], "test_open", num_classes, args.batch_size, shrey)
    finally:
        close_data(data)

    # Build PA1 surrogate-open split.
    sur_cfg = copy.deepcopy(cfg)
    sur_cfg["unknown_pas"] = [args.surrogate_open_pa]
    pas = list(sur_cfg.get("pas") or [])
    if args.surrogate_open_pa not in pas:
        pas.append(args.surrogate_open_pa)
    sur_cfg["pas"] = pas

    sur_data = build_data(sur_cfg, args.data_root, args.batch_size)
    try:
        surrogate_open = collect_split(
            model, pre_model, W, b,
            sur_data["val_open_ds"],
            f"val_open_surrogate_{args.surrogate_open_pa}",
            num_classes,
            args.batch_size,
            shrey,
        )
    finally:
        close_data(sur_data)

    payload = BackbonePayload(
        meta={
            "run_name": run_name,
            "run_dir": str(run_dir),
            "checkpoint_tag": Path(args.model_file).stem,
            "unknown_pas": list(cfg.get("unknown_pas", [])),
            "class_names": class_names,
            "num_classes": num_classes,
            "cache_len": cfg.get("cache_len"),
            "seed": cfg.get("seed", 0),
            "source_type": cfg.get("source_type"),
            "source_name": cfg.get("source_name"),
            "dataset_tag": cfg.get("dataset_tag"),
            "noise_tag": cfg.get("noise_tag"),
        },
        val_known=val_known,
        test_known=test_known,
        test_open=test_open,
    )

    seed = int(cfg.get("seed", 0) or 0)
    known_cal = cap_split(val_known, args.known_cap, seed + 101, True, "cap_known")
    open_cal = cap_split(surrogate_open, args.open_cap, seed + 202, False, "cap_surrogate_open")

    method = make_method()
    method.fit(payload, calibration={
        "calibration_mode": f"shreyash_keras_surrogate_{args.surrogate_open_pa}_knownonly",
        "calibration_known": known_cal,
        "calibration_open": open_cal,
    })

    unknown_label = int(num_classes)

    cal_known_pred = method.predict(known_cal, unknown_label=unknown_label)
    cal_open_pred = method.predict(open_cal, unknown_label=unknown_label)

    cal_known_scores = cal_known_pred["unknown_score"]
    cal_open_scores = cal_open_pred["unknown_score"]

    budget = float(args.max_known_reject_cal)
    threshold = float(np.percentile(cal_known_scores, 100.0 * (1.0 - budget)))

    threshold_known_reject_cal = float(np.mean(cal_known_scores >= threshold))
    threshold_open_recall_cal = float(np.mean(cal_open_scores >= threshold))

    known_base = method.predict(test_known, unknown_label=unknown_label)
    open_base = method.predict(test_open, unknown_label=unknown_label)

    known_pred = apply_score_threshold(known_base, threshold, unknown_label)
    open_pred = apply_score_threshold(open_base, threshold, unknown_label)

    metrics = evaluate_osr_predictions(
        known_split=test_known,
        open_split=test_open,
        known_pred=known_pred,
        open_pred=open_pred,
        known_class_names=class_names,
        unknown_label_name="unknown",
    )

    params = method.get_params()
    fit_summary = params.get("last_fit_summary", {}) or {}

    row = {
        "run_name": run_name,
        "run_dir": str(run_dir),
        "checkpoint": str(args.model_file),
        "method": f"shreyash_keras_dqn_banded_guard_var_energy_PA1surrogate_knownonly_budget{budget}",
        "target_unknown_pas": json.dumps(cfg.get("unknown_pas", [])),
        "surrogate_open_pa": args.surrogate_open_pa,
        "decision_mode": "score_threshold",
        "max_known_reject_cal": budget,
        "score_threshold": threshold,
        "threshold_known_reject_cal": threshold_known_reject_cal,
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
        "run_name",
        "target_unknown_pas",
        "method",
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
