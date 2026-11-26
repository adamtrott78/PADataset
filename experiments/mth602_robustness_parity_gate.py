#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
METRICS = (
    "known_reject_rate",
    "unknown_precision",
    "unknown_recall",
    "unknown_f1",
    "osr_acc",
    "osr_macro_f1",
    "unknown_auroc",
)
METHODS = ("DQNGuard", "DQN-IDS-style", "VarMax")
PRINT_LOCK = threading.Lock()


def log(msg: str) -> None:
    with PRINT_LOCK:
        print(msg, flush=True)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def atomic_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def validate_cell(cell: dict[str, Any], pipeline_root: Path) -> tuple[Path, list[dict[str, Any]]]:
    run_name = str(cell["run_name"])
    run_dir = pipeline_root / "backbones" / run_name
    cached_dir = pipeline_root / "osr" / run_name

    required = (
        run_dir / "config.json",
        run_dir / "best_model.pt",
        run_dir / "train_complete.json",
        run_dir / "osr_posttrain_bundle" / "frozen" / "methods_frozen.json",
        run_dir / "osr_posttrain_bundle" / "target_cache" / "manifest.json",
        cached_dir / "osr_complete.json",
        cached_dir / "result.json",
    )
    missing = [str(p) for p in required if not p.is_file()]
    if missing:
        raise RuntimeError(f"{run_name}: missing parity inputs: {missing}")

    cfg = read_json(run_dir / "config.json")
    rr = cfg.get("robustness_replication") or {}
    expected_pair = list(cell["canonical_pair"])
    raw_pair = rr.get("canonical_pair")
    if isinstance(raw_pair, str):
        observed_pair = raw_pair.split("-")
    elif isinstance(raw_pair, (list, tuple)):
        observed_pair = list(raw_pair)
    else:
        observed_pair = []
    if str(cfg.get("run_name")) != run_name:
        raise RuntimeError(f"{run_name}: config run_name drift")
    if observed_pair != expected_pair:
        raise RuntimeError(
            f"{run_name}: canonical pair drift expected={expected_pair} observed={observed_pair}"
        )
    if int(rr.get("partition_seed", -1)) != int(cell["partition_seed"]):
        raise RuntimeError(f"{run_name}: partition seed drift")
    if int(rr.get("training_seed", -1)) != int(cell["training_seed"]):
        raise RuntimeError(f"{run_name}: training seed drift")
    if int(rr.get("dqn_seed", -1)) != 42:
        raise RuntimeError(f"{run_name}: DQN seed drift")
    if rr.get("final_science_eligible") is not False:
        raise RuntimeError(f"{run_name}: smoke cell unexpectedly final-science eligible")

    frozen = read_json(run_dir / "osr_posttrain_bundle" / "frozen" / "methods_frozen.json")
    target = read_json(run_dir / "osr_posttrain_bundle" / "target_cache" / "manifest.json")
    cached_done = read_json(cached_dir / "osr_complete.json")
    if frozen.get("status") != "SUCCESS":
        raise RuntimeError(f"{run_name}: methods_frozen status is not SUCCESS")
    if frozen.get("target_test_consumed_before_method_fit") is not False:
        raise RuntimeError(f"{run_name}: target-test firewall drift in freeze receipt")
    if target.get("methods_frozen_before_target_test") is not True:
        raise RuntimeError(f"{run_name}: target cache predates method freeze")
    if target.get("target_test_consumed_before_method_fit") is not False:
        raise RuntimeError(f"{run_name}: target-test firewall drift in target cache")
    if cached_done.get("status") != "SUCCESS":
        raise RuntimeError(f"{run_name}: cached OSR is not complete")

    checkpoint_sha = sha256_file(run_dir / "best_model.pt")
    config_sha = sha256_file(run_dir / "config.json")
    if frozen.get("checkpoint_sha256") != checkpoint_sha:
        raise RuntimeError(f"{run_name}: frozen-method checkpoint binding mismatch")
    if frozen.get("config_sha256") != config_sha:
        raise RuntimeError(f"{run_name}: frozen-method config binding mismatch")
    if target.get("checkpoint_sha256") != checkpoint_sha:
        raise RuntimeError(f"{run_name}: target-cache checkpoint binding mismatch")
    if target.get("config_sha256") != config_sha:
        raise RuntimeError(f"{run_name}: target-cache config binding mismatch")

    cached_rows = read_json(cached_dir / "result.json")
    if not isinstance(cached_rows, list) or len(cached_rows) != 6:
        raise RuntimeError(f"{run_name}: expected exactly six cached method-direction rows")
    expected = {
        (target_pa, surrogate_pa, method)
        for target_pa, surrogate_pa in (
            (expected_pair[0], expected_pair[1]),
            (expected_pair[1], expected_pair[0]),
        )
        for method in METHODS
    }
    observed = {
        (str(r.get("target")), str(r.get("surrogate")), str(r.get("method")))
        for r in cached_rows
    }
    if observed != expected:
        raise RuntimeError(f"{run_name}: cached result topology drift: {sorted(observed)}")
    return run_dir, cached_rows


def run_command(cmd: list[str], env: dict[str, str], log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as f:
        proc = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            env=env,
            stdout=f,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    if proc.returncode != 0:
        tail = "\n".join(log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-30:])
        raise RuntimeError(
            f"command failed rc={proc.returncode}: {' '.join(cmd)}\n--- log tail ---\n{tail}"
        )


def maybe_run_dqnguard(
    *,
    run_dir: Path,
    target: str,
    surrogate: str,
    out_dir: Path,
    data_root: Path,
    env: dict[str, str],
    fresh: bool,
) -> dict[str, str]:
    csv_path = out_dir / "osr_summary.csv"
    if fresh and out_dir.exists():
        shutil.rmtree(out_dir)
    if not csv_path.is_file():
        out_dir.mkdir(parents=True, exist_ok=True)
        cmd = [
            sys.executable,
            str(REPO_ROOT / "experiments" / "pa_eval_dqn_guard_surrogate_open.py"),
            "--run-dir", str(run_dir),
            "--checkpoint", "best_model",
            "--out-dir", str(out_dir),
            "--target-open-pa", target,
            "--surrogate-open-pa", surrogate,
            "--mode", "var_energy",
            "--decision-mode", "score_threshold",
            "--max-known-reject-cal", "0.05",
            "--known-cap", "625",
            "--open-cap", "625",
            "--device", "cuda",
            "--batch-size", "128",
            "--num-workers", "0",
            "--data-root", str(data_root),
        ]
        run_command(cmd, env, out_dir / "canonical.log")
    rows = read_csv_rows(csv_path)
    if len(rows) != 1:
        raise RuntimeError(f"{csv_path}: expected exactly one DQNGuard row")
    row = rows[0]
    if json.loads(row["target_unknown_pas"]) != [target]:
        raise RuntimeError(f"{csv_path}: DQNGuard target drift")
    if row["surrogate_open_pa"] != surrogate:
        raise RuntimeError(f"{csv_path}: DQNGuard surrogate drift")
    if row["decision_mode"] != "score_threshold":
        raise RuntimeError(f"{csv_path}: DQNGuard decision-mode drift")
    if row["mix_true_open"].lower() not in {"false", "0"}:
        raise RuntimeError(f"{csv_path}: DQNGuard true-open mixing drift")
    return row


def maybe_run_controls(
    *,
    run_dir: Path,
    target: str,
    surrogate: str,
    out_dir: Path,
    data_root: Path,
    env: dict[str, str],
    fresh: bool,
) -> dict[str, dict[str, str]]:
    csv_path = out_dir / "control_summary.csv"
    if fresh and out_dir.exists():
        shutil.rmtree(out_dir)
    if not csv_path.is_file():
        out_dir.mkdir(parents=True, exist_ok=True)
        cmd = [
            sys.executable,
            str(REPO_ROOT / "experiments" / "pa_eval_l2o_controls_v1.py"),
            "--run-dir", str(run_dir),
            "--checkpoint", "best_model",
            "--out-dir", str(out_dir),
            "--policy", str(REPO_ROOT / "manifests" / "l2o_control_eval_policy_v1.json"),
            "--target-open-pa", target,
            "--surrogate-open-pa", surrogate,
            "--device", "cuda",
            "--batch-size", "128",
            "--num-workers", "0",
            "--data-root", str(data_root),
        ]
        run_command(cmd, env, out_dir / "canonical.log")
    rows = read_csv_rows(csv_path)
    by_family = {r["control_family"]: r for r in rows}
    if set(by_family) != {"dqn_ids_style", "varmax"}:
        raise RuntimeError(f"{csv_path}: canonical control method topology drift")
    for family, row in by_family.items():
        if json.loads(row["target_unknown_pas"]) != [target]:
            raise RuntimeError(f"{csv_path}: {family} target drift")
        if row["external_surrogate"] != surrogate:
            raise RuntimeError(f"{csv_path}: {family} surrogate drift")
        if row["target_labels_used_for_tuning"].lower() not in {"false", "0"}:
            raise RuntimeError(f"{csv_path}: {family} target-label tuning drift")
        if row["target_test_consumed_before_final_eval"].lower() not in {"false", "0"}:
            raise RuntimeError(f"{csv_path}: {family} target-test firewall drift")
    return by_family


def compare_method(
    *,
    run_name: str,
    partition_seed: int,
    training_seed: int,
    target: str,
    surrogate: str,
    method: str,
    cached: dict[str, Any],
    canonical: dict[str, str],
    tolerance: float,
) -> dict[str, Any]:
    deltas = {}
    cached_values = {}
    canonical_values = {}
    for metric in METRICS:
        cv = float(cached[metric])
        rv = float(canonical[metric])
        cached_values[metric] = cv
        canonical_values[metric] = rv
        deltas[metric] = abs(cv - rv)
    max_delta = max(deltas.values()) if deltas else 0.0
    return {
        "run_name": run_name,
        "partition_seed": int(partition_seed),
        "training_seed": int(training_seed),
        "target": target,
        "surrogate": surrogate,
        "direction": f"{target}<-{surrogate}",
        "method": method,
        "cached": cached_values,
        "canonical": canonical_values,
        "abs_delta": deltas,
        "max_abs_delta": max_delta,
        "tolerance": tolerance,
        "pass": bool(max_delta <= tolerance),
    }


def run_cell(
    *,
    cell: dict[str, Any],
    gpu: int,
    pipeline_root: Path,
    data_root: Path,
    out_root: Path,
    tolerance: float,
    fresh: bool,
) -> list[dict[str, Any]]:
    run_name = str(cell["run_name"])
    pair = list(cell["canonical_pair"])
    run_dir, cached_rows = validate_cell(cell, pipeline_root)
    cached = {
        (str(r["target"]), str(r["surrogate"]), str(r["method"])): r
        for r in cached_rows
    }

    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = str(gpu)
    env["OMP_NUM_THREADS"] = "4"
    env["MKL_NUM_THREADS"] = "4"
    env["OPENBLAS_NUM_THREADS"] = "4"
    env["NUMEXPR_NUM_THREADS"] = "4"
    env["PYTHONUNBUFFERED"] = "1"

    results: list[dict[str, Any]] = []
    cell_root = out_root / run_name
    for target, surrogate in ((pair[0], pair[1]), (pair[1], pair[0])):
        tag = f"{target}_from_{surrogate}"
        log(f"[GPU{gpu}] CANONICAL START {run_name} {target}<-{surrogate}")

        dg = maybe_run_dqnguard(
            run_dir=run_dir,
            target=target,
            surrogate=surrogate,
            out_dir=cell_root / tag / "dqnguard",
            data_root=data_root,
            env=env,
            fresh=fresh,
        )
        controls = maybe_run_controls(
            run_dir=run_dir,
            target=target,
            surrogate=surrogate,
            out_dir=cell_root / tag / "controls",
            data_root=data_root,
            env=env,
            fresh=fresh,
        )
        canonical_rows = {
            "DQNGuard": dg,
            "DQN-IDS-style": controls["dqn_ids_style"],
            "VarMax": controls["varmax"],
        }
        for method in METHODS:
            result = compare_method(
                run_name=run_name,
                partition_seed=int(cell["partition_seed"]),
                training_seed=int(cell["training_seed"]),
                target=target,
                surrogate=surrogate,
                method=method,
                cached=cached[(target, surrogate, method)],
                canonical=canonical_rows[method],
                tolerance=tolerance,
            )
            results.append(result)
            log(
                f"[GPU{gpu}] {run_name} {target}<-{surrogate} {method} "
                f"max_delta={result['max_abs_delta']:.3e} "
                f"{'PASS' if result['pass'] else 'FAIL'}"
            )
        atomic_json(cell_root / tag / "parity.json", {
            "schema": "padataset.mth602-robustness-parity-direction.v1",
            "run_name": run_name,
            "direction": f"{target}<-{surrogate}",
            "gpu": gpu,
            "rows": results[-3:],
        })
    return results


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "run_name", "partition_seed", "training_seed", "direction", "method",
        "cached_unknown_f1", "canonical_unknown_f1", "unknown_f1_abs_delta",
        "max_abs_delta", "tolerance", "pass",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({
                "run_name": row["run_name"],
                "partition_seed": row["partition_seed"],
                "training_seed": row["training_seed"],
                "direction": row["direction"],
                "method": row["method"],
                "cached_unknown_f1": row["cached"]["unknown_f1"],
                "canonical_unknown_f1": row["canonical"]["unknown_f1"],
                "unknown_f1_abs_delta": row["abs_delta"]["unknown_f1"],
                "max_abs_delta": row["max_abs_delta"],
                "tolerance": row["tolerance"],
                "pass": row["pass"],
            })


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--manifest",
        default=str(REPO_ROOT / "manifests" / "mth602_robustness_parity_smoke_v1.json"),
    )
    ap.add_argument(
        "--pipeline-root",
        default=str(Path.home() / ".cache" / "workspace-control" / "mth602-robustness-pipeline"),
    )
    ap.add_argument(
        "--data-root",
        default="/srv/workspace-ci/padataset/trusted-cache/scientific-data/ota_core_high_run01_len16384_v1",
    )
    ap.add_argument("--fresh", action="store_true")
    args = ap.parse_args()

    manifest_path = Path(args.manifest).resolve()
    manifest = read_json(manifest_path)
    if manifest.get("schema") != "padataset.mth602-robustness-parity-smoke.v1":
        raise SystemExit("parity manifest schema mismatch")
    if manifest.get("status") != "READY_FOR_LOCAL_PARITY_GATE":
        raise SystemExit("parity manifest is not ready")
    if manifest.get("methods") != list(METHODS):
        raise SystemExit("parity method set/order drift")
    if manifest.get("metrics") != list(METRICS):
        raise SystemExit("parity metric set/order drift")
    inv = manifest.get("invariants") or {}
    if inv.get("checkpoint") != "best_model" or int(inv.get("dqn_seed", -1)) != 42:
        raise SystemExit("parity frozen checkpoint/DQN seed drift")
    if inv.get("target_labels_used_for_tuning") is not False:
        raise SystemExit("parity manifest permits target-label tuning")
    if inv.get("canonical_state_mutation") is not False or inv.get("retraining") is not False:
        raise SystemExit("parity manifest permits forbidden mutation/retraining")

    pipeline_root = Path(args.pipeline_root).expanduser().resolve()
    data_root = Path(args.data_root).resolve()
    if not data_root.is_dir():
        raise SystemExit(f"trusted data root does not exist: {data_root}")
    tolerance = float(manifest["abs_tolerance"])
    out_root = pipeline_root / "parity"
    out_root.mkdir(parents=True, exist_ok=True)

    lanes = manifest.get("lanes") or []
    if len(lanes) != 2 or sorted(int(x["gpu"]) for x in lanes) != [0, 1]:
        raise SystemExit("parity manifest must declare exactly GPU0 and GPU1 lanes")
    cells = [c for lane in lanes for c in lane.get("cells", [])]
    if len(cells) != 4 or len({c["run_name"] for c in cells}) != 4:
        raise SystemExit("parity manifest must pin exactly four distinct smoke backbones")

    # Fail closed on all provenance checks before launching any canonical evaluator.
    for cell in cells:
        validate_cell(cell, pipeline_root)

    started = time.time()
    log(
        f"PARITY_GATE_START | cells=4 | method_direction_rows=24 | "
        f"metric_comparisons=168 | tolerance={tolerance:.1e}"
    )

    all_rows: list[dict[str, Any]] = []

    def run_lane(lane: dict[str, Any]) -> list[dict[str, Any]]:
        gpu = int(lane["gpu"])
        lane_rows: list[dict[str, Any]] = []
        for cell in lane.get("cells", []):
            lane_rows.extend(
                run_cell(
                    cell=cell,
                    gpu=gpu,
                    pipeline_root=pipeline_root,
                    data_root=data_root,
                    out_root=out_root,
                    tolerance=tolerance,
                    fresh=args.fresh,
                )
            )
        return lane_rows

    errors: list[str] = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        future_map = {pool.submit(run_lane, lane): int(lane["gpu"]) for lane in lanes}
        for fut in as_completed(future_map):
            gpu = future_map[fut]
            try:
                all_rows.extend(fut.result())
            except Exception as exc:
                errors.append(f"GPU{gpu}: {type(exc).__name__}: {exc}")
                log(f"[GPU{gpu}] PARITY LANE ERROR: {type(exc).__name__}: {exc}")

    all_rows.sort(key=lambda r: (r["run_name"], r["target"], r["surrogate"], r["method"]))
    failed = [r for r in all_rows if not r["pass"]]
    expected_rows = 24
    metric_comparisons = len(all_rows) * len(METRICS)
    max_delta = max((r["max_abs_delta"] for r in all_rows), default=None)
    status = (
        "PASS"
        if not errors and len(all_rows) == expected_rows and not failed
        else "FAIL"
    )

    report = {
        "schema": "padataset.mth602-robustness-parity-report.v1",
        "status": status,
        "manifest": str(manifest_path),
        "candidate_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
        ).strip(),
        "cells": 4,
        "directions": 8,
        "methods": list(METHODS),
        "metrics": list(METRICS),
        "expected_method_direction_rows": expected_rows,
        "observed_method_direction_rows": len(all_rows),
        "metric_comparisons": metric_comparisons,
        "abs_tolerance": tolerance,
        "max_abs_delta": max_delta,
        "failed_method_direction_rows": len(failed),
        "errors": errors,
        "target_labels_used_for_tuning": False,
        "retraining_performed": False,
        "canonical_state_modified": False,
        "elapsed_sec": time.time() - started,
        "rows": all_rows,
    }
    atomic_json(out_root / "parity_report.json", report)
    write_csv(out_root / "parity_summary.csv", all_rows)

    log(
        f"PARITY_GATE={status} | rows={len(all_rows)}/{expected_rows} | "
        f"metric_comparisons={metric_comparisons}/168 | "
        f"max_abs_delta={max_delta if max_delta is not None else '-'} | "
        f"failed_rows={len(failed)} | errors={len(errors)}"
    )
    log(f"REPORT={out_root / 'parity_report.json'}")
    log(f"SUMMARY={out_root / 'parity_summary.csv'}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
