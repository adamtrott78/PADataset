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

import pandas as pd
import torch

from cross_surrogate_dqnguard import CrossSurrogateDQNGuardB
from multisurrogate_dqnguard import (
    assert_target_quarantined,
    partition_known_calibration,
)
from osr_core import (
    build_backbone_payload,
    evaluate_osr_predictions,
    extract_backbone_outputs,
    load_backbone_run,
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


def _flatten_cross_rows(params: dict) -> list[dict]:
    rows = []
    for train_surrogate, by_eval in sorted(params["cross_metrics"].items()):
        for eval_surrogate, metrics in sorted(by_eval.items()):
            rows.append(
                {
                    "train_surrogate": train_surrogate,
                    "eval_surrogate": eval_surrogate,
                    "diagonal": False,
                    "unknown_precision": metrics["unknown_precision"],
                    "unknown_recall": metrics["unknown_recall"],
                    "unknown_f1": metrics["unknown_f1"],
                    "osr_macro_f1": metrics["osr_macro_f1"],
                    "known_reject_rate": metrics["known_reject_rate"],
                    "unknown_auroc": metrics["unknown_auroc"],
                }
            )
    return rows


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
    ap.add_argument(
        "--state-mode",
        choices=["softmax3", "expanded5"],
        default="softmax3",
    )
    args = ap.parse_args()

    t0 = time.time()
    out = Path(args.out_dir)
    if out.exists():
        if not out.is_dir():
            raise SystemExit(f"Refusing non-directory output path: {out}")
        if any(out.iterdir()):
            raise SystemExit(f"Refusing to overwrite non-empty output directory: {out}")
    else:
        out.mkdir(parents=True)

    handle = load_backbone_run(args.run_dir, args.checkpoint, device=args.device)
    cfg = dict(handle.config)

    if cfg.get("early_stopping_mode", "known_only") != "known_only":
        raise SystemExit(
            "Architecture B requires known-only backbone checkpoint selection"
        )
    if cfg.get("quarantine_target_until_test") is not True:
        raise SystemExit(
            "Architecture B requires quarantine_target_until_test=true"
        )
    unknown_pas = list(cfg.get("unknown_pas") or [])
    if len(unknown_pas) != 1:
        raise SystemExit(f"Expected exactly one held-out target, got {unknown_pas}")
    target_pa = str(unknown_pas[0])
    if int(cfg.get("cache_len", -1)) != 16384:
        raise SystemExit("Architecture B provenance requires cache_len=16384")

    # Keep the genuine target physically unconsumed through Architecture-B
    # fitting, thresholding, and cross-surrogate candidate selection.
    payload = build_backbone_payload(
        handle,
        include=("val_known", "test_known"),
        batch_size=args.batch_size,
        num_workers=args.num_workers,
        pin_memory=True,
        return_sample_meta=True,
    )
    if payload.val_known is None or payload.test_known is None:
        raise SystemExit("Required known backbone splits are missing")
    if payload.test_open is not None:
        raise SystemExit("Target-open split was consumed before winner freeze")

    known_classes = list(payload.meta["class_names"])
    if len(known_classes) != 4 or target_pa in known_classes:
        raise SystemExit(
            "Architecture B development protocol requires exactly four "
            f"non-target known classes; target={target_pa}, known={known_classes}"
        )

    partitions = partition_known_calibration(
        payload.val_known,
        payload.meta["class_names"],
        seed=args.partition_seed,
    )

    method = CrossSurrogateDQNGuardB(
        state_mode=args.state_mode,
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
    if not method.fitted_ or method.selected_surrogate_ is None:
        raise RuntimeError("Architecture-B winner was not frozen after fit")

    # The genuine target is first materialized here, after the winner is frozen.
    target_open = extract_backbone_outputs(
        handle,
        "test_open",
        batch_size=args.batch_size,
        num_workers=args.num_workers,
        pin_memory=True,
        return_sample_meta=True,
    )
    assert_target_quarantined(partitions, target_open)

    unknown_label = int(payload.meta["num_classes"])
    known_pred = method.predict(payload.test_known, unknown_label)
    open_pred = method.predict(target_open, unknown_label)
    target_metrics = evaluate_osr_predictions(
        known_split=payload.test_known,
        open_split=target_open,
        known_pred=known_pred,
        open_pred=open_pred,
        known_class_names=payload.meta["class_names"],
        unknown_label_name="unknown",
    )

    params = method.get_params()
    selected = str(params["selected_surrogate"])

    cross_rows = _flatten_cross_rows(params)
    pd.DataFrame(cross_rows).to_csv(
        out / "cross_surrogate_matrix.csv",
        index=False,
    )
    pd.DataFrame(
        [dict(v) for _, v in sorted(params["candidate_summaries"].items())]
    ).to_csv(out / "candidate_summary.csv", index=False)

    summary = {
        "architecture": "B",
        "method": method.method_name,
        "state_mode": args.state_mode,
        "target_pa": target_pa,
        "known_classes": known_classes,
        "selected_surrogate": selected,
        "selection_rule": [
            "max worst off-diagonal unknown_f1",
            "max mean off-diagonal unknown_f1",
            "max mean off-diagonal osr_macro_f1",
            "min known_guard_reject_rate",
        ],
        "selected_threshold": params["selected_threshold"],
        "threshold_known_reject_cal": params[
            "threshold_known_reject_cal"
        ][selected],
        "known_budget": args.known_budget,
        "partition_manifest_sha256": partitions.manifest["sha256"],
        "candidate_summaries": params["candidate_summaries"],
        "target_metrics": target_metrics,
        "elapsed_sec": time.time() - t0,
    }
    summary_path = out / "osr_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    selected_dqn = method.selected_dqn_
    if selected_dqn is None or selected_dqn.agent is None:
        raise RuntimeError("Selected DQN is missing after fit")

    selected_checkpoint = {
        "schema": "padataset.cross-surrogate-dqnguard-b.dqn.v1",
        "architecture": "B",
        "state_mode": args.state_mode,
        "selected_surrogate": selected,
        "score_threshold": float(params["selected_threshold"]),
        "known_budget": float(args.known_budget),
        "qnet_state_dict": selected_dqn.agent.model.state_dict(),
        "centroid_known": selected_dqn.centroid_known_,
        "centroid_unknown": selected_dqn.centroid_unknown_,
        "centroid_known_count": selected_dqn.centroid_known_count_,
        "centroid_unknown_count": selected_dqn.centroid_unknown_count_,
        "dqn_params": params["selected_dqn_params"],
    }
    checkpoint_path = out / "selected_dqn.pt"
    torch.save(selected_checkpoint, checkpoint_path)

    (out / "partition_manifest.json").write_text(
        json.dumps(partitions.manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    run_dir = Path(args.run_dir)
    if not run_dir.is_absolute():
        run_dir = REPO_ROOT / run_dir
    config_path = run_dir / "config.json"
    backbone_checkpoint = run_dir / f"{args.checkpoint}.pt"

    result_record = {
        "schema": "padataset.cross-surrogate-dqnguard-b.result.v1",
        "task_id": "mth602-final-multisurrogate-dqnguard-v1",
        "architecture": "B",
        "target_pa": target_pa,
        "source": {
            "git_sha": git_head(),
            "cache_len": int(cfg["cache_len"]),
            "cache_root": str(cfg["cache_root"]),
            "backbone_seed": int(cfg.get("seed", 0)),
            "partition_seed": int(args.partition_seed),
            "dqn_seed": 42,
        },
        "backbone": {
            "run_dir": args.run_dir,
            "config_sha256": sha256_file(config_path),
            "checkpoint_path": str(backbone_checkpoint),
            "checkpoint_sha256": sha256_file(backbone_checkpoint),
            "known_classes": known_classes,
            "checkpoint_selection": "known_only",
        },
        "evidence_partition": {
            "target_quarantined": True,
            "known_fit": "val_known/fit",
            "known_guard": "val_known/guard",
            "known_threshold": "val_known/threshold",
            "pseudo_open": {
                k: {
                    "role": f"val_known/pseudo/{k}",
                    "count": int(len(v.y_true)),
                }
                for k, v in sorted(partitions.pseudo_open.items())
            },
            "manifest_sha256": partitions.manifest["sha256"],
        },
        "candidate_selection": {
            "own_surrogate_diagonal_excluded": True,
            "selected_surrogate": selected,
            "candidate_summaries": params["candidate_summaries"],
            "rule": summary["selection_rule"],
        },
        "score": {
            "state_mode": args.state_mode,
            "direction": "higher_is_more_unknown",
            "definition": "DQN Q_unknown - Q_known",
        },
        "threshold": {
            "source": "known_only",
            "budget": float(args.known_budget),
            "value": float(params["selected_threshold"]),
            "calibration_known_reject_rate": float(
                params["threshold_known_reject_cal"][selected]
            ),
        },
        "metrics": {
            key: float(target_metrics[key])
            for key in (
                "known_reject_rate",
                "unknown_precision",
                "unknown_recall",
                "unknown_f1",
                "osr_macro_f1",
                "unknown_auroc",
            )
        },
        "artifacts": {
            "summary_sha256": sha256_file(summary_path),
            "selected_dqn_sha256": sha256_file(checkpoint_path),
            "cross_surrogate_matrix": "cross_surrogate_matrix.csv",
            "candidate_summary": "candidate_summary.csv",
        },
        "provenance": {
            "command": sys.argv,
            "target_labels_used_for_fitting": False,
            "target_labels_used_for_thresholding": False,
            "target_labels_used_for_candidate_selection": False,
            "target_first_consumed_after_winner_frozen": True,
            "fallback_status": None,
        },
        "status": "SMALL_REAL" if args.dqn_episodes >= 30 else "SMOKE",
    }
    record_path = out / "result_record.json"
    record_path.write_text(
        json.dumps(result_record, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "result_record": str(record_path),
                "selected_surrogate": selected,
                "state_mode": args.state_mode,
                "known_reject_rate": target_metrics["known_reject_rate"],
                "unknown_f1": target_metrics["unknown_f1"],
                "osr_macro_f1": target_metrics["osr_macro_f1"],
                "unknown_auroc": target_metrics["unknown_auroc"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
