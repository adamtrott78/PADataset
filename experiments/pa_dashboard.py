#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import time
from pathlib import Path


ARTIFACTS = [
    ("C", "config.json"),
    ("B", "best_model.pt"),
    ("F", "final_model.pt"),
    ("H", "history.json"),
    ("S", "summary.json"),
    ("T", "train_complete.json"),
    ("E", "train_error.json"),
]


def load_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def fmt_time(sec):
    if sec is None:
        return "?"
    try:
        sec = max(0, int(float(sec)))
    except Exception:
        return "?"
    if sec >= 3600:
        return f"{sec // 3600:d}:{(sec % 3600) // 60:02d}:{sec % 60:02d}"
    return f"{sec // 60:02d}:{sec % 60:02d}"


def fmt_float(x, nd=4):
    if x is None:
        return "?"
    try:
        return f"{float(x):.{nd}f}"
    except Exception:
        return "?"


def clear():
    print("\033[2J\033[H", end="")


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
            parts.append(f"GPU{idx} mem {used}/{total} MiB util {util}%")
        return "  ".join(parts)
    except Exception:
        return "GPU status unavailable"


def active_process_text():
    try:
        out = subprocess.check_output(["pgrep", "-af", "pa_train_one.py"], text=True)
        return out.strip()
    except Exception:
        return ""


def read_manifest(path: Path):
    with path.open(newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return list(reader)


def resolve_run(row, repo: Path):
    cfg_path = repo / row["cfg_path"]
    cfg = load_json(cfg_path) or {}

    run_name = cfg.get("run_name") or row.get("run_name")
    save_root = cfg.get("save_root") or row.get("save_root") or "results_pa_final"
    run_dir = repo / save_root / run_name

    paper_set = cfg.get("paper_set") or row.get("paper_set", "?")
    family = cfg.get("family_tag") or row.get("family_tag", "?")
    seed = cfg.get("seed", row.get("seed", "?"))
    gpu = row.get("gpu", "?")
    unknown = row.get("unknown_pa", "?")

    return {
        "cfg": cfg,
        "cfg_path": cfg_path,
        "run_name": run_name,
        "save_root": save_root,
        "run_dir": run_dir,
        "paper_set": paper_set,
        "family": family,
        "seed": seed,
        "gpu": gpu,
        "unknown": unknown,
    }



def stale_reason_for(run):
    """Return reason if existing run_dir artifacts do not match manifest cfg."""
    run_dir = run["run_dir"]
    cfg = run.get("cfg") or {}
    existing_cfg = load_json(run_dir / "config.json")

    if not existing_cfg:
        return None

    checks = [
        ("epochs", cfg.get("epochs"), existing_cfg.get("epochs")),
        ("run_name", cfg.get("run_name"), existing_cfg.get("run_name")),
        ("family_tag", cfg.get("family_tag"), existing_cfg.get("family_tag")),
        ("paper_set", cfg.get("paper_set"), existing_cfg.get("paper_set")),
        ("unknown_pas", cfg.get("unknown_pas"), existing_cfg.get("unknown_pas")),
        ("pas", cfg.get("pas"), existing_cfg.get("pas")),
        ("cache_len", cfg.get("cache_len"), existing_cfg.get("cache_len")),
        ("source_type", cfg.get("source_type"), existing_cfg.get("source_type")),
        ("source_name", cfg.get("source_name"), existing_cfg.get("source_name")),
        ("dataset_tag", cfg.get("dataset_tag"), existing_cfg.get("dataset_tag")),
        ("noise_tag", cfg.get("noise_tag"), existing_cfg.get("noise_tag")),
    ]

    bad = []
    for key, expected, actual in checks:
        if expected != actual:
            bad.append(f"{key}:manifest={expected!r},run={actual!r}")

    if bad:
        return "; ".join(bad[:3])

    return None


def artifact_flags(run_dir: Path):
    out = []
    for flag, name in ARTIFACTS:
        out.append(flag if (run_dir / name).exists() else "-")
    return "".join(out)


def status_for(run, active_text: str):
    run_dir = run["run_dir"]
    cfg_path = str(run["cfg_path"])

    if stale_reason_for(run):
        return "STALE"
    if (run_dir / "train_error.json").exists():
        return "ERROR"
    if (run_dir / "train_complete.json").exists():
        return "DONE"
    if cfg_path in active_text or run["run_name"] in active_text:
        if (
            (run_dir / "final_model.pt").exists()
            and (run_dir / "history.json").exists()
            and not (run_dir / "summary.json").exists()
        ):
            return "FINALIZING"
        return "RUNNING"
    if (
        (run_dir / "final_model.pt").exists()
        and (run_dir / "history.json").exists()
        and not (run_dir / "summary.json").exists()
    ):
        return "INCOMPLETE"
    if (run_dir / "summary.json").exists() and not (run_dir / "train_complete.json").exists():
        return "WRAPPING"
    if (run_dir / "train_progress.json").exists():
        return "STARTED"
    return "PENDING"


def tqdm_line(progress, summary):
    if progress is None:
        if summary is not None:
            return "Epoch done: 100%|██████████| ?/? [?<00:00, ?it/s]"
        return "Epoch ?/?:   0%|          | 0/? [00:00<?, ?it/s]"

    phase = progress.get("phase", "?")
    epoch = int(progress.get("epoch", 0) or 0)
    epochs = int(progress.get("epochs", 0) or 0)
    step = int(progress.get("step", 0) or 0)
    steps = int(progress.get("steps", 0) or 0)
    pct = float(progress.get("pct", 0.0) or 0.0)
    sps = float(progress.get("steps_per_sec", 0.0) or 0.0)

    bar_width = 10
    filled = max(0, min(bar_width, int(bar_width * pct / 100.0)))
    bar = "█" * filled + " " * (bar_width - filled)

    elapsed = None
    eta = None
    if sps > 0 and step > 0:
        elapsed = step / sps
        eta = max(0, steps - step) / sps

    if phase == "validation":
        return f"Epoch {epoch}/{epochs}: 100%|{'█' * bar_width}| {steps}/{steps} [{fmt_time(elapsed)}<?, ?it/s] validating"

    if phase == "epoch_done" or (summary is not None and steps > 0 and step >= steps):
        speed = f"{sps:.2f}it/s" if sps > 0 else "?it/s"
        return f"Epoch {epoch}/{epochs}: 100%|{'█' * bar_width}| {steps}/{steps} [{fmt_time(elapsed)}<00:00, {speed}]"

    return f"Epoch {epoch}/{epochs}: {pct:3.0f}%|{bar}| {step}/{steps} [{fmt_time(elapsed)}<{fmt_time(eta)}, {sps:.2f}it/s]"


def metric_line(progress, summary, complete):
    parts = []

    if progress:
        loss = progress.get("loss_so_far", progress.get("train_loss"))
        if loss is not None:
            parts.append(f"loss {fmt_float(loss)}")
        else:
            parts.append(f"phase {progress.get('phase', '?')}")
    else:
        parts.append("progress pending")

    if summary:
        parts.append(f"best_ep {summary.get('best_epoch', '?')}")
        parts.append(f"val_acc {fmt_float(summary.get('best_val_acc'))}")
        parts.append(f"val_f1 {fmt_float(summary.get('best_val_macro_f1'))}")
        if "test_known_acc" in summary:
            parts.append(f"test_acc {fmt_float(summary.get('test_known_acc'))}")
        if "test_known_macro_f1" in summary:
            parts.append(f"test_f1 {fmt_float(summary.get('test_known_macro_f1'))}")
        if "test_dqn_proxy_expanded5" in summary:
            parts.append(f"proxy5 {fmt_float(summary.get('test_dqn_proxy_expanded5'))}")
    else:
        parts.append("val pending")

    if complete:
        parts.append(f"elapsed {fmt_time(complete.get('elapsed_sec'))}")

    if complete and summary:
        parts.append("eval pending")
    else:
        parts.append("eval not-ready")

    return " | ".join(parts)


def compact_run_line(i, total, run, status, progress, summary, complete, arts):
    epoch = "?"
    epochs = "?"
    ep_pct = 0.0
    run_pct = 0.0
    step = "?"
    steps = "?"
    loss = "?"

    if progress:
        epoch_i = int(progress.get("epoch", 0) or 0)
        epochs_i = int(progress.get("epochs", 0) or 0)
        step_i = int(progress.get("step", 0) or 0)
        steps_i = int(progress.get("steps", 0) or 0)

        epoch = epoch_i if epoch_i > 0 else "?"
        epochs = epochs_i if epochs_i > 0 else "?"
        step = step_i
        steps = steps_i
        ep_pct = float(progress.get("pct", 0.0) or 0.0)

        if epoch_i > 0 and epochs_i > 0 and steps_i > 0:
            run_pct = 100.0 * ((epoch_i - 1) + (step_i / max(steps_i, 1))) / epochs_i
        elif summary is not None or complete is not None:
            run_pct = 100.0

        loss = fmt_float(progress.get("loss_so_far", progress.get("train_loss")), 4)

    elif summary is not None or complete is not None:
        ep_pct = 100.0
        run_pct = 100.0

    val = "?"
    proxy = "?"
    test = "?"
    if summary:
        val = fmt_float(summary.get("best_val_macro_f1"), 3)
        proxy = fmt_float(summary.get("test_dqn_proxy_expanded5"), 3)
        test = fmt_float(summary.get("test_known_macro_f1"), 3)

    elapsed = "?"
    if complete:
        elapsed = fmt_time(complete.get("elapsed_sec"))

    rn = run["run_name"]
    if len(rn) > 34:
        rn = rn[:31] + "..."

    ep_txt = f"{epoch}/{epochs}"
    step_txt = f"{step}/{steps}"

    return (
        f"{i:02d}/{total:02d} "
        f"{status[:4]:<4} "
        f"{('g' + str(run['gpu'])):<3} "
        f"{str(run['paper_set']):<8.8} "
        f"{str(run['family']):<22.22} "
        f"{str(run['unknown']):<4.4} "
        f"{ep_txt:<7.7} "
        f"{run_pct:6.1f} "
        f"{ep_pct:6.1f} "
        f"{step_txt:>11.11} "
        f"{loss:>7.7} "
        f"{val:>5.5} "
        f"{test:>6.6} "
        f"{proxy:>6.6} "
        f"{arts:<7.7} "
        f"{elapsed:>7.7} "
        f"{rn}"
    )

def render_once(repo: Path, manifest: Path, view: str = "full", active_only: bool = False, max_rows: int | None = None):
    rows = read_manifest(manifest)
    active_text = active_process_text()

    total = len(rows)
    done = running = errors = pending = stale = 0

    print(f"PADataset train/eval dashboard | {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"MANIFEST={manifest}")
    print()
    print(gpu_line())
    print()

    rendered = []

    for i, row in enumerate(rows, 1):
        run = resolve_run(row, repo)
        run_dir = run["run_dir"]
        progress = load_json(run_dir / "train_progress.json")
        summary = load_json(run_dir / "summary.json")
        complete = load_json(run_dir / "train_complete.json")

        st = status_for(run, active_text)
        arts = artifact_flags(run_dir)

        if st == "DONE":
            done += 1
        elif st in {"RUNNING", "STARTED", "FINALIZING", "WRAPPING"}:
            running += 1
        elif st == "ERROR":
            errors += 1
        elif st == "STALE":
            stale += 1
        else:
            pending += 1

        if active_only and st not in {"RUNNING", "STARTED", "FINALIZING", "WRAPPING", "ERROR", "INCOMPLETE"}:
            continue

        rendered.append((i, run, run_dir, progress, summary, complete, st, arts))

    if view == "compact":
        print(
            f"{'idx':<5} "
            f"{'stat':<4} "
            f"{'gpu':<3} "
            f"{'paper':<8} "
            f"{'family':<22} "
            f"{'unk':<4} "
            f"{'epoch':<7} "
            f"{'run%':>6} "
            f"{'ep%':>6} "
            f"{'step/steps':>11} "
            f"{'loss':>7} "
            f"{'val':>5} "
            f"{'test':>6} "
            f"{'p5':>6} "
            f"{'arts':<7} "
            f"{'elapsed':>7} "
            f"run"
        )
        print("-" * 150)
        rows_to_show = rendered if max_rows is None else rendered[:max_rows]
        for i, run, run_dir, progress, summary, complete, st, arts in rows_to_show:
            print(compact_run_line(i, total, run, st, progress, summary, complete, arts))
        if max_rows is not None and len(rendered) > max_rows:
            print(f"... hidden {len(rendered) - max_rows} rows due to --max-rows={max_rows}")
    else:
        rows_to_show = rendered if max_rows is None else rendered[:max_rows]
        for i, run, run_dir, progress, summary, complete, st, arts in rows_to_show:
            print("=" * 80)
            print(
                f"RUN {i}/{total} | {st} | gpu={run['gpu']} seed={run['seed']} "
                f"| {run['paper_set']} unk={run['unknown']} | arts={arts}"
            )
            print(run["run_name"])
            print(tqdm_line(progress, summary))
            stale_reason = stale_reason_for(run)
            err = load_json(run_dir / "train_error.json")
            if stale_reason:
                msg = stale_reason.replace("\n", " ")
                if len(msg) > 180:
                    msg = msg[:177] + "..."
                print(f"stale {msg}")
            elif err:
                msg = str(err.get("error", "?")).replace("\n", " ")
                if len(msg) > 180:
                    msg = msg[:177] + "..."
                print(f"error {msg}")
            else:
                print(metric_line(progress, summary, complete))
            print()
        if max_rows is not None and len(rendered) > max_rows:
            print(f"... hidden {len(rendered) - max_rows} rows due to --max-rows={max_rows}")

    print("=" * 80)
    print(f"summary: total={total} done={done} running={running} errors={errors} stale={stale} pending={pending}")
    print("artifact flags: C=config B=best F=final H=history S=summary T=train_complete E=train_error")

    if total and done == total:
        print()
        print("FINAL STATE: TRAINING COMPLETE")
    elif errors:
        print()
        print("FINAL STATE: ERRORS PRESENT")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", nargs="?", default="manifests/smoke_train_manifest.tsv")
    ap.add_argument("--repo", default=os.environ.get("REPO", str(Path.cwd())))
    ap.add_argument("--refresh", type=float, default=float(os.environ.get("REFRESH", 2)))
    ap.add_argument("--view", choices=["full", "compact"], default=os.environ.get("VIEW", "full"))
    ap.add_argument("--active-only", action="store_true", default=os.environ.get("ACTIVE_ONLY", "0") == "1")
    ap.add_argument("--max-rows", type=int, default=None)
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo).expanduser().resolve()
    manifest = (repo / args.manifest).resolve() if not Path(args.manifest).is_absolute() else Path(args.manifest)

    while True:
        clear()
        render_once(repo, manifest, view=args.view, active_only=args.active_only, max_rows=args.max_rows)
        print(f"Refresh: {args.refresh:g}s | Ctrl+C exits dashboard only")
        if args.once:
            break
        time.sleep(args.refresh)


if __name__ == "__main__":
    main()
