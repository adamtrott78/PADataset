#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import numpy as np

from osr_core import build_backbone_payload, evaluate_osr_predictions, load_backbone_run
from multisurrogate_dqnguard import (
    MultiSurrogateHybridDQNGuard,
    assert_target_quarantined,
    partition_known_calibration,
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
    ).strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--checkpoint", default="best_model")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--num-workers", type=int, default=0)
    ap.add_argument("--partition-seed", type=int, default=1701)
    ap.add_argument("--dqn-episodes", type=int, default=30)
    ap.add_argument("--known-budget", type=float, default=0.05)
    args = ap.parse_args()

    t0 = time.time()
    out = Path(args.out_dir)
    if out.exists():
        raise SystemExit(f"Refusing to overwrite existing output directory: {out}")
    out.mkdir(parents=True)

    handle = load_backbone_run(args.run_dir, args.checkpoint, device=args.device)
    cfg = dict(handle.config)

    if cfg.get("early_stopping_mode", "known_only") != "known_only":
        raise SystemExit(
            "Stage 03 forbids target-informed backbone selection: "
            "early_stopping_mode must be known_only"
        )
    if cfg.get("quarantine_target_until_test") is not True:
        raise SystemExit(
            "Stage 03 requires quarantine_target_until_test=true so target-open "
            "examples are first consumed only by the frozen final evaluator"
        )
    unknown_pas = list(cfg.get("unknown_pas") or [])
    if len(unknown_pas) != 1:
        raise SystemExit(f"Expected exactly one held-out target, got {unknown_pas}")
    target_pa = str(unknown_pas[0])
    if int(cfg.get("cache_len", -1)) != 16384:
        raise SystemExit("Stage 03 provenance requires cache_len=16384")

    payload = build_backbone_payload(
        handle,
        include=("val_known", "test_known", "test_open"),
        batch_size=args.batch_size,
        num_workers=args.num_workers,
        pin_memory=True,
        return_sample_meta=True,
    )
    if payload.val_known is None or payload.test_known is None or payload.test_open is None:
        raise SystemExit("Required backbone splits are missing")
    known_classes = list(payload.meta["class_names"])
    if len(known_classes) != 4 or target_pa in known_classes:
        raise SystemExit(
            f"Stage 03 requires exactly four non-target known classes; "
            f"target={target_pa}, known={known_classes}"
        )

    partitions = partition_known_calibration(
        payload.val_known,
        payload.meta["class_names"],
        seed=args.partition_seed,
    )
    assert_target_quarantined(partitions, payload.test_open)

    method = MultiSurrogateHybridDQNGuard(
        budget=args.known_budget,
        seed=42,
        dqn_kwargs={
            "episodes": args.dqn_episodes,
            "anchor_fraction": 0.05,
            "train_subsample_size": 1250,
            "centroid_update_threshold": 0.75,
            "learning_rate": 1e-3,
            "batch_size": 32,
        },
    )
    method.fit(payload, partitions)

    unknown_label = int(payload.meta["num_classes"])
    known_pred = method.predict(payload.test_known, unknown_label)
    open_pred = method.predict(payload.test_open, unknown_label)
    metrics = evaluate_osr_predictions(
        known_split=payload.test_known,
        open_split=payload.test_open,
        known_pred=known_pred,
        open_pred=open_pred,
        known_class_names=payload.meta["class_names"],
        unknown_label_name="unknown",
    )

    params = method.get_params()
    summary = {
        "architecture": "C",
        "target_pa": target_pa,
        "method": method.method_name,
        "score_threshold": params["threshold"],
        "threshold_known_reject_cal": params["threshold_known_reject_cal"],
        "known_budget": args.known_budget,
        "partition_manifest_sha256": partitions.manifest["sha256"],
        "guard_aggregation": params["guard_aggregation"],
        "guard_weights": params["guard_weights"],
        **metrics,
        "elapsed_sec": time.time() - t0,
    }
    summary_path = out / "osr_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    result_hash = sha256_file(summary_path)

    run_dir = Path(args.run_dir)
    if not run_dir.is_absolute():
        run_dir = REPO_ROOT / run_dir
    config_path = run_dir / "config.json"
    checkpoint_path = run_dir / f"{args.checkpoint}.pt"

    record = {
        "schema": "padataset.multisurrogate_dqnguard.result.v1",
        "task_id": "mth602-final-multisurrogate-dqnguard-v1",
        "architecture": "C",
        "target_pa": target_pa,
        "source": {
            "git_sha": git_head(),
            "cache_len": int(cfg["cache_len"]),
            "cache_root": str(cfg["cache_root"]),
            "seed": int(cfg.get("seed", 0)),
            "historical_evidence_head": None,
        },
        "backbone": {
            "run_dir": args.run_dir,
            "config_sha256": sha256_file(config_path),
            "checkpoint_path": str(checkpoint_path),
            "checkpoint_sha256": sha256_file(checkpoint_path),
            "known_classes": list(payload.meta["class_names"]),
            "checkpoint_selection": "known_only",
        },
        "evidence_partition": {
            "target_quarantined": True,
            "known_fit": "val_known/fit",
            "known_guard": "val_known/guard",
            "known_norm": "val_known/norm",
            "known_threshold": "val_known/threshold",
            "pseudo_open": [
                {
                    "surrogate": name,
                    "role": "val_known/pseudo",
                    "count": len(split.y_true),
                }
                for name, split in sorted(partitions.pseudo_open.items())
            ],
            "manifest_sha256": partitions.manifest["sha256"],
        },
        "score": {
            "direction": "higher_is_more_unknown",
            "definition": "DQN_margin + max_s empiricalCDF_known(raw_guard_s)",
            "normalization": {"type": "empirical_known_cdf", "fit_role": "known_norm"},
            "aggregation": {"type": "max", "predeclared": True},
        },
        "threshold": {
            "source": "known_only",
            "budget": 0.05,
            "quantile": 0.95,
            "value": float(params["threshold"]),
            "calibration_known_reject_rate": float(params["threshold_known_reject_cal"]),
        },
        "metrics": {
            key: float(metrics[key])
            for key in (
                "known_reject_rate",
                "unknown_precision",
                "unknown_recall",
                "unknown_f1",
                "osr_macro_f1",
                "unknown_auroc",
            )
        },
        "provenance": {
            "config_sha256": sha256_file(config_path),
            "checkpoint_sha256": sha256_file(checkpoint_path),
            "result_sha256": result_hash,
            "command": sys.argv,
            "target_labels_used_for_tuning": False,
            "fallback_status": None,
            "feasibility_status": "partition_and_threshold_valid",
        },
        "status": "SMALL_REAL" if args.dqn_episodes >= 30 else "SMOKE",
    }
    record_path = out / "result_record.json"
    record_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    (out / "partition_manifest.json").write_text(
        json.dumps(partitions.manifest, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps({
        "result_record": str(record_path),
        "summary": str(summary_path),
        "unknown_f1": metrics["unknown_f1"],
        "known_reject_rate": metrics["known_reject_rate"],
        "threshold_known_reject_cal": params["threshold_known_reject_cal"],
    }, indent=2))


if __name__ == "__main__":
    main()
