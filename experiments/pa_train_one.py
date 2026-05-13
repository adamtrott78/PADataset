#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from experiments.pa_constants import DATA_ROOT
from discriminate import run_experiment


REQUIRED_ARTIFACTS = [
    "config.json",
    "best_model.pt",
    "final_model.pt",
    "history.json",
    "summary.json",
]


def expected_run_dir(cfg: dict) -> Path | None:
    if cfg.get("use_timestamped_run_dir", True):
        return None
    run_name = cfg.get("run_name")
    save_root = cfg.get("save_root", "results_pa_baseline")
    if not run_name:
        return None
    return Path(save_root) / run_name


def is_complete(run_dir: Path) -> bool:
    return run_dir.is_dir() and all((run_dir / name).is_file() for name in REQUIRED_ARTIFACTS)


def verify_complete(run_dir: Path) -> None:
    missing = [name for name in REQUIRED_ARTIFACTS if not (run_dir / name).is_file()]
    if missing:
        raise RuntimeError(f"Run directory is incomplete: {run_dir}; missing={missing}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cfg", required=True)
    ap.add_argument("--data-root", default=str(DATA_ROOT))
    ap.add_argument("--no-skip-existing", action="store_true")
    args = ap.parse_args()

    cfg_path = Path(args.cfg).expanduser()
    cfg = json.loads(cfg_path.read_text())

    run_name = cfg["run_name"]
    seed = cfg.get("seed")
    gpu = os.environ.get("CUDA_VISIBLE_DEVICES", "unset")
    expected = expected_run_dir(cfg)

    print(
        f"TRAIN START | run_name={run_name} | seed={seed} | gpu={gpu} | cfg={cfg_path}",
        flush=True,
    )

    if expected is not None and is_complete(expected) and not args.no_skip_existing:
        print(
            f"TRAIN DONE | run_name={run_name} | gpu={gpu} | save_dir={expected} | skipped=true",
            flush=True,
        )
        return

    t0 = time.time()

    try:
        summary = run_experiment(cfg, data_root=args.data_root)
        save_dir = Path(summary["save_dir"])
        verify_complete(save_dir)

        complete_record = {
            "run_name": run_name,
            "save_dir": str(save_dir),
            "cfg_path": str(cfg_path),
            "elapsed_sec": time.time() - t0,
            "summary_path": str(save_dir / "summary.json"),
        }
        (save_dir / "train_complete.json").write_text(json.dumps(complete_record, indent=2))

        best_epoch = summary.get("best_epoch")
        print(
            f"TRAIN DONE | run_name={run_name} | gpu={gpu} | save_dir={save_dir} | best_epoch={best_epoch} | elapsed_sec={complete_record['elapsed_sec']:.1f}",
            flush=True,
        )

    except Exception as e:
        print(
            f"TRAIN ERROR | run_name={run_name} | gpu={gpu} | error={repr(e)}",
            flush=True,
        )
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
