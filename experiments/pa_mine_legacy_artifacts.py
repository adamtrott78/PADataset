#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import traceback
from pathlib import Path
from typing import Any


DEFAULT_RESULT_ROOTS = [
    "results_pa_baseline",
    "results_pa_cache_sweep",
    "results_pa_confmanifold_coarse",
    "results_pa_confmanifold_refined",
    "results_pa_finalist",
    "results_pa_followup",
    "results_pa_osr_bank",
    "results_pa_ota_btzb",
    "results_pa_smoke",
]

DEFAULT_TABLE_ROOTS = [
    "local_artifacts/generated_tables",
    ".",
]


SUMMARY_KEYS = [
    "run_name",
    "task",
    "split_mode",
    "paper_set",
    "family_tag",
    "unknown_pas",
    "known_pa_names",
    "unknown_pa_names",
    "pas",
    "protocols",
    "source_type",
    "source_name",
    "dataset_tag",
    "noise_tag",
    "cache_root",
    "cache_len",
    "batch_size",
    "epochs",
    "seed",
    "lr",
    "weight_decay",
    "lambda_center",
    "label_smoothing",
    "entropy_loss_weight",
    "mlp_dropout",
    "class_weight_mode",
    "grad_clip_norm",
    "scheduler_name",
    "early_stopping_mode",
    "open_conf_selection_metric",
    "best_epoch",
    "best_val_metric",
    "best_val_acc",
    "best_val_macro_f1",
    "best_val_dqn_proxy_softmax3",
    "best_val_dqn_proxy_expanded5",
    "test_known_acc",
    "test_known_macro_f1",
    "test_dqn_proxy_softmax3",
    "test_dqn_proxy_expanded5",
    "test_pmax_auroc",
    "test_p1p2_auroc",
    "test_entropy_auroc",
    "test_energy_auroc",
    "test_logit_variance_auroc",
    "test_softmax3_mean_auroc",
    "test_expanded5_mean_auroc",
    "available_checkpoints",
]

CONFIG_KEYS = [
    "run_name",
    "task",
    "split_mode",
    "paper_set",
    "family_tag",
    "unknown_pas",
    "pas",
    "protocols",
    "source_type",
    "source_name",
    "dataset_tag",
    "noise_tag",
    "cache_root",
    "cache_len",
    "batch_size",
    "epochs",
    "seed",
    "lr",
    "weight_decay",
    "lambda_center",
    "label_smoothing",
    "entropy_loss_weight",
    "mlp_dropout",
    "class_weight_mode",
    "grad_clip_norm",
    "scheduler_name",
    "early_stopping_mode",
    "open_conf_selection_metric",
    "model_selection_metric",
]


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except Exception as e:
        return {"_json_error": repr(e)}


def compact(x: Any) -> Any:
    if x is None:
        return None
    if isinstance(x, (str, int, float, bool)):
        return x
    try:
        return json.dumps(x, sort_keys=True)
    except Exception:
        return repr(x)


def first_nonempty(*vals):
    for v in vals:
        if v is not None and v != "":
            return v
    return None


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return

    fields = sorted({k for row in rows for k in row.keys()})
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow(row)


def safe_stat(path: Path) -> dict[str, Any]:
    try:
        st = path.stat()
        return {
            "size_bytes": st.st_size,
            "mtime": st.st_mtime,
        }
    except Exception:
        return {
            "size_bytes": None,
            "mtime": None,
        }


def mine_run_dirs(result_roots: list[str]) -> list[dict[str, Any]]:
    rows = []

    for root_name in result_roots:
        root = Path(root_name)
        if not root.is_dir():
            continue

        run_dirs = sorted(
            {p.parent for p in root.rglob("config.json")}
            | {p.parent for p in root.rglob("summary.json")}
            | {p.parent for p in root.rglob("history.json")}
            | {p.parent for p in root.rglob("*.pt")}
        )

        for run_dir in run_dirs:
            config_path = run_dir / "config.json"
            summary_path = run_dir / "summary.json"
            history_path = run_dir / "history.json"

            cfg = load_json(config_path) if config_path.exists() else {}
            summ = load_json(summary_path) if summary_path.exists() else {}
            hist = load_json(history_path) if history_path.exists() else {}

            row: dict[str, Any] = {
                "result_root": root_name,
                "run_dir": str(run_dir),
                "has_config": config_path.exists(),
                "has_summary": summary_path.exists(),
                "has_history": history_path.exists(),
                "n_checkpoints": len(list(run_dir.glob("*.pt"))),
                "checkpoint_tags": compact(sorted(p.stem for p in run_dir.glob("*.pt"))),
                "config_path": str(config_path) if config_path.exists() else "",
                "summary_path": str(summary_path) if summary_path.exists() else "",
                "history_path": str(history_path) if history_path.exists() else "",
            }

            row["run_name"] = first_nonempty(
                summ.get("run_name"),
                cfg.get("run_name"),
                run_dir.name,
            )

            for k in sorted(set(SUMMARY_KEYS + CONFIG_KEYS)):
                row[k] = compact(first_nonempty(summ.get(k), cfg.get(k)))

            if isinstance(hist, dict):
                for metric in [
                    "train_loss",
                    "val_loss",
                    "val_acc",
                    "val_macro_f1",
                    "val_dqn_proxy_softmax3",
                    "val_dqn_proxy_expanded5",
                    "lr",
                ]:
                    v = hist.get(metric)
                    if isinstance(v, list) and v:
                        row[f"history_{metric}_len"] = len(v)
                        row[f"history_{metric}_last"] = compact(v[-1])
                        try:
                            row[f"history_{metric}_best"] = max(x for x in v if x is not None)
                        except Exception:
                            row[f"history_{metric}_best"] = None

            rows.append(row)

    return rows


def torch_load_checkpoint(path: Path):
    import torch
    return torch.load(path, map_location="cpu", weights_only=False)


def mine_checkpoints(result_roots: list[str], max_checkpoints: int | None = None) -> list[dict[str, Any]]:
    rows = []
    pt_files: list[Path] = []

    for root_name in result_roots:
        root = Path(root_name)
        if root.is_dir():
            pt_files.extend(sorted(root.rglob("*.pt")))

    if max_checkpoints is not None:
        pt_files = pt_files[:max_checkpoints]

    for i, path in enumerate(pt_files, 1):
        row: dict[str, Any] = {
            "checkpoint_path": str(path),
            "result_root": path.parts[0] if path.parts else "",
            "run_dir": str(path.parent),
            "checkpoint_tag": path.stem,
        }
        row.update(safe_stat(path))

        try:
            ckpt = torch_load_checkpoint(path)
            row["load_ok"] = True
            row["checkpoint_type"] = type(ckpt).__name__

            if isinstance(ckpt, dict):
                row["keys"] = compact(sorted(ckpt.keys()))
                for k in [
                    "num_classes",
                    "input_len",
                    "epoch",
                    "best_epoch",
                    "best_val_metric",
                    "best_val_acc",
                    "best_val_macro_f1",
                    "class_names",
                ]:
                    row[k] = compact(ckpt.get(k))

                cfg = ckpt.get("config")
                if isinstance(cfg, dict):
                    row["has_embedded_config"] = True
                    for k in CONFIG_KEYS:
                        row[f"config_{k}"] = compact(cfg.get(k))
                else:
                    row["has_embedded_config"] = False

                val_stats = ckpt.get("val_stats")
                if isinstance(val_stats, dict):
                    for k, v in val_stats.items():
                        if isinstance(v, (str, int, float, bool)) or v is None:
                            row[f"val_{k}"] = compact(v)

                open_conf = ckpt.get("open_conf_stats")
                if isinstance(open_conf, dict):
                    for k, v in open_conf.items():
                        if isinstance(v, (str, int, float, bool)) or v is None:
                            row[f"open_conf_{k}"] = compact(v)

                msd = ckpt.get("model_state_dict")
                if isinstance(msd, dict):
                    row["model_state_n_tensors"] = len(msd)
                    # Capture tensor shapes only, not tensor values.
                    shapes = {}
                    for j, (name, tensor) in enumerate(msd.items()):
                        if j >= 20:
                            break
                        try:
                            shapes[name] = list(tensor.shape)
                        except Exception:
                            shapes[name] = "?"
                    row["model_state_shape_sample"] = compact(shapes)
            else:
                row["keys"] = ""

        except Exception as e:
            row["load_ok"] = False
            row["error"] = repr(e)
            row["traceback_tail"] = traceback.format_exc(limit=2)

        rows.append(row)

        if i % 25 == 0 or i == len(pt_files):
            print(f"checkpoint inventory {i}/{len(pt_files)}", flush=True)

    return rows


def mine_tables(table_roots: list[str]) -> list[dict[str, Any]]:
    rows = []
    seen = set()

    for root_name in table_roots:
        root = Path(root_name)
        if not root.exists():
            continue

        for path in sorted(root.rglob("*.csv")):
            if ".ipynb_checkpoints" in path.parts:
                continue

            low = path.name.lower()
            if not any(x in low for x in ["leaderboard", "eval", "varmax", "osr"]):
                continue

            resolved = str(path.resolve())
            if resolved in seen:
                continue
            seen.add(resolved)

            row = {
                "path": str(path),
                "name": path.name,
            }
            row.update(safe_stat(path))

            try:
                with path.open(newline="") as f:
                    reader = csv.reader(f)
                    header = next(reader, [])
                    n = sum(1 for _ in reader)
                row["rows"] = n
                row["columns"] = compact(header)
            except Exception as e:
                row["rows"] = None
                row["columns"] = ""
                row["error"] = repr(e)

            rows.append(row)

    return rows


def write_markdown_summary(path: Path, run_rows, ckpt_rows, table_rows):
    from collections import Counter

    root_counts = Counter(r.get("result_root") for r in run_rows)
    family_counts = Counter(r.get("family_tag") for r in run_rows if r.get("family_tag"))
    source_counts = Counter(
        (
            r.get("source_type"),
            r.get("source_name"),
            r.get("dataset_tag"),
            r.get("noise_tag"),
        )
        for r in run_rows
    )

    lines = []
    lines.append("# Legacy PADataset Experiment Inventory")
    lines.append("")
    lines.append("Generated from local ignored artifacts. This file is safe to commit because it contains metadata only, not checkpoints or raw data.")
    lines.append("")
    lines.append("## Counts")
    lines.append("")
    lines.append(f"- Run directories inventoried: {len(run_rows)}")
    lines.append(f"- Checkpoints inventoried: {len(ckpt_rows)}")
    lines.append(f"- Generated tables inventoried: {len(table_rows)}")
    lines.append("")
    lines.append("## Result roots")
    lines.append("")
    for k, v in sorted(root_counts.items()):
        lines.append(f"- `{k}`: {v}")
    lines.append("")
    lines.append("## Family tags observed")
    lines.append("")
    if family_counts:
        for k, v in sorted(family_counts.items()):
            lines.append(f"- `{k}`: {v}")
    else:
        lines.append("- No explicit `family_tag` values found in old summaries/configs.")
    lines.append("")
    lines.append("## Source profiles observed")
    lines.append("")
    for k, v in sorted(source_counts.items(), key=lambda x: str(x[0])):
        lines.append(f"- `{k}`: {v}")
    lines.append("")
    lines.append("## Next reconstruction task")
    lines.append("")
    lines.append("Use `legacy_run_inventory.csv`, `legacy_checkpoint_inventory.csv`, and old generated leaderboard CSVs to define:")
    lines.append("")
    lines.append("1. original digital-noisy source profile")
    lines.append("2. old backbone family grid")
    lines.append("3. old PA open-set folds")
    lines.append("4. OSR evaluation settings")
    lines.append("5. minimal reruns required for missing or ambiguous artifacts")
    lines.append("")

    path.write_text("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="docs/experiments")
    ap.add_argument("--scan-checkpoints", action="store_true")
    ap.add_argument("--max-checkpoints", type=int, default=None)
    ap.add_argument("--result-root", action="append", default=None)
    ap.add_argument("--table-root", action="append", default=None)
    args = ap.parse_args()

    result_roots = args.result_root or DEFAULT_RESULT_ROOTS
    table_roots = args.table_root or DEFAULT_TABLE_ROOTS
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    print("Mining run dirs...")
    run_rows = mine_run_dirs(result_roots)

    print("Mining generated tables...")
    table_rows = mine_tables(table_roots)

    ckpt_rows = []
    if args.scan_checkpoints:
        print("Mining checkpoint metadata...")
        ckpt_rows = mine_checkpoints(result_roots, max_checkpoints=args.max_checkpoints)
    else:
        print("Skipping checkpoint metadata. Use --scan-checkpoints to include .pt metadata.")

    write_csv(out / "legacy_run_inventory.csv", run_rows)
    write_csv(out / "legacy_generated_table_inventory.csv", table_rows)
    write_csv(out / "legacy_checkpoint_inventory.csv", ckpt_rows)

    summary = {
        "n_run_dirs": len(run_rows),
        "n_run_dirs_with_config": sum(1 for r in run_rows if r.get("has_config")),
        "n_run_dirs_with_summary": sum(1 for r in run_rows if r.get("has_summary")),
        "n_generated_tables": len(table_rows),
        "n_checkpoints": len(ckpt_rows),
        "checkpoint_scan_enabled": bool(args.scan_checkpoints),
        "result_roots": result_roots,
        "table_roots": table_roots,
    }
    (out / "legacy_inventory_summary.json").write_text(json.dumps(summary, indent=2))
    write_markdown_summary(out / "legacy_inventory_summary.md", run_rows, ckpt_rows, table_rows)

    print(json.dumps(summary, indent=2))
    print("Wrote:")
    for name in [
        "legacy_run_inventory.csv",
        "legacy_generated_table_inventory.csv",
        "legacy_checkpoint_inventory.csv",
        "legacy_inventory_summary.json",
        "legacy_inventory_summary.md",
    ]:
        print(" ", out / name)


if __name__ == "__main__":
    main()
