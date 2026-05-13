#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from evaluate import evaluate_multiple_osr_methods_on_run, choose_osr_calibration_splits
from varmax_osr import VarMaxOSR, DEFAULT_PAIR_MAP


def grid_values(kind: str) -> Dict[str, Any]:
    kind = kind.lower()
    if kind == "smoke":
        return {
            "top2_grid": [0.90, 0.95, 0.98],
            "var_lo_grid": [1.0, 5.0, 10.0],
            "var_hi_grid": [90.0, 95.0, 99.0],
            "energy_lo_grid": [1.0, 5.0, 10.0],
            "energy_hi_grid": [90.0, 95.0, 99.0],
        }
    if kind == "full":
        return {
            "top2_grid": None,
            "var_lo_grid": None,
            "var_hi_grid": None,
            "energy_lo_grid": None,
            "energy_hi_grid": None,
        }
    raise ValueError(f"Unknown sweep grid: {kind}")


def make_calibration_builder(mode: str, sweep_grid: str):
    grids = grid_values(sweep_grid)

    def builder(payload, extras):
        if mode == "oracle":
            known_cal, open_cal = choose_osr_calibration_splits(
                payload,
                extras,
                prefer_balanced=True,
            )
        else:
            known_cal = extras.get("val_known_balanced", None) or payload.val_known
            open_cal = None

        out = {
            "mode": "sweep",
            "calibration_mode": mode,
            "calibration_known": known_cal,
            "calibration_open": open_cal,
            "pair_map": DEFAULT_PAIR_MAP,
            "surrogate_fit_frac": 0.50,
            "surrogate_guard_frac": 0.25,
            "surrogate_seed": int(payload.meta.get("seed", 0) or 0),
            "known_floor_ratio": 0.95,
            "unknown_recall_floor": 0.60,
            "per_class_floor_ratio": 0.95,
            "top_k": 10,
        }
        out.update(grids)
        return out

    return builder


def make_method_specs(modes: list[str], sweep_grid: str):
    specs = []
    for mode in modes:
        mode = mode.strip()
        if not mode:
            continue

        specs.append({
            "name": f"varmax_{mode}_{sweep_grid}",
            "factory": lambda: VarMaxOSR(
                temperature=1.0,
                use_energy=True,
                fit_on="predicted_class",
                min_samples_per_class=5,
            ),
            "calibration_builder": make_calibration_builder(mode, sweep_grid),
        })
    return specs


def compact_method_row(row: Dict[str, Any], result: Dict[str, Any], run_meta: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(run_meta)
    out.update(row)

    params = result.get("params", {}) or {}
    best = params.get("best_sweep_result") or {}

    out["calibration_mode"] = params.get("calibration_mode")
    out["no_feasible_solution"] = params.get("no_feasible_solution")
    out["baseline_known_closed_acc"] = params.get("baseline_known_closed_acc")
    out["baseline_known_closed_macro_f1"] = params.get("baseline_known_closed_macro_f1")
    out["sweep_candidates"] = len(params.get("best_sweep_result", {}) or {}) if False else len(result.get("params", {}).get("top_feasible_results", []) or []) + len(result.get("params", {}).get("top_fallback_results", []) or [])
    out["top_feasible_count_saved"] = len(params.get("top_feasible_results", []) or [])
    out["top_fallback_count_saved"] = len(params.get("top_fallback_results", []) or [])

    if best:
        out["best_regime"] = best.get("regime")
        out["best_spec_name"] = best.get("spec_name")
        out["best_true_unknown_name"] = best.get("true_unknown_name")
        out["best_heldout_class_name"] = best.get("heldout_class_name")
        out["best_is_structure_aligned"] = best.get("is_structure_aligned")
        out["best_top2_threshold"] = best.get("top2_threshold")
        out["best_var_percentiles"] = json.dumps(best.get("var_percentiles"))
        out["best_energy_percentiles"] = json.dumps(best.get("energy_percentiles"))
        out["best_feasible"] = best.get("feasible")
        out["best_known_floor_ratio"] = best.get("known_floor_ratio")
        out["best_per_class_floor_ratio"] = best.get("per_class_floor_ratio")

    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--checkpoint", default="best_model")
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--modes", default="oracle,surrogate_all")
    ap.add_argument("--sweep-grid", choices=["smoke", "full"], default="smoke")
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--num-workers", type=int, default=0)
    ap.add_argument("--device", default=None)
    ap.add_argument("--data-root", default=None)
    args = ap.parse_args()

    # GNU parallel may shell-quote replacement fields containing commas,
    # producing values like "'oracle,surrogate_all'".
    args.modes = str(args.modes).strip().strip("'\"")

    t0 = time.time()
    run_dir = Path(args.run_dir)
    run_name = run_dir.name
    out_dir = Path(args.out_dir) if args.out_dir else Path("results_pa_osr_eval") / run_name
    out_dir.mkdir(parents=True, exist_ok=True)

    progress_path = out_dir / "osr_progress.json"
    error_path = out_dir / "osr_error.json"

    def write_progress(**payload):
        payload.setdefault("run_name", run_name)
        payload.setdefault("run_dir", str(run_dir))
        payload.setdefault("checkpoint", args.checkpoint)
        payload.setdefault("time", time.strftime("%Y-%m-%dT%H:%M:%S%z"))
        tmp = progress_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2))
        tmp.replace(progress_path)

    print(
        f"OSR START | run_name={run_name} | checkpoint={args.checkpoint} | modes={args.modes} | grid={args.sweep_grid}",
        flush=True,
    )
    write_progress(phase="start", pct=0.0)

    try:
        modes = [x.strip().strip("'\"") for x in args.modes.split(",") if x.strip().strip("'\"")]
        specs = make_method_specs(modes=modes, sweep_grid=args.sweep_grid)

        write_progress(phase="building_payload", pct=10.0)

        result = evaluate_multiple_osr_methods_on_run(
            run_dir=str(run_dir),
            method_specs=specs,
            checkpoint_tag=args.checkpoint,
            batch_size=args.batch_size,
            num_workers=args.num_workers,
            pin_memory=True,
            device=args.device,
            data_root=args.data_root,
            unknown_label_name="unknown",
        )

        write_progress(phase="writing_outputs", pct=90.0)

        handle = result["handle"]
        payload = result["payload"]

        run_meta = {
            "run_name": run_name,
            "run_dir": str(run_dir),
            "checkpoint": args.checkpoint,
            "sweep_grid": args.sweep_grid,
            "paper_set": handle.config.get("paper_set"),
            "family_tag": handle.config.get("family_tag"),
            "unknown_pas": json.dumps(handle.config.get("unknown_pas", [])),
            "seed": handle.config.get("seed"),
            "source_type": handle.config.get("source_type"),
            "source_name": handle.config.get("source_name"),
            "dataset_tag": handle.config.get("dataset_tag"),
            "noise_tag": handle.config.get("noise_tag"),
            "num_classes": payload.meta.get("num_classes"),
            "class_names": json.dumps(payload.meta.get("class_names")),
        }

        rows = []
        for raw_row in result["rows"]:
            method_name = raw_row["method"]
            fitted = result["fitted"][method_name]
            rows.append(compact_method_row(raw_row, fitted, run_meta))

        df = pd.DataFrame(rows)
        csv_path = out_dir / "osr_summary.csv"
        df.to_csv(csv_path, index=False)

        complete = {
            "run_name": run_name,
            "run_dir": str(run_dir),
            "checkpoint": args.checkpoint,
            "modes": modes,
            "sweep_grid": args.sweep_grid,
            "out_dir": str(out_dir),
            "csv_path": str(csv_path),
            "rows": len(rows),
            "elapsed_sec": time.time() - t0,
        }
        (out_dir / "osr_complete.json").write_text(json.dumps(complete, indent=2))

        write_progress(phase="done", pct=100.0, rows=len(rows), elapsed_sec=complete["elapsed_sec"])

        print(
            f"OSR DONE | run_name={run_name} | rows={len(rows)} | csv={csv_path} | elapsed_sec={complete['elapsed_sec']:.1f}",
            flush=True,
        )

    except Exception as e:
        payload = {
            "run_name": run_name,
            "run_dir": str(run_dir),
            "checkpoint": args.checkpoint,
            "error": repr(e),
            "traceback": traceback.format_exc(),
            "elapsed_sec": time.time() - t0,
        }
        error_path.write_text(json.dumps(payload, indent=2))
        write_progress(phase="error", pct=100.0, error=repr(e))
        print(f"OSR ERROR | run_name={run_name} | error={e!r}", flush=True)
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
