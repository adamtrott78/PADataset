#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import argparse
import json
import os
import sys
import time

# Use GPU by default for PA-scale experiments.
# Set CUDA_VISIBLE_DEVICES externally to choose a device, e.g. CUDA_VISIBLE_DEVICES=0.
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")

import h5py
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import (
    Conv1D, MaxPooling1D, GlobalAveragePooling1D,
    Dense, Dropout, Input, ReLU, BatchNormalization,
)
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.regularizers import l2
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, CSVLogger, ModelCheckpoint
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import accuracy_score, f1_score

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from osr_core import _make_setup_from_config
from prepData import build_data_from_setup


def custom_loss_with_entropy(y_true, y_pred):
    cross_entropy = tf.keras.losses.categorical_crossentropy(y_true, y_pred)
    epsilon = 1e-7
    y_pred = tf.clip_by_value(y_pred, epsilon, 1.0 - epsilon)
    entropy = -tf.reduce_sum(y_pred * tf.math.log(y_pred), axis=-1)
    return cross_entropy + 1.0 * entropy


def make_model(input_shape, num_classes):
    inputs = Input(shape=input_shape)

    x = Conv1D(filters=8, kernel_size=3, padding="same", kernel_regularizer=l2(0.005))(inputs)
    x = ReLU()(x)
    x = BatchNormalization()(x)
    x = MaxPooling1D(pool_size=2)(x)

    x = Conv1D(filters=24, kernel_size=3, padding="same", kernel_regularizer=l2(0.005))(x)
    x = ReLU()(x)
    x = BatchNormalization()(x)
    x = MaxPooling1D(pool_size=2)(x)

    x = Conv1D(filters=32, kernel_size=3, padding="same", kernel_regularizer=l2(0.005))(x)
    x = ReLU()(x)
    x = BatchNormalization()(x)
    x = MaxPooling1D(pool_size=2)(x)

    x = GlobalAveragePooling1D()(x)
    x = Dense(48, kernel_regularizer=l2(0.005), name="features48")(x)
    x = ReLU()(x)
    x = Dropout(0.5)(x)

    outputs = Dense(num_classes, activation="softmax", name="softmax")(x)

    model = Model(inputs=inputs, outputs=outputs)
    model.compile(
        optimizer=Adam(learning_rate=1e-5, clipnorm=1.0),
        loss=custom_loss_with_entropy,
        metrics=["accuracy"],
    )
    return model


def collect_loader_numpy(loader, max_batches=None):
    xs, ys = [], []
    metas = []

    for bi, batch in enumerate(loader):
        if max_batches is not None and bi >= max_batches:
            break

        if len(batch) >= 3:
            x, y, meta = batch[:3]
            metas.append(meta)
        else:
            x, y = batch[:2]

        x = x.detach().cpu().numpy().astype("float32")
        y = y.detach().cpu().numpy().astype("int64")

        # Current PA cache is [N, 8, 16384]. Keras Conv1D wants [N, T, C].
        if x.ndim != 3:
            raise ValueError(f"Expected x ndim 3, got {x.shape}")
        x = np.transpose(x, (0, 2, 1))

        xs.append(x)
        ys.append(y)

    X = np.concatenate(xs, axis=0)
    y = np.concatenate(ys, axis=0)
    return X, y


def softmax_stats(probs):
    p1 = probs.max(axis=1)
    sorted_probs = np.sort(probs, axis=1)
    gap = sorted_probs[:, -1] - sorted_probs[:, -2]
    ent = -np.sum(np.clip(probs, 1e-12, 1.0) * np.log(np.clip(probs, 1e-12, 1.0)), axis=1)
    return p1, gap, ent


def anchor_metrics(known_probs, open_probs, anchor_fraction=0.05):
    known_p1, _, _ = softmax_stats(known_probs)
    open_p1, _, _ = softmax_stats(open_probs)

    p1 = np.concatenate([known_p1, open_p1])
    is_open = np.concatenate([
        np.zeros(len(known_p1), dtype=bool),
        np.ones(len(open_p1), dtype=bool),
    ])

    k = max(1, int(anchor_fraction * len(p1)))
    order = np.argsort(p1)
    low_idx = order[:k]
    high_idx = order[-k:]

    return {
        "anchor_fraction": float(anchor_fraction),
        "anchor_k": int(k),
        "anchor_low_open_frac": float(is_open[low_idx].mean()),
        "anchor_high_known_frac": float((~is_open[high_idx]).mean()),
        "anchor_high_open_frac": float(is_open[high_idx].mean()),
        "known_p1_mean": float(known_p1.mean()),
        "open_p1_mean": float(open_p1.mean()),
    }


def save_npz_bundle(out_dir, model, X_train, y_train, X_val, y_val, X_test_known, y_test_known, X_test_open, y_test_open, class_names, cfg, history_dict):
    out_dir = Path(out_dir)
    probs_train = model.predict(X_train, batch_size=512, verbose=0)
    probs_val = model.predict(X_val, batch_size=512, verbose=0)
    probs_test_known = model.predict(X_test_known, batch_size=512, verbose=0)
    probs_test_open = model.predict(X_test_open, batch_size=512, verbose=0)

    np.savez_compressed(
        out_dir / "softmax_outputs.npz",
        train_probs=probs_train,
        train_y=y_train,
        val_known_probs=probs_val,
        val_known_y=y_val,
        test_known_probs=probs_test_known,
        test_known_y=y_test_known,
        test_open_probs=probs_test_open,
        test_open_y=y_test_open,
        class_names=np.array(class_names, dtype=object),
    )

    val_pred = probs_val.argmax(axis=1)
    known_pred = probs_test_known.argmax(axis=1)

    summary = {
        "run_name": cfg.get("run_name"),
        "model_family": "shreyash_keras_cnn",
        "class_names": class_names,
        "num_classes": len(class_names),
        "keras_recipe": {
            "conv_filters": [8, 24, 32],
            "kernel_size": 3,
            "dense": 48,
            "dropout": 0.5,
            "l2": 0.005,
            "optimizer": "Adam",
            "lr": 1e-5,
            "clipnorm": 1.0,
            "loss": "categorical_crossentropy + entropy",
            "batch_size": 500,
            "early_stopping_monitor": "val_loss",
            "early_stopping_patience": 10,
            "reduce_lr_patience": 5,
            "reduce_lr_factor": 0.5,
            "reduce_lr_min_lr": 1e-7,
        },
        "val_acc": float(accuracy_score(y_val, val_pred)),
        "val_macro_f1": float(f1_score(y_val, val_pred, average="macro")),
        "test_known_acc": float(accuracy_score(y_test_known, known_pred)),
        "test_known_macro_f1": float(f1_score(y_test_known, known_pred, average="macro")),
        "history": history_dict,
    }

    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cfg", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--data-root", default="data")
    ap.add_argument("--epochs", type=int, default=500)
    ap.add_argument("--batch-size", type=int, default=500)
    ap.add_argument("--collect-batch-size", type=int, default=128)
    ap.add_argument("--num-workers", type=int, default=0)
    ap.add_argument("--smoke-max-batches", type=int, default=None)
    args = ap.parse_args()

    cfg = json.loads(Path(args.cfg).read_text())
    run_name = cfg.get("run_name", Path(args.cfg).stem)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "config.json").write_text(json.dumps(cfg, indent=2))

    print(f"SHREYASH_KERAS_START | run_name={run_name} | cfg={args.cfg} | out_dir={out_dir}", flush=True)

    setup = _make_setup_from_config(cfg, return_metadata=True)
    setup.root = args.data_root

    data = build_data_from_setup(
        setup,
        batch_size=args.collect_batch_size,
        num_workers=args.num_workers,
        pin_memory=False,
    )

    class_names = list(data["meta"]["class_names"])
    num_classes = int(data["meta"]["num_classes"])

    print("COLLECT train", flush=True)
    X_train, y_train = collect_loader_numpy(data["train_loader"], max_batches=args.smoke_max_batches)
    print("COLLECT val_known", flush=True)
    X_val, y_val = collect_loader_numpy(data["val_loader"], max_batches=args.smoke_max_batches)
    print("COLLECT test_known", flush=True)
    X_test_known, y_test_known = collect_loader_numpy(data["test_known_loader"], max_batches=args.smoke_max_batches)
    print("COLLECT test_open", flush=True)
    X_test_open, y_test_open = collect_loader_numpy(data["test_open_loader"], max_batches=args.smoke_max_batches)

    print("SHAPES", {
        "X_train": X_train.shape,
        "X_val": X_val.shape,
        "X_test_known": X_test_known.shape,
        "X_test_open": X_test_open.shape,
        "num_classes": num_classes,
        "class_names": class_names,
    }, flush=True)

    y_train_cat = tf.keras.utils.to_categorical(y_train, num_classes=num_classes)
    y_val_cat = tf.keras.utils.to_categorical(y_val, num_classes=num_classes)

    weights = compute_class_weight(
        class_weight="balanced",
        classes=np.arange(num_classes),
        y=y_train,
    )
    class_weights = {i: float(w) for i, w in enumerate(weights)}
    print("CLASS_WEIGHTS", class_weights, flush=True)

    model = make_model(input_shape=X_train.shape[1:], num_classes=num_classes)
    model.summary(print_fn=lambda x: print(x, flush=True))

    callbacks = [
        EarlyStopping(monitor="val_loss", patience=10, restore_best_weights=True),
        ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=5, min_lr=1e-7),
        CSVLogger(str(out_dir / "keras_history.csv")),
        ModelCheckpoint(str(out_dir / "best_model.keras"), monitor="val_loss", save_best_only=True),
    ]

    t0 = time.time()
    history = model.fit(
        X_train,
        y_train_cat,
        epochs=args.epochs,
        batch_size=args.batch_size,
        validation_data=(X_val, y_val_cat),
        class_weight=class_weights,
        callbacks=callbacks,
        verbose=1,
    )
    elapsed = time.time() - t0

    # Save final and reload best for summary/output.
    model.save(out_dir / "final_model.keras")
    best = tf.keras.models.load_model(
        out_dir / "best_model.keras",
        custom_objects={"custom_loss_with_entropy": custom_loss_with_entropy},
    )

    summary = save_npz_bundle(
        out_dir=out_dir,
        model=best,
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        X_test_known=X_test_known,
        y_test_known=y_test_known,
        X_test_open=X_test_open,
        y_test_open=y_test_open,
        class_names=class_names,
        cfg=cfg,
        history_dict={k: [float(x) for x in v] for k, v in history.history.items()},
    )

    val_open_probs = best.predict(X_test_open[: min(len(X_test_open), len(X_val))], batch_size=512, verbose=0)
    val_known_probs = best.predict(X_val[: len(val_open_probs)], batch_size=512, verbose=0)
    anchors = anchor_metrics(val_known_probs, val_open_probs, anchor_fraction=0.05)

    complete = {
        "run_name": run_name,
        "out_dir": str(out_dir),
        "elapsed_sec": elapsed,
        "summary": summary,
        "anchor_metrics_balanced_val_known_vs_test_open_subset": anchors,
    }
    (out_dir / "train_complete.json").write_text(json.dumps(complete, indent=2))

    print("SHREYASH_KERAS_DONE", json.dumps(complete, indent=2), flush=True)


if __name__ == "__main__":
    main()
