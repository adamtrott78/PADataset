#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from osr_core import load_backbone_run
from evaluate import (
    build_osr_eval_bundle,
    collect_split_outputs_from_loader,
    _make_setup_from_run_config,
)
from prepData import build_data_from_setup
from experiments.l2o_directional_contract import resolve_directional_l2o_contract


ANALYSIS_MODE = "selector_geometry_pair_v1"


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


from experiments.l2o_selector_geometry_metrics_v1 import (
    summarize_confidence,
    summarize_feature_geometry,
)


def build_surrogate_open_split(
    handle,
    surrogate_pa: str,
    batch_size: int,
    num_workers: int,
    data_root=None,
    config_override: dict[str, Any] | None = None,
):
    if config_override is None:
        cfg = copy.deepcopy(handle.config)
        cfg["unknown_pas"] = [surrogate_pa]
        pas = cfg.get("pas", None)
        if pas is not None:
            cfg["pas"] = list(dict.fromkeys(list(pas) + [surrogate_pa]))
    else:
        cfg = copy.deepcopy(config_override)
        if cfg.get("unknown_pas") != [surrogate_pa]:
            raise ValueError(
                "surrogate config unknown_pas must exactly match requested surrogate"
            )
        if surrogate_pa not in list(cfg.get("pas", [])):
            raise ValueError("surrogate config pas must contain requested surrogate")

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
            raise RuntimeError(f"No val_open_loader for surrogate {surrogate_pa}")
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


def run_selector_geometry_pair(
    *,
    run_dir: str,
    checkpoint: str,
    out_dir: str,
    evaluation_target: str,
    evaluation_surrogate: str,
    known_cap: int,
    open_cap: int,
    device: str,
    batch_size: int,
    num_workers: int,
    data_root: str | None,
) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    handle = load_backbone_run(
        run_dir=run_dir,
        checkpoint_tag=checkpoint,
        device=device,
    )

    forward = resolve_directional_l2o_contract(
        handle.config,
        evaluation_target=evaluation_target,
        evaluation_surrogate=evaluation_surrogate,
        model_class_names=handle.class_names,
    )
    reverse = resolve_directional_l2o_contract(
        handle.config,
        evaluation_target=evaluation_surrogate,
        evaluation_surrogate=evaluation_target,
        model_class_names=handle.class_names,
    )

    directional_handle = copy.copy(handle)
    directional_handle.config = forward.target_config
    directional_handle.setup = None
    directional_handle.unknown_pas = [forward.evaluation_target]

    payload, _extras = build_osr_eval_bundle(
        directional_handle,
        batch_size=batch_size,
        num_workers=num_workers,
        pin_memory=True,
        data_root=data_root,
    )

    seed = int(payload.meta.get("seed", 0) or 0)
    known_cal = cap_split(
        payload.val_known, known_cap, seed + 101, True, "cap_known"
    )

    rows = []
    directions = [
        (
            forward.evaluation_target,
            forward.evaluation_surrogate,
            forward.surrogate_config,
        ),
        (
            reverse.evaluation_target,
            reverse.evaluation_surrogate,
            reverse.surrogate_config,
        ),
    ]

    for target, surrogate, surrogate_cfg in directions:
        sur_open = build_surrogate_open_split(
            handle=directional_handle,
            surrogate_pa=surrogate,
            batch_size=batch_size,
            num_workers=num_workers,
            data_root=data_root,
            config_override=surrogate_cfg,
        )
        sur_cal = cap_split(
            sur_open, open_cap, seed + 202, False, "cap_surrogate_open"
        )

        row = {
            "analysis_mode": ANALYSIS_MODE,
            "run_name": handle.run_name,
            "run_dir": run_dir,
            "checkpoint": checkpoint,
            "target": target,
            "surrogate": surrogate,
            "canonical_pair": json.dumps(list(forward.canonical_excluded_pair)),
            "known_pas": json.dumps(list(forward.known_pas)),
            "target_labels_used_for_tuning": False,
            "known_cap": int(len(known_cal.y_true)),
            "open_cap": int(len(sur_cal.y_true)),
        }
        row.update(summarize_confidence(known_cal, sur_cal))
        row.update(summarize_feature_geometry(known_cal, sur_cal))
        rows.append(row)

    df = pd.DataFrame(rows)
    path = out / "osr_summary.csv"
    df.to_csv(path, index=False)
    (out / "selector_geometry.json").write_text(
        json.dumps(
            {
                "schema": "padataset.l2o-selector-geometry-pair.v1",
                "analysis_mode": ANALYSIS_MODE,
                "canonical_pair": list(forward.canonical_excluded_pair),
                "known_pas": list(forward.known_pas),
                "rows": rows,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(df.to_string(index=False))
    print("\nWrote:", path)
    return path
