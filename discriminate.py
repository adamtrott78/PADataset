from __future__ import annotations

import copy
import gc
import json
import os
import time
from datetime import datetime
from typing import Any, Dict, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from IPython.display import display
from torch.utils.data import DataLoader, Subset
from tqdm.auto import tqdm

from prepData import DataSetup, build_data_from_setup
from evaluate import evaluate_classifier, evaluate_open_confidence


# -----------------------------
# model + loss
# -----------------------------
class CenterLoss(nn.Module):
    def __init__(self, num_classes: int, feat_dim: int, device: str = "cpu"):
        super().__init__()
        self.centers = nn.Parameter(torch.randn(num_classes, feat_dim, device=device))

    def forward(self, features: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        centers_batch = self.centers.index_select(0, labels)
        return F.mse_loss(features, centers_batch)


class ConvBranch(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv1d(1, 32, kernel_size=5, stride=1, padding=2),
            nn.BatchNorm1d(32),
            nn.LeakyReLU(0.1),

            nn.Conv1d(32, 64, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm1d(64),
            nn.LeakyReLU(0.1),

            nn.Conv1d(64, 128, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm1d(128),
            nn.LeakyReLU(0.1),

            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.conv(x)


class ModulationClassifierReduced(nn.Module):
    def __init__(self, num_classes: int, input_len: int = 8192, mlp_dropout: float = 0.3):
        super().__init__()
        self.input_len = input_len
        self.mlp_dropout = float(mlp_dropout)

        self.branches = nn.ModuleList([ConvBranch() for _ in range(8)])

        self.feature_layer = nn.Sequential(
            nn.Linear(128 * 8, 1024),
            nn.LeakyReLU(0.1),
            nn.Dropout(self.mlp_dropout),

            nn.Linear(1024, 512),
            nn.LeakyReLU(0.1),
            nn.Dropout(self.mlp_dropout),

            nn.Linear(512, 256),
            nn.LeakyReLU(0.1),
            nn.Dropout(self.mlp_dropout),
        )
        self.classifier = nn.Linear(256, num_classes)

    def forward(self, x: torch.Tensor, return_features: bool = False):
        branch_feats = [self.branches[i](x[:, i:i + 1, :]) for i in range(8)]
        fused = torch.cat(branch_feats, dim=1)
        features = self.feature_layer(fused)
        logits = self.classifier(features)

        if return_features:
            return logits, features
        return logits

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        branch_feats = [self.branches[i](x[:, i:i + 1, :]) for i in range(8)]
        return torch.cat(branch_feats, dim=1)


# -----------------------------
# utils
# -----------------------------
def save_training_curves(history: Dict[str, list], save_dir: str) -> None:
    epochs = np.arange(1, len(history["train_loss"]) + 1)

    plt.figure(figsize=(8, 5))
    plt.plot(epochs, history["train_loss"], label="Train Loss")
    plt.plot(epochs, history["val_loss"], label="Val Loss")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.title("Training and Validation Loss")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, "loss_curve.png"), dpi=200)
    plt.close()

    plt.figure(figsize=(8, 5))
    plt.plot(epochs, history["val_acc"], label="Val Accuracy")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")
    plt.title("Validation Accuracy")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, "val_accuracy_curve.png"), dpi=200)
    plt.close()

    if "lr" in history and len(history["lr"]) > 0:
        plt.figure(figsize=(8, 5))
        plt.plot(epochs, history["lr"], label="LR")
        plt.xlabel("Epoch")
        plt.ylabel("Learning Rate")
        plt.title("Learning Rate Schedule")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(save_dir, "lr_curve.png"), dpi=200)
        plt.close()

    if "val_dqn_proxy_softmax3" in history and len(history["val_dqn_proxy_softmax3"]) > 0:
        plt.figure(figsize=(8, 5))
        hist_softmax3 = [np.nan if v is None else v for v in history["val_dqn_proxy_softmax3"]]
        hist_expanded5 = [np.nan if v is None else v for v in history["val_dqn_proxy_expanded5"]]
        plt.plot(epochs, hist_softmax3, label="Val DQN Proxy Softmax3")
        plt.plot(epochs, hist_expanded5, label="Val DQN Proxy Expanded5")
        plt.xlabel("Epoch")
        plt.ylabel("Proxy Score")
        plt.title("Open-Manifold Validation Proxy Scores")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(save_dir, "val_open_proxy_curve.png"), dpi=200)
        plt.close()


def save_experiment_summary(summary: Dict[str, Any], save_dir: str) -> None:
    with open(os.path.join(save_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)


def cleanup_experiment_objects(*objs) -> None:
    for obj in objs:
        try:
            if hasattr(obj, "close"):
                obj.close()
        except Exception:
            pass
    del objs
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


CHECKPOINT_TAGS = [
    "best_model",
    "epoch_20",
    "epoch_50",
    "epoch_100",
    "final_model",
]


def list_available_checkpoints(run_dir: str) -> list[str]:
    out = []
    for tag in CHECKPOINT_TAGS:
        if os.path.isfile(os.path.join(run_dir, f"{tag}.pt")):
            out.append(tag)
    return out


def softmax_entropy_from_logits(logits: torch.Tensor, eps: float = 1e-12) -> torch.Tensor:
    probs = torch.softmax(logits, dim=1).clamp(min=eps, max=1.0)
    return -(probs * probs.log()).sum(dim=1)


def build_class_weight_tensor(train_loader, num_classes: int, device: str = "cpu"):
    counts = np.zeros(num_classes, dtype=np.float64)

    for batch in train_loader:
        y = batch[1] if len(batch) >= 2 else None
        if y is None:
            continue
        y_np = y.detach().cpu().numpy()
        counts += np.bincount(y_np, minlength=num_classes).astype(np.float64)

    counts = np.clip(counts, 1.0, None)
    weights = counts.sum() / (num_classes * counts)
    weights = weights / weights.mean()
    return torch.tensor(weights, dtype=torch.float32, device=device)


def make_scheduler(
    optimizer,
    scheduler_name: str,
    epochs: int,
    scheduler_factor: float = 0.5,
    scheduler_patience: int = 5,
    scheduler_min_lr: float = 1e-7,
):
    scheduler_name = (scheduler_name or "cosine").lower()

    if scheduler_name == "cosine":
        return torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer,
            T_max=epochs,
            eta_min=scheduler_min_lr,
        )

    if scheduler_name == "plateau":
        return torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer,
            mode="min",
            factor=scheduler_factor,
            patience=scheduler_patience,
            min_lr=scheduler_min_lr,
        )

    if scheduler_name == "none":
        return None

    raise ValueError(f"Unsupported scheduler_name: {scheduler_name}")


def _make_subset_loader(
    dataset,
    target_n: int,
    batch_size: int,
    num_workers: int,
    pin_memory: bool,
    seed: int,
):
    n = len(dataset)
    if n == 0:
        raise ValueError("Cannot create subset loader from an empty dataset")

    take = min(target_n, n)
    rng = np.random.default_rng(seed)
    idx = rng.choice(n, size=take, replace=False)
    subset = Subset(dataset, idx.tolist())
    loader = DataLoader(
        subset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory,
    )
    return subset, loader


def ensure_val_open_stream(
    data: Dict[str, Any],
    batch_size: int,
    num_workers: int,
    pin_memory: bool,
    seed: int,
    require_true_val_open: bool = False,
    allow_val_open_fallback: bool = True,
):
    """
    Returns:
        val_open_ds, val_open_loader, val_open_source
    where val_open_source is one of:
        - 'true_val_open'
        - 'fallback_from_test_open'
        - None
    """
    if "val_open_ds" in data and "val_open_loader" in data:
        return data["val_open_ds"], data["val_open_loader"], "true_val_open"

    if require_true_val_open:
        raise RuntimeError(
            "This run requires a true val_open stream, but build_data_from_setup() did not provide one. "
            "Patch prepData.py to emit val_open_ds/val_open_loader for open_pa."
        )

    if not allow_val_open_fallback:
        return None, None, None

    if "test_open_ds" not in data or "val_ds" not in data:
        return None, None, None

    target_n = len(data["val_ds"])
    val_open_ds, val_open_loader = _make_subset_loader(
        dataset=data["test_open_ds"],
        target_n=target_n,
        batch_size=batch_size,
        num_workers=num_workers,
        pin_memory=pin_memory,
        seed=seed,
    )
    return val_open_ds, val_open_loader, "fallback_from_test_open"


def _select_known_only_metric(
    val_stats: Dict[str, Any],
    metric_name: str,
) -> float:
    if metric_name == "val_macro_f1":
        return float(val_stats["macro_f1"])
    if metric_name == "val_acc":
        return float(val_stats["acc"])
    if metric_name == "val_loss":
        return -float(val_stats["loss"])
    raise ValueError(f"Unsupported known-only selection metric: {metric_name}")


def _select_open_conf_metric(
    open_conf_stats: Dict[str, Any],
    metric_name: str,
) -> float:
    if metric_name not in open_conf_stats:
        raise ValueError(f"Unsupported open-conf selection metric: {metric_name}")
    return float(open_conf_stats[metric_name])


# -----------------------------
# training
# -----------------------------
def train_classifier(
    model: nn.Module,
    train_loader,
    val_loader,
    num_classes: int,
    device: str = "cuda",
    epochs: int = 20,
    lr: float = 1e-3,
    weight_decay: float = 0.0,
    lambda_center: float = 0.1,
    save_root: str = "results_baseline",
    class_names: Optional[list[str]] = None,
    run_name: Optional[str] = None,
    config_dict: Optional[Dict[str, Any]] = None,
    early_stopping_patience: Optional[int] = None,

    label_smoothing: float = 0.1,
    entropy_loss_weight: float = 0.0,
    class_weight_mode: Optional[str] = None,
    grad_clip_norm: Optional[float] = None,
    scheduler_name: str = "cosine",
    scheduler_factor: float = 0.5,
    scheduler_patience: int = 5,
    scheduler_min_lr: float = 1e-7,
    model_selection_metric: str = "val_macro_f1",

    val_open_loader=None,
    val_known_balanced_loader=None,
    val_open_balanced_loader=None,
    early_stopping_mode: str = "known_only",
    open_conf_selection_metric: str = "dqn_proxy_expanded5",
    confidence_temperature: float = 1.0,
):
    timestamp = datetime.now().strftime("%H-%M_%m-%d-%y")

    use_timestamped_run_dir = True
    overwrite_existing_run = False
    if config_dict is not None:
        use_timestamped_run_dir = bool(config_dict.get("use_timestamped_run_dir", True))
        overwrite_existing_run = bool(config_dict.get("overwrite_existing_run", False))

    if run_name:
        run_dir_name = f"{timestamp}_{run_name}" if use_timestamped_run_dir else str(run_name)
    else:
        run_dir_name = timestamp

    save_dir = os.path.join(save_root, run_dir_name)
    if os.path.isdir(save_dir) and os.listdir(save_dir) and not overwrite_existing_run:
        raise FileExistsError(
            f"Refusing to overwrite existing non-empty run directory: {save_dir}. "
            "Set overwrite_existing_run=True or choose a new run_name."
        )
    os.makedirs(save_dir, exist_ok=True)

    if config_dict is not None:
        with open(os.path.join(save_dir, "config.json"), "w") as f:
            json.dump(config_dict, f, indent=2)

    progress_interval = 25
    if config_dict is not None:
        progress_interval = int(config_dict.get("progress_interval", progress_interval))
    progress_interval = max(1, progress_interval)

    progress_path = os.path.join(save_dir, "train_progress.json")

    def write_progress(**payload):
        payload.setdefault("run_name", run_name)
        payload.setdefault("time", time.strftime("%Y-%m-%dT%H:%M:%S%z"))
        tmp_path = progress_path + ".tmp"
        with open(tmp_path, "w") as f:
            json.dump(payload, f, indent=2)
        os.replace(tmp_path, progress_path)

    model.to(device)

    class_weights = None
    if class_weight_mode is not None and class_weight_mode.lower() == "balanced":
        class_weights = build_class_weight_tensor(train_loader, num_classes=num_classes, device=device)

    ce_loss = nn.CrossEntropyLoss(
        label_smoothing=label_smoothing,
        weight=class_weights,
    )
    center_loss = CenterLoss(num_classes=num_classes, feat_dim=256, device=device)

    optimizer = optim.Adam(
        list(model.parameters()) + list(center_loss.parameters()),
        lr=lr,
        weight_decay=weight_decay,
    )

    scheduler = make_scheduler(
        optimizer=optimizer,
        scheduler_name=scheduler_name,
        epochs=epochs,
        scheduler_factor=scheduler_factor,
        scheduler_patience=scheduler_patience,
        scheduler_min_lr=scheduler_min_lr,
    )

    if early_stopping_mode == "open_conf" and (
        val_known_balanced_loader is None or val_open_balanced_loader is None
    ):
        raise RuntimeError(
            "early_stopping_mode='open_conf' requires val_known_balanced_loader and "
            "val_open_balanced_loader."
        )

    def save_checkpoint(
        tag: str,
        epoch: int,
        val_stats: Optional[Dict[str, Any]] = None,
        open_conf_stats: Optional[Dict[str, Any]] = None,
        best_metric: Optional[float] = None,
    ):
        torch.save(
            {
                "model_state_dict": model.state_dict(),
                "num_classes": num_classes,
                "input_len": model.input_len,
                "epoch": epoch,
                "val_stats": val_stats,
                "open_conf_stats": open_conf_stats,
                "best_epoch": best_epoch,
                "best_val_metric": best_metric,
                "best_val_acc": None if val_stats is None else val_stats.get("acc"),
                "best_val_macro_f1": None if val_stats is None else val_stats.get("macro_f1"),
                "class_names": class_names,
                "config": config_dict,
            },
            os.path.join(save_dir, f"{tag}.pt"),
        )

    history = {
        "train_loss": [],
        "train_ce_loss": [],
        "train_entropy_loss": [],
        "train_center_loss": [],
        "val_loss": [],
        "val_acc": [],
        "val_macro_f1": [],
        "val_weighted_f1": [],
        "val_dqn_proxy_softmax3": [],
        "val_dqn_proxy_expanded5": [],
        "lr": [],
    }

    best_metric = -np.inf
    best_epoch = -1
    epochs_since_improve = 0
    last_val_stats = None
    last_open_conf_stats = None

    total_train_batches = len(train_loader)

    for epoch in range(1, epochs + 1):
        epoch_t0 = time.time()
        print(
            f"TRAIN_EPOCH_START | run_name={run_name} | epoch={epoch} | epochs={epochs} | steps={total_train_batches}",
            flush=True,
        )
        write_progress(
            phase="train_epoch",
            epoch=epoch,
            epochs=epochs,
            step=0,
            steps=total_train_batches,
            pct=0.0,
            running_samples=0,
        )

        model.train()
        running_loss = 0.0
        running_ce = 0.0
        running_ent = 0.0
        running_center = 0.0
        running_samples = 0

        pbar = tqdm(
            train_loader,
            desc=f"Epoch {epoch}/{epochs}",
            leave=False,
            mininterval=2.0,
        )

        for batch_idx, batch in enumerate(pbar, start=1):
            x, y = batch[:2]
            x = x.to(device, non_blocking=True)
            y = y.to(device, non_blocking=True)

            logits, features = model(x, return_features=True)

            ce = ce_loss(logits, y)
            center = center_loss(features, y) if lambda_center > 0 else torch.tensor(0.0, device=device)
            ent = softmax_entropy_from_logits(logits).mean() if entropy_loss_weight > 0 else torch.tensor(0.0, device=device)

            loss = ce + lambda_center * center + entropy_loss_weight * ent

            optimizer.zero_grad()
            loss.backward()

            if grad_clip_norm is not None:
                torch.nn.utils.clip_grad_norm_(
                    list(model.parameters()) + list(center_loss.parameters()),
                    max_norm=grad_clip_norm,
                )

            optimizer.step()

            bs = y.size(0)
            running_loss += loss.item() * bs
            running_ce += ce.item() * bs
            running_ent += ent.item() * bs
            running_center += center.item() * bs
            running_samples += bs

            if (
                batch_idx == 1
                or batch_idx % progress_interval == 0
                or batch_idx == total_train_batches
            ):
                loss_so_far = running_loss / max(running_samples, 1)
                pct = 100.0 * batch_idx / max(total_train_batches, 1)
                elapsed = time.time() - epoch_t0
                steps_per_sec = batch_idx / max(elapsed, 1e-9)
                print(
                    f"TRAIN_STEP | run_name={run_name} | epoch={epoch} | epochs={epochs} "
                    f"| step={batch_idx} | steps={total_train_batches} | pct={pct:.2f} "
                    f"| loss_so_far={loss_so_far:.5f} | steps_per_sec={steps_per_sec:.3f}",
                    flush=True,
                )
                write_progress(
                    phase="train_step",
                    epoch=epoch,
                    epochs=epochs,
                    step=batch_idx,
                    steps=total_train_batches,
                    pct=pct,
                    running_samples=int(running_samples),
                    loss_so_far=float(loss_so_far),
                    steps_per_sec=float(steps_per_sec),
                )

        train_loss = running_loss / max(running_samples, 1)
        train_ce = running_ce / max(running_samples, 1)
        train_ent = running_ent / max(running_samples, 1)
        train_center = running_center / max(running_samples, 1)

        print(
            f"TRAIN_EPOCH_TRAIN_DONE | run_name={run_name} | epoch={epoch} | train_loss={train_loss:.5f}",
            flush=True,
        )
        write_progress(
            phase="validation",
            epoch=epoch,
            epochs=epochs,
            step=total_train_batches,
            steps=total_train_batches,
            pct=100.0,
            train_loss=float(train_loss),
        )

        val_stats = evaluate_classifier(
            model,
            val_loader,
            device=device,
            class_names=class_names,
            save_dir=None,
            return_outputs=False,
        )
        last_val_stats = val_stats

        open_conf_stats = None
        if early_stopping_mode == "open_conf":
            open_conf_stats = evaluate_open_confidence(
                model,
                known_loader=val_known_balanced_loader,
                open_loader=val_open_balanced_loader,
                device=device,
                class_names=class_names,
                save_dir=None,
                prefix="val_open_conf",
                temperature=confidence_temperature,
            )
            last_open_conf_stats = open_conf_stats
        elif val_open_loader is not None:
            open_conf_stats = evaluate_open_confidence(
                model,
                known_loader=val_loader,
                open_loader=val_open_loader,
                device=device,
                class_names=class_names,
                save_dir=None,
                prefix="val_open_conf",
                temperature=confidence_temperature,
            )
            last_open_conf_stats = open_conf_stats

        history["train_loss"].append(train_loss)
        history["train_ce_loss"].append(train_ce)
        history["train_entropy_loss"].append(train_ent)
        history["train_center_loss"].append(train_center)
        history["val_loss"].append(val_stats["loss"])
        history["val_acc"].append(val_stats["acc"])
        history["val_macro_f1"].append(val_stats["macro_f1"])
        history["val_weighted_f1"].append(val_stats["weighted_f1"])
        history["lr"].append(float(optimizer.param_groups[0]["lr"]))

        if open_conf_stats is not None:
            history["val_dqn_proxy_softmax3"].append(open_conf_stats["dqn_proxy_softmax3"])
            history["val_dqn_proxy_expanded5"].append(open_conf_stats["dqn_proxy_expanded5"])
        else:
            history["val_dqn_proxy_softmax3"].append(None)
            history["val_dqn_proxy_expanded5"].append(None)

        log_msg = (
            f"Epoch {epoch:03d} | "
            f"train_loss={train_loss:.4f} | "
            f"ce={train_ce:.4f} | ent={train_ent:.4f} | center={train_center:.4f} | "
            f"val_loss={val_stats['loss']:.4f} | "
            f"val_acc={val_stats['acc']:.4f} | "
            f"val_macro_f1={val_stats['macro_f1']:.4f}"
        )
        if open_conf_stats is not None:
            log_msg += (
                f" | val_dqn_proxy_softmax3={open_conf_stats['dqn_proxy_softmax3']:.4f}"
                f" | val_dqn_proxy_expanded5={open_conf_stats['dqn_proxy_expanded5']:.4f}"
            )
        print(log_msg, flush=True)

        print(
            f"TRAIN_EPOCH_DONE | run_name={run_name} | epoch={epoch} | epochs={epochs} "
            f"| train_loss={train_loss:.5f} | val_loss={val_stats['loss']:.5f} "
            f"| val_acc={val_stats['acc']:.5f} | val_macro_f1={val_stats['macro_f1']:.5f}",
            flush=True,
        )
        write_progress(
            phase="epoch_done",
            epoch=epoch,
            epochs=epochs,
            step=total_train_batches,
            steps=total_train_batches,
            pct=100.0,
            train_loss=float(train_loss),
            val_loss=float(val_stats["loss"]),
            val_acc=float(val_stats["acc"]),
            val_macro_f1=float(val_stats["macro_f1"]),
        )

        if early_stopping_mode == "known_only":
            current_metric = _select_known_only_metric(val_stats, model_selection_metric)
        elif early_stopping_mode == "open_conf":
            current_metric = _select_open_conf_metric(open_conf_stats, open_conf_selection_metric)
        else:
            raise ValueError(f"Unsupported early_stopping_mode: {early_stopping_mode}")

        improved = current_metric > best_metric
        if improved:
            best_metric = current_metric
            best_epoch = epoch
            epochs_since_improve = 0
            save_checkpoint("best_model", epoch, val_stats, open_conf_stats, best_metric)
        else:
            epochs_since_improve += 1

        if epoch in [20, 50, 100]:
            save_checkpoint(f"epoch_{epoch}", epoch, val_stats, open_conf_stats, best_metric)

        if scheduler is not None:
            if scheduler_name.lower() == "plateau":
                scheduler.step(val_stats["loss"])
            else:
                scheduler.step()

        if early_stopping_patience is not None and epochs_since_improve >= early_stopping_patience:
            print(f"Early stopping at epoch {epoch} (best epoch: {best_epoch})")
            break

    save_checkpoint("final_model", epoch, last_val_stats, last_open_conf_stats, best_metric)
    save_training_curves(history, save_dir)

    with open(os.path.join(save_dir, "history.json"), "w") as f:
        json.dump(history, f, indent=2)

    return save_dir, history


# -----------------------------
# experiment runners
# -----------------------------
def run_experiment(cfg: Dict[str, Any], data_root: str) -> Dict[str, Any]:
    print(f"RUN_STAGE | run_name={cfg.get('run_name', '<unset>')} | stage=enter_run_experiment", flush=True)
    run_name = cfg.get("run_name", "run")
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    cfg = copy.deepcopy(cfg)
    cfg["root"] = data_root

    print(f"RUN_STAGE | run_name={run_name} | stage=before_datasetup", flush=True)
    setup = DataSetup(
        root=data_root,
        task=cfg.get("task", "pa"),
        split_mode=cfg.get("split_mode", "closed"),
        unknown_pas=tuple(cfg.get("unknown_pas", ())),

        normalize=cfg.get("normalize", True),
        cache_len=cfg.get("cache_len", 8192),
        cache_root=cfg.get("cache_root", None),
        force_rebuild_cache=cfg.get("force_rebuild_cache", False),
        skip_cache_build=cfg.get("skip_cache_build", False),

        train_frac=cfg.get("train_frac", 0.70),
        val_frac=cfg.get("val_frac", 0.15),
        seed=cfg.get("seed", 0),

        protocols=tuple(cfg["protocols"]) if cfg.get("protocols") is not None else None,
        pas=tuple(cfg["pas"]) if cfg.get("pas") is not None else None,
        return_metadata=cfg.get("return_metadata", False),

        source_type=cfg.get("source_type", "digital"),
        source_name=cfg.get("source_name", "pilot_noisy_torch"),
        source_glob=cfg.get("source_glob", None),
        manifest_path=cfg.get("manifest_path", None),
        dataset_tag=cfg.get("dataset_tag", None),
        noise_tag=cfg.get("noise_tag", None),
        cache_namespace=cfg.get("cache_namespace", None),

        open_val_frac=cfg.get("open_val_frac", None),
        build_balanced_val_open=cfg.get("build_balanced_val_open", True),
        manifold_balance_seed=cfg.get("manifold_balance_seed", None),
    )

    batch_size = cfg.get("batch_size", 8)
    num_workers = cfg.get("num_workers", 0)
    pin_memory = cfg.get("pin_memory", True)

    print(f"RUN_STAGE | run_name={run_name} | stage=build_data_start", flush=True)
    data = build_data_from_setup(
        setup,
        batch_size=batch_size,
        num_workers=num_workers,
        pin_memory=pin_memory,
    )

    print(f"RUN_STAGE | run_name={run_name} | stage=build_data_done", flush=True)
    train_loader = data["train_loader"]
    val_loader = data["val_loader"]
    meta = data["meta"]

    device = cfg.get("device", "cuda" if torch.cuda.is_available() else "cpu")
    num_classes = meta["num_classes"]
    class_names = meta["class_names"]

    val_open_ds = None
    val_open_loader = None
    val_open_source = None
    val_known_balanced_loader = None
    val_open_balanced_loader = None

    if setup.split_mode == "closed":
        test_loader = data["test_loader"]
    else:
        test_known_loader = data["test_known_loader"]
        test_open_loader = data["test_open_loader"]

        val_open_ds, val_open_loader, val_open_source = ensure_val_open_stream(
            data=data,
            batch_size=batch_size,
            num_workers=num_workers,
            pin_memory=pin_memory,
            seed=cfg.get("seed", 0),
            require_true_val_open=cfg.get("require_true_val_open", False),
            allow_val_open_fallback=cfg.get("allow_val_open_fallback", True),
        )

        val_known_balanced_loader = data.get("val_known_balanced_loader", None)
        val_open_balanced_loader = data.get("val_open_balanced_loader", None)

    model = ModulationClassifierReduced(
        num_classes=num_classes,
        input_len=setup.cache_len,
        mlp_dropout=cfg.get("mlp_dropout", 0.3),
    )

    run_name = cfg.get("run_name", None)

    print(f"RUN_STAGE | run_name={run_name} | stage=train_classifier_start", flush=True)
    save_dir, history = train_classifier(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        num_classes=num_classes,
        device=device,
        epochs=cfg.get("epochs", 20),
        lr=cfg.get("lr", 1e-3),
        weight_decay=cfg.get("weight_decay", 0.0),
        lambda_center=cfg.get("lambda_center", 0.1),
        save_root=cfg.get("save_root", "results_pa_baseline"),
        class_names=class_names,
        run_name=run_name,
        config_dict=cfg,
        early_stopping_patience=cfg.get("early_stopping_patience", None),

        label_smoothing=cfg.get("label_smoothing", 0.1),
        entropy_loss_weight=cfg.get("entropy_loss_weight", 0.0),
        class_weight_mode=cfg.get("class_weight_mode", None),
        grad_clip_norm=cfg.get("grad_clip_norm", None),
        scheduler_name=cfg.get("scheduler_name", "cosine"),
        scheduler_factor=cfg.get("scheduler_factor", 0.5),
        scheduler_patience=cfg.get("scheduler_patience", 5),
        scheduler_min_lr=cfg.get("scheduler_min_lr", 1e-7),
        model_selection_metric=cfg.get("model_selection_metric", "val_macro_f1"),

        val_open_loader=val_open_loader,
        val_known_balanced_loader=val_known_balanced_loader,
        val_open_balanced_loader=val_open_balanced_loader,
        early_stopping_mode=cfg.get("early_stopping_mode", "known_only"),
        open_conf_selection_metric=cfg.get("open_conf_selection_metric", "dqn_proxy_expanded5"),
        confidence_temperature=cfg.get("confidence_temperature", 1.0),
    )

    print(f"RUN_STAGE | run_name={run_name} | stage=post_train_eval_start", flush=True)

    ckpt = torch.load(
        os.path.join(save_dir, "best_model.pt"),
        map_location=device,
        weights_only=False,
    )

    best_model = ModulationClassifierReduced(
        num_classes=ckpt["num_classes"],
        input_len=ckpt["input_len"],
        mlp_dropout=cfg.get("mlp_dropout", 0.3),
    ).to(device)
    best_model.load_state_dict(ckpt["model_state_dict"])

    best_epoch = ckpt.get("epoch")
    best_val_metric = ckpt.get("best_val_metric")
    val_stats = ckpt.get("val_stats") or {}
    best_open_conf_stats = ckpt.get("open_conf_stats") or {}
    best_val_acc = ckpt.get("best_val_acc")
    best_val_macro_f1 = ckpt.get("best_val_macro_f1")
    available_checkpoints = list_available_checkpoints(save_dir)

    if setup.split_mode == "closed":
        test_stats = evaluate_classifier(
            best_model,
            test_loader,
            device=device,
            class_names=class_names,
            save_dir=save_dir,
            cm_filename="test_confusion_matrix.png",
        )

        summary = {
            "run_name": run_name,
            "save_dir": save_dir,
            "task": setup.task,
            "split_mode": setup.split_mode,

            "num_classes": num_classes,
            "class_names": class_names,

            "best_epoch": best_epoch,
            "best_val_metric": best_val_metric,
            "best_val_acc": best_val_acc,
            "best_val_macro_f1": best_val_macro_f1,

            "test_loss": test_stats["loss"],
            "test_acc": test_stats["acc"],
            "test_macro_f1": test_stats["macro_f1"],
            "test_weighted_f1": test_stats["weighted_f1"],
            "test_n_samples": test_stats["n_samples"],

            "n_train": meta.get("n_train"),
            "n_val": meta.get("n_val"),
            "n_test": meta.get("n_test"),

            "cache_len": cfg.get("cache_len", 8192),
            "batch_size": batch_size,
            "lr": cfg.get("lr", 1e-3),
            "weight_decay": cfg.get("weight_decay", 0.0),
            "lambda_center": cfg.get("lambda_center", 0.1),
            "label_smoothing": cfg.get("label_smoothing", 0.1),
            "entropy_loss_weight": cfg.get("entropy_loss_weight", 0.0),
            "mlp_dropout": cfg.get("mlp_dropout", 0.3),
            "class_weight_mode": cfg.get("class_weight_mode", None),
            "grad_clip_norm": cfg.get("grad_clip_norm", None),
            "scheduler_name": cfg.get("scheduler_name", "cosine"),
            "epochs": cfg.get("epochs", 20),
            "seed": cfg.get("seed", 0),

            "source_type": meta.get("source_type"),
            "source_name": meta.get("source_name"),
            "dataset_tag": meta.get("dataset_tag"),
            "noise_tag": meta.get("noise_tag"),

            "available_checkpoints": available_checkpoints,
        }

    else:
        known_stats = evaluate_classifier(
            best_model,
            test_known_loader,
            device=device,
            class_names=class_names,
            save_dir=save_dir,
            cm_filename="test_known_confusion_matrix.png",
        )

        test_open_conf_stats = evaluate_open_confidence(
            best_model,
            known_loader=test_known_loader,
            open_loader=test_open_loader,
            device=device,
            class_names=class_names,
            save_dir=save_dir,
            prefix="test_open_conf",
            temperature=cfg.get("confidence_temperature", 1.0),
        )

        val_manifold_stats = None
        if val_known_balanced_loader is not None and val_open_balanced_loader is not None:
            val_manifold_stats = evaluate_open_confidence(
                best_model,
                known_loader=val_known_balanced_loader,
                open_loader=val_open_balanced_loader,
                device=device,
                class_names=class_names,
                save_dir=save_dir,
                prefix="val_open_conf",
                temperature=cfg.get("confidence_temperature", 1.0),
            )

        summary = {
            "run_name": run_name,
            "save_dir": save_dir,
            "task": setup.task,
            "split_mode": setup.split_mode,

            "unknown_pas": list(setup.unknown_pas),
            "known_pa_names": meta.get("known_pa_names"),
            "unknown_pa_names": meta.get("unknown_pa_names"),
            "open_label": meta.get("open_label"),
            "known_label_map": meta.get("known_label_map"),

            "num_classes": num_classes,
            "class_names": class_names,

            "best_epoch": best_epoch,
            "best_val_metric": best_val_metric,
            "best_val_acc": best_val_acc,
            "best_val_macro_f1": best_val_macro_f1,
            "best_val_dqn_proxy_softmax3": best_open_conf_stats.get("dqn_proxy_softmax3"),
            "best_val_dqn_proxy_expanded5": best_open_conf_stats.get("dqn_proxy_expanded5"),

            "val_open_source": val_open_source,
            "n_val_open": None if val_open_ds is None else len(val_open_ds),
            "n_val_known_balanced": meta.get("n_val_known_balanced"),
            "n_val_open_balanced": meta.get("n_val_open_balanced"),

            "test_known_loss": known_stats["loss"],
            "test_known_acc": known_stats["acc"],
            "test_known_macro_f1": known_stats["macro_f1"],
            "test_known_weighted_f1": known_stats["weighted_f1"],
            "test_known_n_samples": known_stats["n_samples"],

            "test_pmax_auroc": test_open_conf_stats["pmax_auroc"],
            "test_p1p2_auroc": test_open_conf_stats["p1p2_auroc"],
            "test_entropy_auroc": test_open_conf_stats["entropy_auroc"],
            "test_energy_auroc": test_open_conf_stats["energy_auroc"],
            "test_logit_variance_auroc": test_open_conf_stats["logit_variance_auroc"],
            "test_softmax3_mean_auroc": test_open_conf_stats["softmax3_mean_auroc"],
            "test_expanded5_mean_auroc": test_open_conf_stats["expanded5_mean_auroc"],
            "test_dqn_proxy_softmax3": test_open_conf_stats["dqn_proxy_softmax3"],
            "test_dqn_proxy_expanded5": test_open_conf_stats["dqn_proxy_expanded5"],

            "test_known_pmax_mean": test_open_conf_stats["known_pmax_mean"],
            "test_open_pmax_mean": test_open_conf_stats["open_pmax_mean"],
            "test_known_p1p2_mean": test_open_conf_stats["known_p1p2_mean"],
            "test_open_p1p2_mean": test_open_conf_stats["open_p1p2_mean"],
            "test_known_entropy_mean": test_open_conf_stats["known_entropy_mean"],
            "test_open_entropy_mean": test_open_conf_stats["open_entropy_mean"],

            "val_softmax3_mean_auroc": None if val_manifold_stats is None else val_manifold_stats["softmax3_mean_auroc"],
            "val_expanded5_mean_auroc": None if val_manifold_stats is None else val_manifold_stats["expanded5_mean_auroc"],
            "val_dqn_proxy_softmax3": None if val_manifold_stats is None else val_manifold_stats["dqn_proxy_softmax3"],
            "val_dqn_proxy_expanded5": None if val_manifold_stats is None else val_manifold_stats["dqn_proxy_expanded5"],

            "n_train": meta.get("n_train"),
            "n_val": meta.get("n_val"),
            "n_test_known": meta.get("n_test_known"),
            "n_test_open": meta.get("n_test_open"),
            "test_open_n_samples": len(data["test_open_ds"]),

            "cache_len": cfg.get("cache_len", 8192),
            "batch_size": batch_size,
            "lr": cfg.get("lr", 1e-3),
            "weight_decay": cfg.get("weight_decay", 0.0),
            "lambda_center": cfg.get("lambda_center", 0.1),
            "label_smoothing": cfg.get("label_smoothing", 0.1),
            "entropy_loss_weight": cfg.get("entropy_loss_weight", 0.0),
            "mlp_dropout": cfg.get("mlp_dropout", 0.3),
            "class_weight_mode": cfg.get("class_weight_mode", None),
            "grad_clip_norm": cfg.get("grad_clip_norm", None),
            "scheduler_name": cfg.get("scheduler_name", "cosine"),
            "early_stopping_mode": cfg.get("early_stopping_mode", "known_only"),
            "open_conf_selection_metric": cfg.get("open_conf_selection_metric", "dqn_proxy_expanded5"),
            "epochs": cfg.get("epochs", 20),
            "seed": cfg.get("seed", 0),

            "source_type": meta.get("source_type"),
            "source_name": meta.get("source_name"),
            "dataset_tag": meta.get("dataset_tag"),
            "noise_tag": meta.get("noise_tag"),

            "available_checkpoints": available_checkpoints,
        }

    print(f"RUN_STAGE | run_name={run_name} | stage=train_classifier_done", flush=True)

    # Preserve paper/system-level identity fields for manifest-driven final experiments.
    for _k in [
        "paper_set",
        "protocol_tag",
        "family_tag",
        "pas",
        "protocols",
        "cache_root",
        "run_schema_version",
        "use_timestamped_run_dir",
        "notes",
    ]:
        if _k in cfg:
            summary[_k] = cfg.get(_k)

    summary.setdefault("run_schema_version", "final_parallel_experiment_system")
    summary.setdefault("cache_root", setup.cache_root)
    summary.setdefault("pas", None if setup.pas is None else list(setup.pas))
    summary.setdefault("protocols", None if setup.protocols is None else list(setup.protocols))

    print(f"RUN_STAGE | run_name={run_name} | stage=summary_write", flush=True)
    save_experiment_summary(summary, save_dir)

    try:
        if hasattr(data.get("dataset", None), "close"):
            data["dataset"].close()
    except Exception:
        pass

    cleanup_experiment_objects(
        train_loader,
        val_loader,
        data.get("test_loader", None),
        data.get("test_known_loader", None),
        data.get("test_open_loader", None),
        val_open_loader,
        val_known_balanced_loader,
        val_open_balanced_loader,
        data.get("train_ds", None),
        data.get("val_ds", None),
        data.get("val_open_ds", None),
        data.get("val_known_balanced_ds", None),
        data.get("val_open_balanced_ds", None),
        data.get("test_ds", None),
        data.get("test_known_ds", None),
        data.get("test_open_ds", None),
        model,
        best_model,
    )

    del data
    del train_loader
    del val_loader
    if setup.split_mode == "closed":
        del test_loader
    else:
        del test_known_loader
        del test_open_loader
    del model
    del best_model
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return summary


def run_experiment_suite(
    experiment_list,
    data_root: str,
    leaderboard_path: str = "experiment_leaderboard.csv",
):
    summaries = []

    for i, cfg in enumerate(experiment_list, start=1):
        print("=" * 80)
        print(f"Running experiment {i}/{len(experiment_list)}")
        print(json.dumps(cfg, indent=2))
        print("=" * 80)

        summary = run_experiment(cfg, data_root)
        summaries.append(summary)

        df = pd.DataFrame(summaries)
        df.to_csv(leaderboard_path, index=False)

        if "test_dqn_proxy_expanded5" in df.columns:
            display(df.sort_values("test_dqn_proxy_expanded5", ascending=False))
        elif "test_dqn_proxy_softmax3" in df.columns:
            display(df.sort_values("test_dqn_proxy_softmax3", ascending=False))
        elif "test_macro_f1" in df.columns:
            display(df.sort_values("test_macro_f1", ascending=False))
        elif "test_known_macro_f1" in df.columns:
            display(df.sort_values("test_known_macro_f1", ascending=False))

    return pd.DataFrame(summaries)