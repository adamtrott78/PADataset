#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

ALLOWED_RECORD_KEYS = {
    "trial_id",
    "canonical_pair",
    "stage",
    "config_path",
    "config_sha256",
    "status",
    "best_epoch",
    "val_macro_f1",
    "val_min_class_f1",
    "val_per_class_f1",
}
ALLOWED_STAGES = {"screen", "refine", "finalist"}


def _finite_unit(value: Any, label: str) -> float:
    x = float(value)
    if not math.isfinite(x) or not (0.0 <= x <= 1.0):
        raise ValueError(f"{label} must be finite and in [0,1]")
    return x


def validate_known_only_record(record: dict[str, Any], expected_stage: str | None = None) -> dict[str, Any]:
    extra = set(record) - ALLOWED_RECORD_KEYS
    if extra:
        raise ValueError(f"selection record contains forbidden/unreviewed fields: {sorted(extra)}")
    missing = {"trial_id", "canonical_pair", "stage", "config_path", "status", "val_macro_f1", "val_min_class_f1"} - set(record)
    if missing:
        raise ValueError(f"selection record missing required fields: {sorted(missing)}")
    stage = record["stage"]
    if stage not in ALLOWED_STAGES:
        raise ValueError(f"unsupported stage {stage!r}")
    if expected_stage is not None and stage != expected_stage:
        raise ValueError(f"stage mismatch: expected {expected_stage!r}, got {stage!r}")
    if record["status"] != "COMPLETE":
        raise ValueError(f"only COMPLETE known-validation records may be ranked: {record['trial_id']}")
    macro = _finite_unit(record["val_macro_f1"], "val_macro_f1")
    min_class = _finite_unit(record["val_min_class_f1"], "val_min_class_f1")
    per_class = record.get("val_per_class_f1")
    if per_class is not None:
        if not isinstance(per_class, dict) or not per_class:
            raise ValueError("val_per_class_f1 must be a non-empty mapping")
        vals = [_finite_unit(v, f"val_per_class_f1[{k}]") for k, v in per_class.items()]
        if abs(min(vals) - min_class) > 1e-9:
            raise ValueError("val_min_class_f1 does not match val_per_class_f1")
    out = dict(record)
    out["val_macro_f1"] = macro
    out["val_min_class_f1"] = min_class
    return out


def rank_pair(records: list[dict[str, Any]], stage: str, promote_top: int) -> dict[str, Any]:
    cleaned = [validate_known_only_record(r, expected_stage=stage) for r in records]
    if not cleaned:
        raise ValueError("cannot rank an empty result set")
    pair = cleaned[0]["canonical_pair"]
    if any(r["canonical_pair"] != pair for r in cleaned):
        raise ValueError("rank_pair received multiple canonical pairs")

    def key(r: dict[str, Any]) -> tuple[Any, ...]:
        feasible = r["val_min_class_f1"] >= 0.90
        return (
            1 if feasible else 0,
            r["val_macro_f1"],
            r["val_min_class_f1"],
            str(r["trial_id"]),
        )

    ranked = sorted(cleaned, key=key, reverse=True)
    top = ranked[: max(1, promote_top)]
    winner = ranked[0]
    gate_pass = winner["val_macro_f1"] >= 0.95 and winner["val_min_class_f1"] >= 0.90
    frozen = stage == "finalist" and gate_pass
    return {
        "canonical_pair": pair,
        "stage": stage,
        "selection_evidence": "known_validation_only",
        "ranking_rule": "feasible_min_class_first_then_val_macro_f1_then_val_min_class_f1",
        "gate": {"val_macro_f1_min": 0.95, "val_min_class_f1_min": 0.90},
        "winner_trial_id": winner["trial_id"],
        "winner_config_path": winner["config_path"],
        "winner_val_macro_f1": winner["val_macro_f1"],
        "winner_val_min_class_f1": winner["val_min_class_f1"],
        "gate_pass": gate_pass,
        "frozen": frozen,
        "promotion_trial_ids": [r["trial_id"] for r in top],
        "promotion_config_paths": [r["config_path"] for r in top],
        "ranked_trial_ids": [r["trial_id"] for r in ranked],
    }


def rank_results(records: list[dict[str, Any]], stage: str, promote_top: int) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        cleaned = validate_known_only_record(record, expected_stage=stage)
        groups[cleaned["canonical_pair"]].append(cleaned)
    pairs = [rank_pair(groups[pair], stage, promote_top) for pair in sorted(groups)]
    return {
        "schema": "padataset.l2o-hpo-ranking.v2",
        "stage": stage,
        "selection_evidence": "known_validation_only",
        "target_metrics_used": False,
        "test_metrics_used": False,
        "pairs": pairs,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--stage", choices=sorted(ALLOWED_STAGES), required=True)
    ap.add_argument("--promote-top", type=int, required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    payload = json.loads(Path(args.results).read_text(encoding="utf-8"))
    records = payload["records"] if isinstance(payload, dict) else payload
    if not isinstance(records, list):
        raise SystemExit("results must be a list or an object containing records")
    result = rank_results(records, args.stage, args.promote_top)
    Path(args.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pairs": len(result["pairs"]), "out": args.out}, sort_keys=True))


if __name__ == "__main__":
    main()
