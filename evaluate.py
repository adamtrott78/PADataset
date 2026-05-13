from __future__ import annotations

import os
import gc
from typing import Sequence, Callable, Optional, Dict, Any
from prepData import DataSetup, build_data_from_setup
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
import pandas as pd
from sklearn.metrics import (
    confusion_matrix,
    ConfusionMatrixDisplay,
    f1_score,
    roc_auc_score,
)


def _softmax_np(logits: np.ndarray, temperature: float = 1.0) -> np.ndarray:
    z = logits / float(temperature)
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / np.clip(e.sum(axis=1, keepdims=True), 1e-12, None)


def compute_confidence_features(
    logits: np.ndarray,
    probs: Optional[np.ndarray] = None,
    temperature: float = 1.0,
) -> Dict[str, np.ndarray]:
    if probs is None:
        probs = _softmax_np(logits, temperature=temperature)

    p_max = probs.max(axis=1)

    sorted_probs = np.sort(probs, axis=1)
    p1_p2 = sorted_probs[:, -1] - sorted_probs[:, -2]

    probs_clip = np.clip(probs, 1e-12, 1.0)
    entropy = -np.sum(probs_clip * np.log(probs_clip), axis=1)

    scaled_logits = logits / float(temperature)
    energy = (
        float(temperature)
        * torch.logsumexp(torch.tensor(scaled_logits, dtype=torch.float32), dim=1)
    ).numpy()

    abs_logits = np.abs(logits)
    logit_variance = np.var(
        abs_logits - abs_logits.mean(axis=1, keepdims=True),
        axis=1,
    )

    return {
        "p_max": p_max,
        "p1_p2": p1_p2,
        "entropy": entropy,
        "energy": energy,
        "logit_variance": logit_variance,
    }


def _compute_safe_classification_metrics(
    labels_np: np.ndarray,
    preds_np: np.ndarray,
    class_names: Optional[list[str]] = None,
) -> Dict[str, Any]:
    """
    Closed-set metrics are only valid for labels in [0, num_classes-1].
    Open-set loaders may contain y=-1, so we drop invalid labels here.
    """
    valid_mask = labels_np >= 0
    valid_labels = labels_np[valid_mask]
    valid_preds = preds_np[valid_mask]

    if valid_labels.size == 0:
        cm = np.zeros((0, 0), dtype=int)
        return {
            "acc": np.nan,
            "macro_f1": np.nan,
            "weighted_f1": np.nan,
            "confusion_matrix": cm,
            "class_names": [] if class_names is None else class_names,
            "n_valid_samples": 0,
        }

    acc = float(np.mean(valid_preds == valid_labels))
    macro_f1 = float(f1_score(valid_labels, valid_preds, average="macro"))
    weighted_f1 = float(f1_score(valid_labels, valid_preds, average="weighted"))
    cm = confusion_matrix(valid_labels, valid_preds)

    if class_names is None:
        out_class_names = [str(i) for i in range(cm.shape[0])]
    elif len(class_names) != cm.shape[0]:
        # Open-PA runs can have a known-class confusion matrix whose dimension is
        # smaller than the original PA universe. Never let plotting/reporting crash
        # the run finalization just because label display names are stale or full-set.
        print(
            "EVAL_WARN | confusion_matrix_label_mismatch "
            f"| cm_shape={cm.shape} | n_class_names={len(class_names)} "
            "| using_numeric_display_labels",
            flush=True,
        )
        out_class_names = [str(i) for i in range(cm.shape[0])]
    else:
        out_class_names = list(class_names)

    return {
        "acc": acc,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "confusion_matrix": cm,
        "class_names": out_class_names,
        "n_valid_samples": int(valid_labels.size),
    }


@torch.no_grad()
def collect_classifier_outputs(
    model,
    data_loader,
    device: str = "cuda",
    class_names: Optional[list[str]] = None,
):
    model.eval()

    # ignore_index makes open labels like -1 safe
    ce_loss = nn.CrossEntropyLoss(ignore_index=-1)

    total_loss = 0.0
    total_loss_samples = 0
    total_correct = 0
    total_valid_samples = 0
    total_samples = 0

    all_logits = []
    all_probs = []
    all_preds = []
    all_labels = []

    for batch in data_loader:
        if len(batch) == 3:
            x, y, _ = batch
        else:
            x, y = batch

        x = x.to(device, non_blocking=True)
        y = y.to(device, non_blocking=True)

        logits = model(x)
        probs = torch.softmax(logits, dim=1)
        preds = logits.argmax(dim=1)

        valid_mask = (y >= 0) & (y < logits.shape[1])

        if valid_mask.any():
            loss = ce_loss(logits, y)
            bs_valid = int(valid_mask.sum().item())
            total_loss += loss.item() * bs_valid
            total_loss_samples += bs_valid
            total_correct += (preds[valid_mask] == y[valid_mask]).sum().item()
            total_valid_samples += bs_valid

        bs_total = y.size(0)
        total_samples += bs_total

        all_logits.append(logits.cpu().numpy())
        all_probs.append(probs.cpu().numpy())
        all_preds.append(preds.cpu().numpy())
        all_labels.append(y.cpu().numpy())

    logits_np = np.concatenate(all_logits, axis=0)
    probs_np = np.concatenate(all_probs, axis=0)
    preds_np = np.concatenate(all_preds, axis=0)
    labels_np = np.concatenate(all_labels, axis=0)

    avg_loss = total_loss / max(total_loss_samples, 1)

    metric_block = _compute_safe_classification_metrics(
        labels_np=labels_np,
        preds_np=preds_np,
        class_names=class_names,
    )

    return {
        "loss": avg_loss,
        "acc": metric_block["acc"],
        "macro_f1": metric_block["macro_f1"],
        "weighted_f1": metric_block["weighted_f1"],
        "n_samples": int(total_samples),
        "n_valid_samples": metric_block["n_valid_samples"],
        "confusion_matrix": metric_block["confusion_matrix"],
        "labels": labels_np,
        "preds": preds_np,
        "logits": logits_np,
        "probs": probs_np,
        "class_names": metric_block["class_names"],
    }


@torch.no_grad()
def evaluate_classifier(
    model,
    data_loader,
    device: str = "cuda",
    class_names: Optional[list[str]] = None,
    save_dir: Optional[str] = None,
    cm_filename: str = "confusion_matrix.png",
    return_outputs: bool = False,
):
    out = collect_classifier_outputs(
        model=model,
        data_loader=data_loader,
        device=device,
        class_names=class_names,
    )

    cm = out["confusion_matrix"]
    out_class_names = out["class_names"]

    if save_dir is not None and cm.size > 0:
        os.makedirs(save_dir, exist_ok=True)

        fig, ax = plt.subplots(figsize=(8, 8))
        disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=out_class_names)
        disp.plot(ax=ax, cmap="Blues", xticks_rotation=45, colorbar=False)
        plt.title("Confusion Matrix")
        plt.tight_layout()
        plt.savefig(os.path.join(save_dir, cm_filename), dpi=200)
        plt.close()

    if not return_outputs:
        out = {
            "loss": out["loss"],
            "acc": out["acc"],
            "macro_f1": out["macro_f1"],
            "weighted_f1": out["weighted_f1"],
            "n_samples": out["n_samples"],
            "n_valid_samples": out["n_valid_samples"],
            "confusion_matrix": out["confusion_matrix"],
        }

    return out


def _known_higher_auroc(known_values: np.ndarray, open_values: np.ndarray) -> tuple[float, str]:
    y = np.concatenate([
        np.ones(len(known_values), dtype=int),
        np.zeros(len(open_values), dtype=int),
    ])
    raw = np.concatenate([known_values, open_values])

    known_mean = float(np.mean(known_values))
    open_mean = float(np.mean(open_values))

    if known_mean >= open_mean:
        score = raw
        direction = "known_higher"
    else:
        score = -raw
        direction = "known_lower"

    auroc = roc_auc_score(y, score)
    return float(auroc), direction


def _save_overlay_hist(known_vals, open_vals, title, xlabel, path):
    plt.figure(figsize=(8, 5))
    plt.hist(known_vals, bins=50, alpha=0.6, label="Known", density=False)
    plt.hist(open_vals, bins=50, alpha=0.6, label="Unknown/Open", density=False)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("Frequency")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()


@torch.no_grad()
def evaluate_open_confidence(
    model,
    known_loader,
    open_loader,
    device: str = "cuda",
    class_names: Optional[list[str]] = None,
    save_dir: Optional[str] = None,
    prefix: str = "test",
    temperature: float = 1.0,
) -> Dict[str, Any]:
    known_out = collect_classifier_outputs(model, known_loader, device=device, class_names=class_names)
    open_out = collect_classifier_outputs(model, open_loader, device=device, class_names=class_names)

    known_cf = compute_confidence_features(known_out["logits"], known_out["probs"], temperature=temperature)
    open_cf = compute_confidence_features(open_out["logits"], open_out["probs"], temperature=temperature)

    pmax_auroc, pmax_dir = _known_higher_auroc(known_cf["p_max"], open_cf["p_max"])
    p1p2_auroc, p1p2_dir = _known_higher_auroc(known_cf["p1_p2"], open_cf["p1_p2"])
    ent_auroc, ent_dir = _known_higher_auroc(known_cf["entropy"], open_cf["entropy"])
    energy_auroc, energy_dir = _known_higher_auroc(known_cf["energy"], open_cf["energy"])
    var_auroc, var_dir = _known_higher_auroc(known_cf["logit_variance"], open_cf["logit_variance"])

    softmax3_mean_auroc = float(np.mean([pmax_auroc, p1p2_auroc, ent_auroc]))
    expanded5_mean_auroc = float(np.mean([pmax_auroc, p1p2_auroc, ent_auroc, energy_auroc, var_auroc]))

    known_macro_f1 = float(known_out["macro_f1"])
    dqn_proxy_softmax3 = float(np.sqrt(max(known_macro_f1, 0.0) * max(softmax3_mean_auroc, 0.0)))
    dqn_proxy_expanded5 = float(np.sqrt(max(known_macro_f1, 0.0) * max(expanded5_mean_auroc, 0.0)))

    if save_dir is not None:
        os.makedirs(save_dir, exist_ok=True)
        _save_overlay_hist(
            known_cf["p_max"],
            open_cf["p_max"],
            title="Softmax p_max Distribution",
            xlabel="p_max",
            path=os.path.join(save_dir, f"{prefix}_pmax_hist.png"),
        )
        _save_overlay_hist(
            known_cf["p1_p2"],
            open_cf["p1_p2"],
            title="Softmax p1-p2 Distribution",
            xlabel="p1-p2",
            path=os.path.join(save_dir, f"{prefix}_p1p2_hist.png"),
        )
        _save_overlay_hist(
            known_cf["entropy"],
            open_cf["entropy"],
            title="Softmax Entropy Distribution",
            xlabel="entropy",
            path=os.path.join(save_dir, f"{prefix}_entropy_hist.png"),
        )

    return {
        "known_n": int(len(known_out["labels"])),
        "open_n": int(len(open_out["labels"])),

        "known_closed_acc": known_out["acc"],
        "known_closed_macro_f1": known_out["macro_f1"],

        "pmax_auroc": pmax_auroc,
        "pmax_direction": pmax_dir,
        "p1p2_auroc": p1p2_auroc,
        "p1p2_direction": p1p2_dir,
        "entropy_auroc": ent_auroc,
        "entropy_direction": ent_dir,
        "energy_auroc": energy_auroc,
        "energy_direction": energy_dir,
        "logit_variance_auroc": var_auroc,
        "logit_variance_direction": var_dir,

        "softmax3_mean_auroc": softmax3_mean_auroc,
        "expanded5_mean_auroc": expanded5_mean_auroc,
        "dqn_proxy_softmax3": dqn_proxy_softmax3,
        "dqn_proxy_expanded5": dqn_proxy_expanded5,

        "known_pmax_mean": float(np.mean(known_cf["p_max"])),
        "open_pmax_mean": float(np.mean(open_cf["p_max"])),
        "known_p1p2_mean": float(np.mean(known_cf["p1_p2"])),
        "open_p1p2_mean": float(np.mean(open_cf["p1_p2"])),
        "known_entropy_mean": float(np.mean(known_cf["entropy"])),
        "open_entropy_mean": float(np.mean(open_cf["entropy"])),
        "known_energy_mean": float(np.mean(known_cf["energy"])),
        "open_energy_mean": float(np.mean(open_cf["energy"])),
        "known_logit_variance_mean": float(np.mean(known_cf["logit_variance"])),
        "open_logit_variance_mean": float(np.mean(open_cf["logit_variance"])),
    }

def _make_setup_from_run_config(config: Dict[str, Any], data_root: Optional[str] = None) -> DataSetup:
    root = data_root or config.get("root")
    if root is None:
        raise ValueError("Need data_root or config['root'] to rebuild run splits")

    return DataSetup(
        root=root,
        task=config.get("task", "pa"),
        split_mode=config.get("split_mode", "closed"),
        unknown_pas=tuple(config.get("unknown_pas", ())),

        normalize=config.get("normalize", True),
        cache_len=config.get("cache_len", 8192),
        cache_root=config.get("cache_root", None),
        force_rebuild_cache=config.get("force_rebuild_cache", False),
        skip_cache_build=config.get("skip_cache_build", False),

        train_frac=config.get("train_frac", 0.70),
        val_frac=config.get("val_frac", 0.15),
        seed=config.get("seed", 0),

        protocols=tuple(config["protocols"]) if config.get("protocols") is not None else None,
        pas=tuple(config["pas"]) if config.get("pas") is not None else None,
        return_metadata=config.get("return_metadata", False),

        source_type=config.get("source_type", "digital"),
        source_name=config.get("source_name", "pilot_noisy_torch"),
        source_glob=config.get("source_glob", None),
        manifest_path=config.get("manifest_path", None),
        dataset_tag=config.get("dataset_tag", None),
        noise_tag=config.get("noise_tag", None),
        cache_namespace=config.get("cache_namespace", None),

        open_val_frac=config.get("open_val_frac", None),
        build_balanced_val_open=config.get("build_balanced_val_open", True),
        manifold_balance_seed=config.get("manifold_balance_seed", None),
    )


def _get_setup_from_handle(handle, data_root: Optional[str] = None) -> DataSetup:
    if hasattr(handle, "setup") and handle.setup is not None:
        return handle.setup
    return _make_setup_from_run_config(handle.config, data_root=data_root)


@torch.no_grad()
def collect_split_outputs_from_loader(
    handle,
    loader,
    split_name: str,
):
    from osr_core import SplitOutputs

    if loader is None:
        return None

    handle.model.eval()

    all_y = []
    all_logits = []
    all_features = []
    all_probs = []
    all_closed_pred = []

    for batch in loader:
        if len(batch) == 3:
            x, y, _ = batch
        else:
            x, y = batch

        x = x.to(handle.device, non_blocking=True)
        logits, features = handle.model(x, return_features=True)
        probs = torch.softmax(logits, dim=1)
        pred = logits.argmax(dim=1)

        all_y.append(y.cpu().numpy())
        all_logits.append(logits.cpu().numpy())
        all_features.append(features.cpu().numpy())
        all_probs.append(probs.cpu().numpy())
        all_closed_pred.append(pred.cpu().numpy())

    return SplitOutputs(
        split_name=split_name,
        y_true=np.concatenate(all_y, axis=0),
        logits=np.concatenate(all_logits, axis=0),
        features=np.concatenate(all_features, axis=0),
        probs=np.concatenate(all_probs, axis=0),
        closed_pred=np.concatenate(all_closed_pred, axis=0),
        sample_meta=None,
    )


def build_osr_eval_bundle(
    handle,
    batch_size: int = 64,
    num_workers: int = 0,
    pin_memory: bool = True,
    data_root: Optional[str] = None,
):
    from osr_core import BackbonePayload

    setup = _get_setup_from_handle(handle, data_root=data_root)

    print("OSR_STAGE | stage=build_data_from_setup_start", flush=True)
    data = build_data_from_setup(
        setup,
        batch_size=batch_size,
        num_workers=num_workers,
        pin_memory=pin_memory,
    )

    print("OSR_STAGE | stage=build_data_from_setup_done", flush=True)

    if setup.split_mode != "open_pa":
        raise ValueError("build_osr_eval_bundle currently expects an open_pa backbone run")

    payload = BackbonePayload(
        meta={
            "run_name": handle.run_name,
            "run_dir": handle.run_dir,
            "checkpoint_tag": handle.checkpoint_tag,
            "unknown_pas": handle.unknown_pas,
            "class_names": handle.class_names,
            "num_classes": handle.num_classes,
            "cache_len": handle.config.get("cache_len"),
            "seed": handle.config.get("seed"),
            "epochs": handle.config.get("epochs"),
            "source_type": handle.config.get("source_type", "digital"),
            "source_name": handle.config.get("source_name", "pilot_noisy_torch"),
            "dataset_tag": handle.config.get("dataset_tag"),
            "noise_tag": handle.config.get("noise_tag"),
        },
        val_known=(print("OSR_STAGE | stage=collect_val_known_start", flush=True) or collect_split_outputs_from_loader(handle, data["val_loader"], "val_known")),
        test_known=(print("OSR_STAGE | stage=collect_test_known_start", flush=True) or collect_split_outputs_from_loader(handle, data["test_known_loader"], "test_known")),
        test_open=(print("OSR_STAGE | stage=collect_test_open_start", flush=True) or collect_split_outputs_from_loader(handle, data["test_open_loader"], "test_open")),
    )
    print("OSR_STAGE | stage=collect_core_splits_done", flush=True)

    extras = {
        "val_open": collect_split_outputs_from_loader(
            handle, data.get("val_open_loader", None), "val_open"
        ),
        "val_known_balanced": collect_split_outputs_from_loader(
            handle, data.get("val_known_balanced_loader", None), "val_known_balanced"
        ),
        "val_open_balanced": collect_split_outputs_from_loader(
            handle, data.get("val_open_balanced_loader", None), "val_open_balanced"
        ),
        "data_meta": data.get("meta", {}),
        "setup": setup,
    }

    try:
        if hasattr(data.get("dataset", None), "close"):
            data["dataset"].close()
    except Exception:
        pass

    del data
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return payload, extras


def choose_osr_calibration_splits(
    payload: BackbonePayload,
    extras: Dict[str, Any],
    prefer_balanced: bool = True,
):
    if prefer_balanced:
        known_cal = extras.get("val_known_balanced", None)
        open_cal = extras.get("val_open_balanced", None)
        if known_cal is not None and open_cal is not None:
            return known_cal, open_cal

    known_cal = payload.val_known
    open_cal = extras.get("val_open", None)

    if known_cal is None or open_cal is None:
        raise RuntimeError("Could not construct known/open calibration splits")

    return known_cal, open_cal


def evaluate_osr_method_on_bundle(
    method,
    payload,
    calibration: Optional[Dict[str, Any]] = None,
    unknown_label_name: str = "unknown",
):
    from osr_core import evaluate_osr_predictions

    method.fit(payload, calibration=calibration)

    unknown_label = payload.meta["num_classes"]

    known_pred = method.predict(payload.test_known, unknown_label=unknown_label)
    open_pred = method.predict(payload.test_open, unknown_label=unknown_label)

    metrics = evaluate_osr_predictions(
        known_split=payload.test_known,
        open_split=payload.test_open,
        known_pred=known_pred,
        open_pred=open_pred,
        known_class_names=payload.meta["class_names"],
        unknown_label_name=unknown_label_name,
    )

    return {
        "method_name": getattr(method, "method_name", method.__class__.__name__),
        "method": method,
        "metrics": metrics,
        "known_pred": known_pred,
        "open_pred": open_pred,
        "params": method.get_params(),
    }
    

def evaluate_osr_method_on_run(
    run_dir: str,
    method_factory: Callable[[], Any],
    calibration_builder: Callable[[Any, Dict[str, Any]], Optional[Dict[str, Any]]],
    checkpoint_tag: str = "best_model",
    batch_size: int = 64,
    num_workers: int = 0,
    pin_memory: bool = True,
    device: Optional[str] = None,
    data_root: Optional[str] = None,
    unknown_label_name: str = "unknown",
):
    from osr_core import load_backbone_run

    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    handle = load_backbone_run(
        run_dir=run_dir,
        checkpoint_tag=checkpoint_tag,
        device=device,
    )

    payload, extras = build_osr_eval_bundle(
        handle,
        batch_size=batch_size,
        num_workers=num_workers,
        pin_memory=pin_memory,
        data_root=data_root,
    )

    method = method_factory()
    calibration = calibration_builder(payload, extras)

    result = evaluate_osr_method_on_bundle(
        method=method,
        payload=payload,
        calibration=calibration,
        unknown_label_name=unknown_label_name,
    )

    result.update({
        "handle": handle,
        "payload": payload,
        "extras": extras,
    })
    return result


def evaluate_multiple_osr_methods_on_run(
    run_dir: str,
    method_specs: Sequence[Dict[str, Any]],
    checkpoint_tag: str = "best_model",
    batch_size: int = 64,
    num_workers: int = 0,
    pin_memory: bool = True,
    device: Optional[str] = None,
    data_root: Optional[str] = None,
    unknown_label_name: str = "unknown",
):
    from osr_core import load_backbone_run

    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    handle = load_backbone_run(
        run_dir=run_dir,
        checkpoint_tag=checkpoint_tag,
        device=device,
    )

    payload, extras = build_osr_eval_bundle(
        handle,
        batch_size=batch_size,
        num_workers=num_workers,
        pin_memory=pin_memory,
        data_root=data_root,
    )

    rows = []
    fitted = {}

    for spec in method_specs:
        method_name = spec["name"]
        method = spec["factory"]()
        calibration = spec["calibration_builder"](payload, extras)

        result = evaluate_osr_method_on_bundle(
            method=method,
            payload=payload,
            calibration=calibration,
            unknown_label_name=unknown_label_name,
        )

        fitted[method_name] = result

        row = {
            "method": method_name,
            **result["metrics"],
        }
        rows.append(row)

    return {
        "handle": handle,
        "payload": payload,
        "extras": extras,
        "rows": rows,
        "fitted": fitted,
        "df": pd.DataFrame(rows),
    }