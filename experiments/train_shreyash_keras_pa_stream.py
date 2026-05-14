#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import argparse
import csv
import json
import os
import sys
import time

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np
import torch
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import (
    Conv1D, MaxPooling1D, GlobalAveragePooling1D,
    Dense, Dropout, Input, ReLU, BatchNormalization,
)
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.regularizers import l2
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, CSVLogger, ModelCheckpoint, BackupAndRestore
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import accuracy_score, f1_score

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from osr_core import _make_setup_from_config
from prepData import build_data_from_setup


def configure_tf():
    gpus = tf.config.list_physical_devices("GPU")
    for gpu in gpus:
        try:
            tf.config.experimental.set_memory_growth(gpu, True)
        except Exception:
            pass
    print("TF_GPUS", gpus, flush=True)


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


def to_numpy_x_y(item):
    x, y = item[:2]

    if isinstance(x, torch.Tensor):
        x = x.detach().cpu().numpy()
    else:
        x = np.asarray(x)

    if isinstance(y, torch.Tensor):
        y = int(y.detach().cpu().item())
    else:
        y = int(y)

    x = x.astype("float32")

    # PA cache tensor: [8, 16384] -> Keras Conv1D: [16384, 8]
    if x.ndim == 2 and x.shape[0] == 8:
        x = np.transpose(x, (1, 0))
    elif x.ndim == 2 and x.shape[1] == 8:
        pass
    else:
        raise ValueError(f"Unexpected sample shape: {x.shape}")

    return x, y


class TorchDatasetSequence(tf.keras.utils.Sequence):
    def __init__(self, dataset, batch_size, num_classes, shuffle=False, seed=0, limit_n=None, return_y=True, **kwargs):
        super().__init__(**kwargs)
        self.dataset = dataset
        self.batch_size = int(batch_size)
        self.num_classes = int(num_classes)
        self.shuffle = bool(shuffle)
        self.rng = np.random.default_rng(seed)
        self.return_y = bool(return_y)

        n = len(dataset)
        if limit_n is not None:
            n = min(n, int(limit_n))
        self.indices = np.arange(n, dtype=np.int64)
        self.on_epoch_end()

    def __len__(self):
        return int(np.ceil(len(self.indices) / self.batch_size))

    def __getitem__(self, batch_idx):
        sl = slice(batch_idx * self.batch_size, min((batch_idx + 1) * self.batch_size, len(self.indices)))
        idxs = self.indices[sl]

        xs = []
        ys = []
        for idx in idxs:
            x, y = to_numpy_x_y(self.dataset[int(idx)])
            xs.append(x)
            ys.append(y)

        X = np.stack(xs, axis=0).astype("float32")
        y = np.asarray(ys, dtype=np.int64)

        if not self.return_y:
            return X

        Y = tf.keras.utils.to_categorical(y, num_classes=self.num_classes)
        return X, Y

    def on_epoch_end(self):
        if self.shuffle:
            self.rng.shuffle(self.indices)

    def labels(self):
        ys = []
        for idx in self.indices:
            _, y = to_numpy_x_y(self.dataset[int(idx)])
            ys.append(y)
        return np.asarray(ys, dtype=np.int64)


def predict_probs(model, dataset, batch_size, num_classes, limit_n=None):
    seq_x = TorchDatasetSequence(
        dataset=dataset,
        batch_size=batch_size,
        num_classes=num_classes,
        shuffle=False,
        limit_n=limit_n,
        return_y=False,
    )
    probs = model.predict(seq_x, verbose=1)
    seq_y = TorchDatasetSequence(
        dataset=dataset,
        batch_size=batch_size,
        num_classes=num_classes,
        shuffle=False,
        limit_n=limit_n,
        return_y=True,
    )
    y = seq_y.labels()
    return probs, y


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




def read_last_completed_epoch(out_dir: Path) -> int:
    """
    Return number of completed epochs.

    Keras `initial_epoch` expects the count of already-completed epochs,
    so if latest_epoch.json says epoch=7, resume should use initial_epoch=7.
    """
    out_dir = Path(out_dir)
    state_path = out_dir / "latest_epoch.json"
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text())
            return int(state.get("epoch", 0))
        except Exception:
            pass

    hist_path = out_dir / "keras_history.csv"
    if hist_path.exists():
        try:
            with hist_path.open(newline="") as f:
                rows = list(csv.DictReader(f))
            return len(rows)
        except Exception:
            pass

    return 0


def read_best_val_loss(out_dir: Path):
    out_dir = Path(out_dir)
    hist_path = out_dir / "keras_history.csv"
    if not hist_path.exists():
        return None

    vals = []
    try:
        with hist_path.open(newline="") as f:
            for row in csv.DictReader(f):
                v = row.get("val_loss")
                if v not in [None, ""]:
                    vals.append(float(v))
    except Exception:
        return None

    return min(vals) if vals else None


class TrainingStateCallback(tf.keras.callbacks.Callback):
    """
    Writes lightweight state every epoch so interrupted jobs can resume.
    """
    def __init__(self, out_dir):
        super().__init__()
        self.out_dir = Path(out_dir)
        self.state_path = self.out_dir / "latest_epoch.json"

    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}
        payload = {
            "epoch": epoch_num,
            "time": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "logs": {k: float(v) for k, v in logs.items() if isinstance(v, (int, float, np.floating))},
            "latest_model_path": str(self.out_dir / "latest_model.keras"),
            "best_model_path": str(self.out_dir / "best_model.keras"),
        }
        tmp = self.state_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2))
        tmp.replace(self.state_path)

        print(
            "TRAIN_STATE"
            f" | epoch={payload['epoch']}"
            f" | latest={payload['latest_model_path']}"
            f" | best={payload['best_model_path']}",
            flush=True,
        )



class EpochOSRMetricsCallback(tf.keras.callbacks.Callback):
    """
    Logs DQN-relevant backbone geometry after each epoch.

    Metrics:
      - epoch_val_known_macro_f1
      - epoch_anchor_high_known_frac
      - epoch_anchor_low_open_frac

    These are the core pass/fail signals for whether the CNN backbone is
    producing a confidence manifold that Shreyash-style DQN can use.
    """
    def __init__(
        self,
        val_known_ds,
        val_open_ds,
        num_classes,
        out_dir,
        batch_size=512,
        limit_n=None,
        every_n=5,
    ):
        super().__init__()
        self.val_known_ds = val_known_ds
        self.val_open_ds = val_open_ds
        self.num_classes = int(num_classes)
        self.out_dir = Path(out_dir)
        self.batch_size = int(batch_size)
        self.limit_n = limit_n
        self.every_n = max(1, int(every_n))
        self.csv_path = self.out_dir / "epoch_osr_metrics.csv"
        self.jsonl_path = self.out_dir / "epoch_osr_metrics.jsonl"

        if not self.csv_path.exists():
            with self.csv_path.open("w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=[
                    "epoch",
                    "epoch_val_known_macro_f1",
                    "epoch_val_known_acc",
                    "epoch_anchor_high_known_frac",
                    "epoch_anchor_low_open_frac",
                    "epoch_anchor_high_open_frac",
                    "epoch_known_p1_mean",
                    "epoch_open_p1_mean",
                    "epoch_anchor_k",
                ])
                w.writeheader()

    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}
        epoch_num = int(epoch + 1)

        # Always evaluate epoch 1, then every N epochs.
        if epoch_num != 1 and epoch_num % self.every_n != 0:
            print(
                "EPOCH_OSR_METRICS_SKIP"
                f" | epoch={epoch_num}"
                f" | next_eval_epoch={((epoch_num // self.every_n) + 1) * self.every_n}",
                flush=True,
            )
            return

        known_probs, known_y = predict_probs(
            self.model,
            self.val_known_ds,
            self.batch_size,
            self.num_classes,
            limit_n=self.limit_n,
        )
        open_probs, open_y = predict_probs(
            self.model,
            self.val_open_ds,
            self.batch_size,
            self.num_classes,
            limit_n=self.limit_n,
        )

        known_pred = known_probs.argmax(axis=1)
        known_macro_f1 = float(f1_score(known_y, known_pred, average="macro"))
        known_acc = float(accuracy_score(known_y, known_pred))

        n_anchor = min(len(known_probs), len(open_probs))
        anchors = anchor_metrics(
            known_probs[:n_anchor],
            open_probs[:n_anchor],
            anchor_fraction=0.05,
        )

        row = {
            "epoch": epoch_num,
            "epoch_val_known_macro_f1": known_macro_f1,
            "epoch_val_known_acc": known_acc,
            "epoch_anchor_high_known_frac": anchors["anchor_high_known_frac"],
            "epoch_anchor_low_open_frac": anchors["anchor_low_open_frac"],
            "epoch_anchor_high_open_frac": anchors["anchor_high_open_frac"],
            "epoch_known_p1_mean": anchors["known_p1_mean"],
            "epoch_open_p1_mean": anchors["open_p1_mean"],
            "epoch_anchor_k": anchors["anchor_k"],
        }

        with self.csv_path.open("a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(row.keys()))
            w.writerow(row)

        with self.jsonl_path.open("a") as f:
            f.write(json.dumps(row) + "\n")

        # Also attach to Keras logs so CSVLogger can capture them too.
        logs["epoch_val_known_macro_f1"] = known_macro_f1
        logs["epoch_anchor_high_known_frac"] = anchors["anchor_high_known_frac"]
        logs["epoch_anchor_low_open_frac"] = anchors["anchor_low_open_frac"]

        print(
            "EPOCH_OSR_METRICS"
            f" | epoch={epoch_num}"
            f" | known_macro_f1={known_macro_f1:.4f}"
            f" | known_acc={known_acc:.4f}"
            f" | anchor_hi_known={anchors['anchor_high_known_frac']:.4f}"
            f" | anchor_lo_open={anchors['anchor_low_open_frac']:.4f}"
            f" | known_p1_mean={anchors['known_p1_mean']:.4f}"
            f" | open_p1_mean={anchors['open_p1_mean']:.4f}",
            flush=True,
        )



def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cfg", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--data-root", default="data")
    ap.add_argument("--epochs", type=int, default=500)
    ap.add_argument("--batch-size", type=int, default=500)
    ap.add_argument("--predict-batch-size", type=int, default=512)
    ap.add_argument("--smoke-n", type=int, default=None)
    ap.add_argument("--resume", action="store_true", help="Resume from latest_model.keras if present, else best_model.keras.")
    ap.add_argument(
        "--epoch-metric-n",
        type=int,
        default=None,
        help="Optional cap for per-epoch OSR metric evaluation. Default uses full val_known and val_open.",
    )
    ap.add_argument(
        "--epoch-metric-every",
        type=int,
        default=5,
        help="Evaluate known-F1 and DQN anchor metrics every N epochs. Epoch 1 is always evaluated.",
    )
    args = ap.parse_args()

    configure_tf()

    cfg = json.loads(Path(args.cfg).read_text())
    run_name = cfg.get("run_name", Path(args.cfg).stem)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "config.json").write_text(json.dumps(cfg, indent=2))

    print(f"SHREYASH_KERAS_STREAM_START | run_name={run_name} | cfg={args.cfg} | out_dir={out_dir}", flush=True)

    setup = _make_setup_from_config(cfg, return_metadata=True)
    setup.root = args.data_root

    data = build_data_from_setup(
        setup,
        batch_size=128,
        num_workers=0,
        pin_memory=False,
    )

    class_names = list(data["meta"]["class_names"])
    num_classes = int(data["meta"]["num_classes"])

    train_ds = data["train_ds"]
    val_ds = data["val_ds"]
    test_known_ds = data["test_known_ds"]
    test_open_ds = data["test_open_ds"]
    val_open_ds = data.get("val_open_ds", None)

    train_seq_for_labels = TorchDatasetSequence(
        train_ds, batch_size=args.batch_size, num_classes=num_classes,
        shuffle=False, seed=0, limit_n=args.smoke_n, return_y=True,
    )
    train_y = train_seq_for_labels.labels()

    class_weights_arr = compute_class_weight(
        class_weight="balanced",
        classes=np.arange(num_classes),
        y=train_y,
    )
    class_weights = {i: float(w) for i, w in enumerate(class_weights_arr)}

    train_seq = TorchDatasetSequence(
        train_ds, batch_size=args.batch_size, num_classes=num_classes,
        shuffle=True, seed=int(cfg.get("seed", 0)), limit_n=args.smoke_n, return_y=True,
    )
    val_seq = TorchDatasetSequence(
        val_ds, batch_size=args.batch_size, num_classes=num_classes,
        shuffle=False, seed=0, limit_n=args.smoke_n, return_y=True,
    )

    # Infer input shape from first sample.
    x0, _ = to_numpy_x_y(train_ds[0])

    latest_model_path = out_dir / "latest_model.keras"
    best_model_path = out_dir / "best_model.keras"
    initial_epoch = 0

    if args.resume and latest_model_path.exists():
        print(f"RESUME_LOAD | source=latest | path={latest_model_path}", flush=True)
        model = tf.keras.models.load_model(
            latest_model_path,
            custom_objects={"custom_loss_with_entropy": custom_loss_with_entropy},
        )
        initial_epoch = read_last_completed_epoch(out_dir)
    elif args.resume and best_model_path.exists():
        print(f"RESUME_LOAD | source=best | path={best_model_path}", flush=True)
        model = tf.keras.models.load_model(
            best_model_path,
            custom_objects={"custom_loss_with_entropy": custom_loss_with_entropy},
        )
        initial_epoch = read_last_completed_epoch(out_dir)
    else:
        model = make_model(input_shape=x0.shape, num_classes=num_classes)

    print(
        "RESUME_INFO",
        {
            "resume": bool(args.resume),
            "initial_epoch": int(initial_epoch),
            "target_epochs": int(args.epochs),
            "latest_model_exists": latest_model_path.exists(),
            "best_model_exists": best_model_path.exists(),
        },
        flush=True,
    )

    model.summary(print_fn=lambda x: print(x, flush=True))

    prev_best_val_loss = read_best_val_loss(out_dir)
    epoch_metric_open_ds = val_open_ds if val_open_ds is not None else test_open_ds

    callbacks = [
        EpochOSRMetricsCallback(
            val_known_ds=val_ds,
            val_open_ds=epoch_metric_open_ds,
            num_classes=num_classes,
            out_dir=out_dir,
            batch_size=args.predict_batch_size,
            limit_n=args.epoch_metric_n,
            every_n=args.epoch_metric_every,
        ),
        TrainingStateCallback(out_dir=out_dir),
        BackupAndRestore(backup_dir=str(out_dir / "keras_backup")),
        EarlyStopping(monitor="val_loss", patience=10, restore_best_weights=True),
        ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=5, min_lr=1e-7),
        CSVLogger(str(out_dir / "keras_history.csv"), append=bool(initial_epoch > 0)),
        ModelCheckpoint(
            str(latest_model_path),
            monitor="val_loss",
            save_best_only=False,
        ),
        ModelCheckpoint(
            str(best_model_path),
            monitor="val_loss",
            save_best_only=True,
            mode="min",
            initial_value_threshold=prev_best_val_loss,
        ),
    ]

    print("TRAIN_INFO", {
        "run_name": run_name,
        "class_names": class_names,
        "num_classes": num_classes,
        "train_n": len(train_seq.indices),
        "val_n": len(val_seq.indices),
        "test_known_n": min(len(test_known_ds), args.smoke_n or len(test_known_ds)),
        "test_open_n": min(len(test_open_ds), args.smoke_n or len(test_open_ds)),
        "batch_size": args.batch_size,
        "class_weights": class_weights,
    }, flush=True)

    t0 = time.time()
    history = model.fit(
        train_seq,
        epochs=args.epochs,
        initial_epoch=initial_epoch,
        validation_data=val_seq,
        class_weight=class_weights,
        callbacks=callbacks,
        verbose=1,
    )
    elapsed = time.time() - t0

    model.save(out_dir / "final_model.keras")

    best = tf.keras.models.load_model(
        out_dir / "best_model.keras",
        custom_objects={"custom_loss_with_entropy": custom_loss_with_entropy},
    )

    val_probs, val_y = predict_probs(best, val_ds, args.predict_batch_size, num_classes, limit_n=args.smoke_n)
    test_known_probs, test_known_y = predict_probs(best, test_known_ds, args.predict_batch_size, num_classes, limit_n=args.smoke_n)
    test_open_probs, test_open_y = predict_probs(best, test_open_ds, args.predict_batch_size, num_classes, limit_n=args.smoke_n)

    if val_open_ds is not None:
        val_open_probs, val_open_y = predict_probs(best, val_open_ds, args.predict_batch_size, num_classes, limit_n=args.smoke_n)
        anchor_known_probs = val_probs[: min(len(val_probs), len(val_open_probs))]
        anchor_open_probs = val_open_probs[: min(len(val_probs), len(val_open_probs))]
        anchor_source = "true_val_open"
    else:
        n_anchor = min(len(val_probs), len(test_open_probs))
        val_open_probs = None
        val_open_y = None
        anchor_known_probs = val_probs[:n_anchor]
        anchor_open_probs = test_open_probs[:n_anchor]
        anchor_source = "test_open_subset_fallback"

    anchors = anchor_metrics(anchor_known_probs, anchor_open_probs, anchor_fraction=0.05)

    npz_payload = {
        "val_known_probs": val_probs,
        "val_known_y": val_y,
        "test_known_probs": test_known_probs,
        "test_known_y": test_known_y,
        "test_open_probs": test_open_probs,
        "test_open_y": test_open_y,
        "class_names": np.array(class_names, dtype=object),
    }
    if val_open_probs is not None:
        npz_payload["val_open_probs"] = val_open_probs
        npz_payload["val_open_y"] = val_open_y

    np.savez_compressed(out_dir / "softmax_outputs.npz", **npz_payload)

    val_pred = val_probs.argmax(axis=1)
    known_pred = test_known_probs.argmax(axis=1)

    summary = {
        "run_name": run_name,
        "model_family": "shreyash_keras_cnn_stream",
        "class_names": class_names,
        "num_classes": num_classes,
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
            "batch_size": args.batch_size,
            "early_stopping_monitor": "val_loss",
            "early_stopping_patience": 10,
            "reduce_lr_patience": 5,
            "reduce_lr_factor": 0.5,
            "reduce_lr_min_lr": 1e-7,
        },
        "val_acc": float(accuracy_score(val_y, val_pred)),
        "val_macro_f1": float(f1_score(val_y, val_pred, average="macro")),
        "test_known_acc": float(accuracy_score(test_known_y, known_pred)),
        "test_known_macro_f1": float(f1_score(test_known_y, known_pred, average="macro")),
        "anchor_source": anchor_source,
        "anchor_metrics": anchors,
        "history": {k: [float(x) for x in v] for k, v in history.history.items()},
        "elapsed_sec": float(elapsed),
    }

    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    (out_dir / "train_complete.json").write_text(json.dumps({
        "run_name": run_name,
        "out_dir": str(out_dir),
        "elapsed_sec": float(elapsed),
        "summary_path": str(out_dir / "summary.json"),
        "softmax_outputs_path": str(out_dir / "softmax_outputs.npz"),
    }, indent=2))

    print("SHREYASH_KERAS_STREAM_DONE", json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
