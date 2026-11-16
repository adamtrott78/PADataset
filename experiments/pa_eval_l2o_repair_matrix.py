#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
from pathlib import Path


def load_audit(path: Path) -> dict[str, dict]:
    if not path.is_file():
        raise FileNotFoundError(f"Audit file missing: {path}")
    payload = json.loads(path.read_text())
    return {
        rec.get("run_name"): rec
        for rec in payload.get("records", [])
        if rec.get("run_name")
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="manifests/l2o_surrogate_matrix_repair_v1.tsv")
    ap.add_argument("--results-root", default="results_pa_ota_l2o_repair")
    ap.add_argument("--audit", default="local_artifacts/l2o_repair_audit.json")
    ap.add_argument("--out-root", default="results_pa_osr_eval/l2o_repair_budget005")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--num-workers", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    manifest_rows = list(csv.DictReader(Path(args.manifest).open(), delimiter="\t"))
    audit = load_audit(Path(args.audit))
    results_root = Path(args.results_root)
    out_root = Path(args.out_root)

    commands = []
    for row in manifest_rows:
        run_name = row["run_name"]
        status = audit.get(run_name, {}).get("status")
        if status != "PASS":
            print(f"SKIP | run={run_name} | audit_status={status}")
            continue

        run_dir = results_root / run_name
        cfg_path = run_dir / "config.json"
        ckpt = run_dir / "best_model.pt"
        complete = run_dir / "train_complete.json"
        if not cfg_path.is_file() or not ckpt.is_file() or not complete.is_file():
            raise RuntimeError(f"PASS run lacks required artifacts: {run_dir}")

        cfg = json.loads(cfg_path.read_text())
        target = row["target_pa"]
        surrogate = row["surrogate_pa"]
        known = [x for x in row["known_pas"].split(",") if x]

        if cfg.get("unknown_pas") != [target]:
            raise RuntimeError(f"Target mismatch for {run_name}")
        if surrogate in (cfg.get("pas") or []):
            raise RuntimeError(f"Surrogate leaked into backbone taxonomy for {run_name}")
        if set(cfg.get("pas") or []) != set(known + [target]):
            raise RuntimeError(f"Known/target taxonomy mismatch for {run_name}")
        if cfg.get("early_stopping_mode") != "known_only":
            raise RuntimeError(f"Non-known-only checkpoint selection for {run_name}")
        if cfg.get("quarantine_target_until_test") is not True:
            raise RuntimeError(f"Target quarantine missing for {run_name}")
        if float(cfg.get("open_val_frac", -1)) != 0.0:
            raise RuntimeError(f"Target-open validation enabled for {run_name}")

        out_dir = out_root / f"{run_name}__sur{surrogate}__budget005"
        if out_dir.exists():
            raise RuntimeError(f"Refusing to overwrite existing output: {out_dir}")

        cmd = [
            sys.executable,
            "experiments/pa_eval_dqn_guard_surrogate_open.py",
            "--run-dir", str(run_dir),
            "--checkpoint", "best_model",
            "--out-dir", str(out_dir),
            "--surrogate-open-pa", surrogate,
            "--mode", "var_energy",
            "--decision-mode", "score_threshold",
            "--max-known-reject-cal", "0.05",
            "--known-cap", "625",
            "--open-cap", "625",
            "--device", args.device,
            "--batch-size", str(args.batch_size),
            "--num-workers", str(args.num_workers),
        ]
        commands.append((run_name, target, surrogate, cmd))

    print(f"ELIGIBLE_CELLS={len(commands)}")
    for run_name, target, surrogate, cmd in commands:
        print(
            "COMMAND | "
            f"run={run_name} | target={target} | surrogate={surrogate} | "
            + " ".join(cmd)
        )
        if args.dry_run:
            continue
        env = os.environ.copy()
        subprocess.run(cmd, check=True, env=env)

        out_dir = Path(cmd[cmd.index("--out-dir") + 1])
        summary = out_dir / "osr_summary.csv"
        if not summary.is_file() or summary.stat().st_size == 0:
            raise RuntimeError(f"DQNGuard evaluation produced no summary: {out_dir}")
        print(f"EVAL_DONE | run={run_name} | summary={summary}")


if __name__ == "__main__":
    main()
