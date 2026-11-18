#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
from typing import Any

PA_ORDER = ["PA1", "PA2", "PA3", "PA4", "PA8"]
HPO_FIELDS = (
    "lr",
    "weight_decay",
    "lambda_center",
    "label_smoothing",
    "entropy_loss_weight",
    "mlp_dropout",
    "grad_clip_norm",
    "scheduler_name",
    "batch_size",
)
STAGE_EPOCHS = {"screen": 8, "refine": 24, "finalist": 60}
STAGE_TRANSITIONS = {"screen": "refine", "refine": "finalist"}


def canonical_pair_key(a: str, b: str) -> str:
    order = {pa: i for i, pa in enumerate(PA_ORDER)}
    if a not in order or b not in order or a == b:
        raise ValueError(f"invalid PA pair: {a!r}, {b!r}")
    x, y = sorted((a, b), key=order.__getitem__)
    return f"{x}-{y}"


def _unit(seed: int, trial_index: int, field: str) -> float:
    raw = hashlib.sha256(f"{seed}:{trial_index}:{field}".encode("utf-8")).digest()
    value = int.from_bytes(raw[:8], "big")
    return value / float(2**64)


def _choice_index(seed: int, trial_index: int, field: str, n: int) -> int:
    raw = hashlib.sha256(f"{seed}:{trial_index}:{field}:choice".encode("utf-8")).digest()
    return int.from_bytes(raw[:8], "big") % n


def candidate_params(space: dict[str, Any], trial_index: int, seed: int) -> dict[str, Any]:
    params: dict[str, Any] = {}
    search = space["search_space"]
    for field in HPO_FIELDS:
        spec = search[field]
        typ = spec["type"]
        if typ == "categorical":
            values = spec["values"]
            params[field] = values[_choice_index(seed, trial_index, field, len(values))]
        elif typ == "log_float":
            low = float(spec["low"])
            high = float(spec["high"])
            if not (0 < low < high):
                raise ValueError(f"invalid log_float bounds for {field}")
            u = _unit(seed, trial_index, field)
            params[field] = float(f"{math.exp(math.log(low) + u * (math.log(high) - math.log(low))):.12g}")
        else:
            raise ValueError(f"unsupported search-space type {typ!r} for {field}")
    return params


def validate_base_config(base: dict[str, Any], space: dict[str, Any]) -> str:
    target = base.get("target_unknown_pa")
    surrogate = base.get("surrogate_open_pa")
    pair = canonical_pair_key(target, surrogate)
    expected_known = [pa for pa in PA_ORDER if pa not in {target, surrogate}]
    if base.get("known_pas_l2o") != expected_known:
        raise ValueError(
            f"{pair}: known_pas_l2o must be canonical complement {expected_known}, got {base.get('known_pas_l2o')}"
        )
    inv = space["invariants"]
    checks = {
        "cache_len": inv["cache_len"],
        "split_mode": inv["split_mode"],
        "open_val_frac": inv["open_val_frac"],
        "early_stopping_mode": inv["early_stopping_mode"],
        "quarantine_target_until_test": inv["quarantine_target_until_test"],
        "deterministic_training": inv["deterministic_training"],
        "deterministic_profile": inv["deterministic_profile"],
    }
    for key, expected in checks.items():
        if base.get(key) != expected:
            raise ValueError(f"{pair}: base invariant drift for {key}: {base.get(key)!r} != {expected!r}")
    if base.get("force_rebuild_cache") is not False or base.get("skip_cache_build") is not True:
        raise ValueError(f"{pair}: HPO base config must reuse the trusted cache")
    if base.get("use_timestamped_run_dir") is not False:
        raise ValueError(f"{pair}: deterministic HPO requires use_timestamped_run_dir=false")
    return pair


def build_trial_config(
    base: dict[str, Any],
    space: dict[str, Any],
    params: dict[str, Any],
    stage: str,
    trial_index: int,
    seed: int,
) -> dict[str, Any]:
    if stage not in STAGE_EPOCHS:
        raise ValueError(f"unsupported HPO stage: {stage}")
    pair = validate_base_config(base, space)
    cfg = copy.deepcopy(base)
    for field in HPO_FIELDS:
        cfg[field] = params[field]
    trial_id = f"{pair}__t{trial_index:03d}"
    cfg["epochs"] = STAGE_EPOCHS[stage]
    cfg["run_name"] = f"l2o_hpo_v2_{pair.replace('-', '_')}_t{trial_index:03d}_{stage}"
    cfg["save_root"] = "results_pa_ota_l2o_hpo_v2"
    cfg["paper_set"] = "L2O_HPO_PILOT_V2"
    cfg["family_tag"] = "l2o_hpo_pilot_v2"
    cfg["run_group"] = "l2o_hpo_pilot_v2"
    cfg["catalog_family_name"] = "l2o_hpo_pilot_v2"
    cfg["overwrite_existing_run"] = False
    cfg["hpo_trial"] = {
        "schema": "padataset.l2o-hpo-trial.v2",
        "trial_id": trial_id,
        "canonical_pair": pair,
        "trial_index": trial_index,
        "candidate_seed": seed,
        "stage": stage,
        "selection_evidence": "known_validation_only",
        "target_metrics_allowed_for_selection": False,
        "test_metrics_allowed_for_selection": False,
        "params": copy.deepcopy(params),
    }
    cfg["notes"] = (
        "MTH602 L2O HPO pilot v2. Hyperparameters are deterministically predeclared; "
        "ranking/promotion uses known-validation evidence only. True target remains quarantined "
        "until frozen final evaluation."
    )
    validate_base_config(cfg, space)
    return cfg


def promote_trial_config(source: dict[str, Any], space: dict[str, Any], next_stage: str) -> dict[str, Any]:
    meta = source.get("hpo_trial") or {}
    current = meta.get("stage")
    if STAGE_TRANSITIONS.get(current) != next_stage:
        raise ValueError(f"invalid HPO promotion {current!r} -> {next_stage!r}")
    pair = validate_base_config(source, space)
    params = meta.get("params")
    if not isinstance(params, dict) or any(field not in params for field in HPO_FIELDS):
        raise ValueError("source HPO config lacks frozen parameter set")
    trial_index = int(meta["trial_index"])
    seed = int(meta["candidate_seed"])
    promoted = build_trial_config(source, space, params, next_stage, trial_index, seed)
    if promoted["hpo_trial"]["canonical_pair"] != pair:
        raise AssertionError("canonical pair drift during promotion")
    promoted["hpo_trial"]["promoted_from_stage"] = current
    promoted["hpo_trial"]["promoted_from_run_name"] = source["run_name"]
    return promoted


def _sha256_json(payload: Any) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def screen_cli(args: argparse.Namespace) -> None:
    space = _load(args.space)
    max_trials = next(x["max_trials"] for x in space["resource_ladder"] if x["stage"] == "screen")
    start = args.wave_index * args.wave_size
    stop = min(start + args.wave_size, max_trials)
    if start >= max_trials:
        raise SystemExit(f"wave starts beyond screen max_trials={max_trials}")

    bases: dict[str, tuple[Path, dict[str, Any]]] = {}
    for raw in args.base:
        key, sep, path_text = raw.partition("=")
        if not sep:
            raise SystemExit("--base must be CANONICAL_PAIR=path")
        path = Path(path_text)
        cfg = _load(path)
        actual = validate_base_config(cfg, space)
        if key != actual:
            raise SystemExit(f"--base key {key!r} does not match config pair {actual!r}")
        bases[key] = (path, cfg)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    for trial_index in range(start, stop):
        params = candidate_params(space, trial_index, args.seed)
        for pair in sorted(bases, key=lambda p: tuple(PA_ORDER.index(x) for x in p.split("-"))):
            base_path, base = bases[pair]
            cfg = build_trial_config(base, space, params, "screen", trial_index, args.seed)
            out_path = out_dir / f"{cfg['run_name']}.json"
            out_path.write_text(json.dumps(cfg, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            entries.append({
                "trial_id": cfg["hpo_trial"]["trial_id"],
                "canonical_pair": pair,
                "stage": "screen",
                "trial_index": trial_index,
                "config_path": str(out_path),
                "config_sha256": _sha256_json(cfg),
                "base_config_path": str(base_path),
                "params": params,
            })

    manifest = {
        "schema": "padataset.l2o-hpo-wave-manifest.v2",
        "stage": "screen",
        "wave_index": args.wave_index,
        "wave_size": args.wave_size,
        "candidate_seed": args.seed,
        "trial_index_start": start,
        "trial_index_stop_exclusive": stop,
        "selection_evidence": "known_validation_only",
        "space_sha256": _sha256_json(space),
        "entries": entries,
    }
    manifest_path = Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.emit_manifest_json:
        print(json.dumps(manifest, sort_keys=True))
    else:
        print(json.dumps({"configs": len(entries), "manifest": str(manifest_path)}, sort_keys=True))


def promote_cli(args: argparse.Namespace) -> None:
    space = _load(args.space)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    for raw in args.source_config:
        source_path = Path(raw)
        source = _load(source_path)
        cfg = promote_trial_config(source, space, args.stage)
        out_path = out_dir / f"{cfg['run_name']}.json"
        out_path.write_text(json.dumps(cfg, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        entries.append({
            "trial_id": cfg["hpo_trial"]["trial_id"],
            "canonical_pair": cfg["hpo_trial"]["canonical_pair"],
            "stage": args.stage,
            "config_path": str(out_path),
            "config_sha256": _sha256_json(cfg),
            "source_config_path": str(source_path),
            "params": cfg["hpo_trial"]["params"],
        })
    manifest = {
        "schema": "padataset.l2o-hpo-promotion-manifest.v2",
        "stage": args.stage,
        "selection_evidence": "known_validation_only",
        "entries": entries,
    }
    manifest_path = Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"configs": len(entries), "manifest": str(manifest_path)}, sort_keys=True))


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)

    screen = sub.add_parser("screen")
    screen.add_argument("--space", required=True)
    screen.add_argument("--base", action="append", required=True)
    screen.add_argument("--wave-index", type=int, required=True)
    screen.add_argument("--wave-size", type=int, default=8)
    screen.add_argument("--seed", type=int, default=6022026)
    screen.add_argument("--out-dir", required=True)
    screen.add_argument("--manifest", required=True)
    screen.set_defaults(func=screen_cli)

    promote = sub.add_parser("promote")
    promote.add_argument("--space", required=True)
    promote.add_argument("--source-config", action="append", required=True)
    promote.add_argument("--stage", choices=["refine", "finalist"], required=True)
    promote.add_argument("--out-dir", required=True)
    promote.add_argument("--manifest", required=True)
    promote.set_defaults(func=promote_cli)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
