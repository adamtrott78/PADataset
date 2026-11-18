#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def _compressed_states(track: np.ndarray, quant_step: float) -> np.ndarray:
    x = np.asarray(track, dtype=np.float64).reshape(-1)
    q = np.rint(x / quant_step).astype(np.int64)
    if q.size == 0:
        return q
    keep = np.ones(q.size, dtype=bool)
    keep[1:] = q[1:] != q[:-1]
    return q[keep]


def trajectory_features(track: np.ndarray, spread: np.ndarray, quant_step: float) -> dict:
    states = _compressed_states(track, quant_step)
    if states.size == 0:
        states = np.array([0], dtype=np.int64)

    unique_count = int(np.unique(states).size)
    revisit = 0
    seen = set()
    for s in states:
        si = int(s)
        if si in seen:
            revisit += 1
        seen.add(si)
    revisit_fraction = revisit / max(1, len(states))

    delta = np.diff(states)
    delta = delta[delta != 0]
    if delta.size:
        pos = float(np.mean(delta > 0))
        neg = float(np.mean(delta < 0))
        monotonic_fraction = max(pos, neg)
        signs = np.sign(delta)
        direction_change_rate = (
            float(np.mean(signs[1:] != signs[:-1])) if signs.size > 1 else 0.0
        )
        mean_abs_step = float(np.mean(np.abs(delta)))
    else:
        monotonic_fraction = 1.0
        direction_change_rate = 0.0
        mean_abs_step = 0.0

    return {
        "unique_states": unique_count,
        "compressed_state_count": int(states.size),
        "revisit_fraction": float(revisit_fraction),
        "monotonic_fraction": float(monotonic_fraction),
        "direction_change_rate": float(direction_change_rate),
        "mean_abs_step_bins": mean_abs_step,
        "centroid_range": float(np.max(track) - np.min(track)),
        "centroid_std": float(np.std(track)),
        "spread_mean": float(np.mean(spread)),
        "spread_std": float(np.std(spread)),
    }


def collect_rows(cache_root: Path, max_per_file: int, quant_step: float) -> pd.DataFrame:
    rows = []
    files = sorted(cache_root.glob("*.h5"))
    for path in files:
        with h5py.File(path, "r") as f:
            mode = str(f.attrs.get("feature_mode", ""))
            if mode != "stft_tracks64_v1":
                continue
            y = np.asarray(f["y_pa"]).reshape(-1)
            # PADataset PA_NAMES order: PA1=0, PA4=3.
            mask = np.flatnonzero((y == 0) | (y == 3))
            if mask.size == 0:
                continue

            if mask.size > max_per_file:
                take = np.linspace(0, mask.size - 1, max_per_file, dtype=np.int64)
                mask = mask[take]

            X = f["Xfeat"]
            frame_count = int(f.attrs.get("stft_frame_count", 64))
            sample_points = np.floor(
                np.arange(frame_count, dtype=np.float64) * X.shape[-1] / frame_count
            ).astype(np.int64)
            sample_points = np.minimum(sample_points, X.shape[-1] - 1)

            for idx in mask:
                centroid = np.asarray(X[int(idx), 2, sample_points], dtype=np.float32)
                spread = np.asarray(X[int(idx), 3, sample_points], dtype=np.float32)
                feat = trajectory_features(centroid, spread, quant_step)
                feat.update(
                    {
                        "label": 1 if int(y[int(idx)]) == 3 else 0,
                        "pa_name": "PA4" if int(y[int(idx)]) == 3 else "PA1",
                        "group": path.name,
                        "cache_file": str(path),
                        "local_idx": int(idx),
                    }
                )
                rows.append(feat)

    if not rows:
        raise RuntimeError(f"No PA1/PA4 STFT-track rows found under {cache_root}")
    return pd.DataFrame(rows)


def evaluate(df: pd.DataFrame, folds: int) -> dict:
    feature_cols = [
        "unique_states",
        "compressed_state_count",
        "revisit_fraction",
        "monotonic_fraction",
        "direction_change_rate",
        "mean_abs_step_bins",
        "centroid_range",
        "centroid_std",
        "spread_mean",
        "spread_std",
    ]
    X = df[feature_cols].to_numpy(dtype=np.float64)
    y = df["label"].to_numpy(dtype=np.int64)
    groups = df["group"].to_numpy()

    n_groups_per_class = min(
        df[df["label"] == cls]["group"].nunique() for cls in sorted(df["label"].unique())
    )
    n_splits = min(int(folds), int(n_groups_per_class))
    if n_splits < 2:
        raise RuntimeError("Need at least two cache-file groups per class")

    splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=1701)
    fold_rows = []
    coefs = []
    for fold, (tr, te) in enumerate(splitter.split(X, y, groups), start=1):
        model = make_pipeline(
            StandardScaler(),
            LogisticRegression(
                max_iter=2000,
                class_weight="balanced",
                solver="lbfgs",
                random_state=1701,
            ),
        )
        model.fit(X[tr], y[tr])
        p = model.predict_proba(X[te])[:, 1]
        pred = (p >= 0.5).astype(np.int64)
        fold_rows.append(
            {
                "fold": fold,
                "n_train": int(len(tr)),
                "n_test": int(len(te)),
                "accuracy": float(accuracy_score(y[te], pred)),
                "macro_f1": float(f1_score(y[te], pred, average="macro")),
                "auroc": float(roc_auc_score(y[te], p)),
            }
        )
        lr = model[-1]
        coefs.append(dict(zip(feature_cols, lr.coef_[0].tolist())))

    single_metric = {}
    for col in feature_cols:
        v = df[col].to_numpy(dtype=np.float64)
        auc = float(roc_auc_score(y, v))
        single_metric[col] = max(auc, 1.0 - auc)

    return {
        "schema": "padataset.pa1-pa4-stft-diagnostic.v1",
        "n_samples": int(len(df)),
        "n_pa1": int((df["label"] == 0).sum()),
        "n_pa4": int((df["label"] == 1).sum()),
        "n_groups": int(df["group"].nunique()),
        "feature_columns": feature_cols,
        "folds": fold_rows,
        "mean_accuracy": float(np.mean([r["accuracy"] for r in fold_rows])),
        "mean_macro_f1": float(np.mean([r["macro_f1"] for r in fold_rows])),
        "mean_auroc": float(np.mean([r["auroc"] for r in fold_rows])),
        "single_metric_abs_auroc": single_metric,
        "mean_logistic_coefficients": {
            k: float(np.mean([c[k] for c in coefs])) for k in feature_cols
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache-root", required=True)
    ap.add_argument("--out-dir", default="results/pa1_pa4_stft_diagnostic")
    ap.add_argument("--max-per-file", type=int, default=512)
    ap.add_argument("--quant-step", type=float, default=0.02)
    ap.add_argument("--folds", type=int, default=5)
    args = ap.parse_args()

    cache_root = Path(args.cache_root).expanduser()
    out_dir = Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    df = collect_rows(cache_root, int(args.max_per_file), float(args.quant_step))
    result = evaluate(df, int(args.folds))

    df.to_csv(out_dir / "sample_features.csv", index=False)
    (out_dir / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
