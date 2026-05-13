#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import time
from pathlib import Path


def load_json(path: Path):
    try:
        if path.is_file():
            return json.loads(path.read_text())
    except Exception:
        return None
    return None


def read_manifest(path: Path):
    rows = []
    with path.open(newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            rows.append(row)
    return rows


def gpu_line():
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=index,memory.used,memory.total,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        parts = []
        for line in out.strip().splitlines():
            idx, used, total, util = [x.strip() for x in line.split(",")]
            parts.append(f"GPU{idx} mem {int(used):5d}/{int(total):5d} MiB util {int(util):3d}%")
        return "  ".join(parts)
    except Exception:
        return "GPU status unavailable"


def short(s, n=140):
    s = str(s)
    return s if len(s) <= n else s[: n - 3] + "..."


def status_for(out_dir: Path):
    err = load_json(out_dir / "osr_error.json")
    comp = load_json(out_dir / "osr_complete.json")
    prog = load_json(out_dir / "osr_progress.json")
    summary = out_dir / "osr_summary.csv"

    if err:
        return "ERROR", prog, comp, err
    if comp or summary.is_file():
        return "DONE", prog, comp, err
    if prog:
        phase = str(prog.get("phase", "")).lower()
        if phase == "error":
            return "ERROR", prog, comp, err
        if phase == "done":
            return "DONE", prog, comp, err
        return "RUNNING", prog, comp, err
    return "PENDING", prog, comp, err


def artifact_flags(out_dir: Path):
    flags = [
        ("P", "osr_progress.json"),
        ("S", "osr_summary.csv"),
        ("C", "osr_complete.json"),
        ("E", "osr_error.json"),
    ]
    return "".join(k if (out_dir / f).exists() else "-" for k, f in flags)


def render_bar(pct, width=30):
    try:
        pct = float(pct)
    except Exception:
        pct = 0.0
    pct = max(0.0, min(100.0, pct))
    filled = int(round(width * pct / 100.0))
    return "█" * filled + "-" * (width - filled)


def render_once(manifest: Path):
    rows = read_manifest(manifest)
    now = time.strftime("%Y-%m-%d %H:%M:%S")

    print(f"PADataset OSR/DQN dashboard | {now}")
    print(f"MANIFEST={manifest.resolve()}")
    print()
    print(gpu_line())
    print()

    counts = {"DONE": 0, "RUNNING": 0, "ERROR": 0, "PENDING": 0}

    for i, row in enumerate(rows, 1):
        run_name = row.get("run_name", "?")
        out_dir = Path(row.get("out_dir", ""))
        gpu = row.get("gpu", "?")
        checkpoint = row.get("checkpoint", "?")
        modes = row.get("modes", "?")
        grid = row.get("sweep_grid", "?")

        status, prog, comp, err = status_for(out_dir)
        counts[status] = counts.get(status, 0) + 1
        arts = artifact_flags(out_dir)

        phase = "waiting"
        pct = 0.0
        rows_done = "?"
        elapsed = "?"

        if prog:
            phase = prog.get("phase", phase)
            pct = prog.get("pct", pct)
            if "rows" in prog:
                rows_done = prog.get("rows")
            if "elapsed_sec" in prog:
                sec = float(prog.get("elapsed_sec", 0.0))
                elapsed = f"{int(sec//60):02d}:{int(sec%60):02d}"

        if comp:
            rows_done = comp.get("rows", rows_done)
            sec = float(comp.get("elapsed_sec", 0.0))
            elapsed = f"{int(sec//60):02d}:{int(sec%60):02d}"

        print("=" * 88)
        print(f"RUN {i}/{len(rows)} | {status} | gpu={gpu} | ckpt={checkpoint} | grid={grid} | arts={arts}")
        print(run_name)
        print(f"modes: {modes}")
        extra = ""
        if prog:
            sc = prog.get("sweep_candidate")
            st = prog.get("sweep_candidates")
            spec = prog.get("spec_name")
            if sc is not None and st is not None:
                extra += f" | sweep {sc}/{st}"
            if spec:
                extra += f" | spec {spec}"

            de = prog.get("dqn_episode")
            des = prog.get("dqn_episodes")
            if de is not None and des is not None:
                extra += f" | dqn_ep {de}/{des}"

            rew = prog.get("dqn_avg_reward")
            eps = prog.get("dqn_epsilon")
            if rew is not None:
                try:
                    extra += f" | reward {float(rew):.4f}"
                except Exception:
                    extra += f" | reward {rew}"
            if eps is not None:
                try:
                    extra += f" | eps {float(eps):.4f}"
                except Exception:
                    extra += f" | eps {eps}"

        print(f"[{render_bar(pct)}] {float(pct):6.2f}% | phase {phase} | rows {rows_done} | elapsed {elapsed}{extra}")

        if err:
            print(f"error: {short(err.get('error', '?'), 180)}")
        elif comp:
            print(f"csv: {comp.get('csv_path', out_dir / 'osr_summary.csv')}")
        elif prog and prog.get("error"):
            print(f"error: {short(prog.get('error'), 180)}")
        else:
            print(f"out: {out_dir}")

        if (out_dir / "osr_summary.csv").is_file():
            try:
                lines = (out_dir / "osr_summary.csv").read_text().splitlines()
                if len(lines) >= 2:
                    print(f"osr_summary rows: {len(lines) - 1}")
            except Exception:
                pass

        print()

    total = len(rows)
    print("=" * 88)
    print(
        f"summary: total={total} done={counts.get('DONE',0)} running={counts.get('RUNNING',0)} "
        f"errors={counts.get('ERROR',0)} pending={counts.get('PENDING',0)}"
    )
    print("artifact flags: P=osr_progress S=osr_summary C=osr_complete E=osr_error")
    if counts.get("ERROR", 0):
        print()
        print("FINAL STATE: ERRORS PRESENT")
    elif total and counts.get("DONE", 0) == total:
        print()
        print("FINAL STATE: ALL OSR EVALS COMPLETE")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--refresh", type=float, default=None)
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()

    manifest = Path(args.manifest)

    if args.once or args.refresh is None:
        render_once(manifest)
        return

    while True:
        print("\033[2J\033[H", end="")
        render_once(manifest)
        print(f"Refresh: {args.refresh:g}s | Ctrl+C exits dashboard only")
        time.sleep(args.refresh)


if __name__ == "__main__":
    main()
