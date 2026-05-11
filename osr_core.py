from __future__ import annotations

import gc
import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from prepData import DataSetup, build_data_from_setup
from discriminate import ModulationClassifierReduced


# ============================================================
# registry
# ============================================================

CHECKPOINT_TAGS = [
    "best_model",
    "epoch_20",
    "epoch_50",
    "epoch_100",
    "final_model",
]


@dataclass
class CheckpointRecord:
    tag: str
    path: str
    exists: bool
    epoch: Optional[int]
    val_stats: Optional[Dict[str, Any]]
    input_len: Optional[int]
    class_names: Optional[List[str]]
    num_classes: Optional[int]


@dataclass
class RunRecord:
    run_name: str
    run_dir: str
    config_path: str
    config: Dict[str, Any]

    task: str
    split_mode: str
    unknown_pas: List[str]
    cache_len: int
    batch_size: int
    lr: float
    weight_decay: float
    lambda_center: float
    epochs: int
    seed: int

    checkpoints: Dict[str, CheckpointRecord]


def _normalize_checkpoint_tag(tag: str) -> str:
    return tag[:-3] if tag.endswith(".pt") else tag


def _safe_load_json(path: str) -> Dict[str, Any]:
    with open(path, "r") as f:
        return json.load(f)


def _inspect_checkpoint(path: str, tag: str) -> CheckpointRecord:
    if not os.path.isfile(path):
        return CheckpointRecord(
            tag=tag,
            path=path,
            exists=False,
            epoch=None,
            val_stats=None,
            input_len=None,
            class_names=None,
            num_classes=None,
        )

    ckpt = torch.load(path, map_location="cpu", weights_only=False)

    return CheckpointRecord(
        tag=tag,
        path=path,
        exists=True,
        epoch=ckpt.get("epoch"),
        val_stats=ckpt.get("val_stats"),
        input_len=ckpt.get("input_len"),
        class_names=ckpt.get("class_names"),
        num_classes=ckpt.get("num_classes"),
    )


def _build_run_record(run_dir: str) -> Optional[RunRecord]:
    config_path = os.path.join(run_dir, "config.json")
    if not os.path.isfile(config_path):
        return None

    cfg = _safe_load_json(config_path)

    checkpoints: Dict[str, CheckpointRecord] = {}
    for tag in CHECKPOINT_TAGS:
        ckpt_path = os.path.join(run_dir, f"{tag}.pt")
        checkpoints[tag] = _inspect_checkpoint(ckpt_path, tag)

    return RunRecord(
        run_name=cfg.get("run_name", os.path.basename(run_dir)),
        run_dir=run_dir,
        config_path=config_path,
        config=cfg,
        task=cfg.get("task", "pa"),
        split_mode=cfg.get("split_mode", "closed"),
        unknown_pas=list(cfg.get("unknown_pas", [])),
        cache_len=int(cfg.get("cache_len", 8192)),
        batch_size=int(cfg.get("batch_size", 8)),
        lr=float(cfg.get("lr", 1e-3)),
        weight_decay=float(cfg.get("weight_decay", 0.0)),
        lambda_center=float(cfg.get("lambda_center", 0.1)),
        epochs=int(cfg.get("epochs", 20)),
        seed=int(cfg.get("seed", 0)),
        checkpoints=checkpoints,
    )


def build_run_registry(results_root: str) -> List[RunRecord]:
    results_root = os.path.expanduser(results_root)
    if not os.path.isdir(results_root):
        raise FileNotFoundError(f"Results root not found: {results_root}")

    runs: List[RunRecord] = []
    for name in sorted(os.listdir(results_root)):
        run_dir = os.path.join(results_root, name)
        if not os.path.isdir(run_dir):
            continue
        rec = _build_run_record(run_dir)
        if rec is not None:
            runs.append(rec)

    return runs


def filter_runs(
    registry: List[RunRecord],
    *,
    split_mode: Optional[str] = None,
    unknown_pa: Optional[str] = None,
    cache_len: Optional[int] = None,
    seed: Optional[int] = None,
) -> List[RunRecord]:
    out = registry
    if split_mode is not None:
        out = [r for r in out if r.split_mode == split_mode]
    if unknown_pa is not None:
        out = [r for r in out if unknown_pa in r.unknown_pas]
    if cache_len is not None:
        out = [r for r in out if r.cache_len == cache_len]
    if seed is not None:
        out = [r for r in out if r.seed == seed]
    return out


def get_run_by_name(registry: List[RunRecord], run_name: str) -> RunRecord:
    for rec in registry:
        if rec.run_name == run_name:
            return rec
    raise KeyError(f"Run not found: {run_name}")


def list_checkpoint_tags(run: RunRecord, only_existing: bool = True) -> List[str]:
    tags = []
    for tag, rec in run.checkpoints.items():
        if only_existing and not rec.exists:
            continue
        tags.append(tag)
    return tags


# ============================================================
# backbone payload API
# ============================================================

@dataclass
class BackboneHandle:
    run_name: str
    run_dir: str
    checkpoint_tag: str
    checkpoint_path: str

    config: Dict[str, Any]
    checkpoint: Dict[str, Any]

    device: str
    model: torch.nn.Module
    setup: DataSetup

    class_names: List[str]
    num_classes: int
    unknown_pas: List[str]


@dataclass
class SplitOutputs:
    split_name: str
    y_true: np.ndarray
    logits: np.ndarray
    features: np.ndarray
    closed_pred: np.ndarray
    probs: np.ndarray
    sample_meta: Optional[List[Dict[str, Any]]] = None


@dataclass
class BackbonePayload:
    meta: Dict[str, Any]
    val_known: Optional[SplitOutputs]
    test_known: Optional[SplitOutputs]
    test_open: Optional[SplitOutputs]


def _load_json(path: str) -> Dict[str, Any]:
    with open(path, "r") as f:
        return json.load(f)


def _make_setup_from_config(cfg: Dict[str, Any], return_metadata: bool = False) -> DataSetup:
    return DataSetup(
        root=cfg["root"] if "root" in cfg else os.path.expanduser("~/Adam/varMax/PADataset/data"),
        task=cfg.get("task", "pa"),
        split_mode=cfg.get("split_mode", "closed"),
        unknown_pas=tuple(cfg.get("unknown_pas", [])),

        normalize=cfg.get("normalize", True),
        cache_len=cfg.get("cache_len", 8192),
        cache_root=cfg.get("cache_root", None),
        force_rebuild_cache=False,

        train_frac=cfg.get("train_frac", 0.70),
        val_frac=cfg.get("val_frac", 0.15),
        seed=cfg.get("seed", 0),

        protocols=tuple(cfg["protocols"]) if cfg.get("protocols") is not None else None,
        pas=tuple(cfg["pas"]) if cfg.get("pas") is not None else None,
        return_metadata=return_metadata,

        source_type=cfg.get("source_type", "digital"),
        source_name=cfg.get("source_name", "pilot_noisy_torch"),
        source_glob=cfg.get("source_glob", None),
        manifest_path=cfg.get("manifest_path", None),
        dataset_tag=cfg.get("dataset_tag", None),
        noise_tag=cfg.get("noise_tag", None),
        cache_namespace=cfg.get("cache_namespace", None),
    )


def load_backbone_run(
    run_dir: str,
    checkpoint_tag: str,
    device: str = "cuda",
) -> BackboneHandle:
    run_dir = os.path.expanduser(run_dir)
    config_path = os.path.join(run_dir, "config.json")
    if not os.path.isfile(config_path):
        raise FileNotFoundError(f"Missing config.json in {run_dir}")

    cfg = _load_json(config_path)

    checkpoint_tag = _normalize_checkpoint_tag(checkpoint_tag)
    checkpoint_path = os.path.join(run_dir, f"{checkpoint_tag}.pt")
    if not os.path.isfile(checkpoint_path):
        raise FileNotFoundError(f"Missing checkpoint: {checkpoint_path}")

    ckpt = torch.load(checkpoint_path, map_location=device, weights_only=False)

    num_classes = int(ckpt["num_classes"])
    input_len = int(ckpt["input_len"])
    class_names = list(ckpt.get("class_names", []))

    model = ModulationClassifierReduced(
        num_classes=num_classes,
        input_len=input_len,
    ).to(device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    setup = _make_setup_from_config(cfg, return_metadata=False)

    return BackboneHandle(
        run_name=cfg.get("run_name", os.path.basename(run_dir)),
        run_dir=run_dir,
        checkpoint_tag=checkpoint_tag,
        checkpoint_path=checkpoint_path,
        config=cfg,
        checkpoint=ckpt,
        device=device,
        model=model,
        setup=setup,
        class_names=class_names,
        num_classes=num_classes,
        unknown_pas=list(cfg.get("unknown_pas", [])),
    )


def _collect_split_outputs(
    model: torch.nn.Module,
    loader,
    device: str,
    split_name: str,
) -> SplitOutputs:
    all_y = []
    all_logits = []
    all_features = []
    all_probs = []
    all_closed_pred = []
    all_meta = []

    model.eval()
    with torch.no_grad():
        for batch in loader:
            if len(batch) == 3:
                x, y, meta = batch
                all_meta.extend(meta)
            else:
                x, y = batch

            x = x.to(device, non_blocking=True)
            logits, features = model(x, return_features=True)
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
        sample_meta=all_meta if len(all_meta) > 0 else None,
    )


def _build_data_bundle(
    handle: BackboneHandle,
    batch_size: Optional[int] = None,
    num_workers: int = 0,
    pin_memory: bool = True,
    return_sample_meta: bool = False,
):
    setup = _make_setup_from_config(handle.config, return_metadata=return_sample_meta)
    data = build_data_from_setup(
        setup,
        batch_size=batch_size or int(handle.config.get("batch_size", 8)),
        num_workers=num_workers,
        pin_memory=pin_memory,
    )
    return setup, data


def _get_loader_for_split(data: Dict[str, Any], split_name: str):
    if split_name == "val_known":
        return data["val_loader"]
    if split_name == "test_known":
        return data["test_known_loader"]
    if split_name == "test_open":
        return data["test_open_loader"]
    raise ValueError(f"Unsupported split_name: {split_name}")


def _cleanup_data_bundle(data: Optional[Dict[str, Any]]) -> None:
    if data is None:
        return

    try:
        if hasattr(data.get("dataset", None), "close"):
            data["dataset"].close()
    except Exception:
        pass

    del data
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def extract_backbone_outputs(
    handle: BackboneHandle,
    split_name: str,
    batch_size: Optional[int] = None,
    num_workers: int = 0,
    pin_memory: bool = True,
    return_sample_meta: bool = False,
) -> SplitOutputs:
    if split_name not in {"val_known", "test_known", "test_open"}:
        raise ValueError(f"Unsupported split_name: {split_name}")

    data = None
    try:
        setup, data = _build_data_bundle(
            handle,
            batch_size=batch_size,
            num_workers=num_workers,
            pin_memory=pin_memory,
            return_sample_meta=return_sample_meta,
        )

        if setup.split_mode != "open_pa":
            raise ValueError("extract_backbone_outputs currently expects an open_pa backbone run")

        loader = _get_loader_for_split(data, split_name)
        out = _collect_split_outputs(handle.model, loader, handle.device, split_name)
        return out
    finally:
        _cleanup_data_bundle(data)


def build_backbone_payload(
    handle: BackboneHandle,
    include: Sequence[str] = ("val_known", "test_known", "test_open"),
    batch_size: Optional[int] = None,
    num_workers: int = 0,
    pin_memory: bool = True,
    return_sample_meta: bool = False,
) -> BackbonePayload:
    include = set(include)
    data = None

    try:
        setup, data = _build_data_bundle(
            handle,
            batch_size=batch_size,
            num_workers=num_workers,
            pin_memory=pin_memory,
            return_sample_meta=return_sample_meta,
        )

        if setup.split_mode != "open_pa":
            raise ValueError("build_backbone_payload currently expects an open_pa backbone run")

        val_known = None
        test_known = None
        test_open = None

        if "val_known" in include:
            val_known = _collect_split_outputs(
                handle.model,
                _get_loader_for_split(data, "val_known"),
                handle.device,
                "val_known",
            )

        if "test_known" in include:
            test_known = _collect_split_outputs(
                handle.model,
                _get_loader_for_split(data, "test_known"),
                handle.device,
                "test_known",
            )

        if "test_open" in include:
            test_open = _collect_split_outputs(
                handle.model,
                _get_loader_for_split(data, "test_open"),
                handle.device,
                "test_open",
            )

        meta = {
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
        }

        return BackbonePayload(
            meta=meta,
            val_known=val_known,
            test_known=test_known,
            test_open=test_open,
        )
    finally:
        _cleanup_data_bundle(data)


# ============================================================
# base OSR contract
# ============================================================

class BaseOSRMethod(ABC):
    method_name: str = "base"

    @abstractmethod
    def fit(self, payload: BackbonePayload, calibration: Dict[str, Any] | None = None) -> None:
        raise NotImplementedError

    @abstractmethod
    def score(self, split: SplitOutputs) -> np.ndarray:
        # larger score => more likely unknown
        raise NotImplementedError

    @abstractmethod
    def predict(self, split: SplitOutputs, unknown_label: int) -> Dict[str, np.ndarray]:
        """
        returns:
          unknown_score: [N]
          is_unknown:    [N] bool
          closed_pred:   [N]
          final_pred:    [N]
        """
        raise NotImplementedError

    @abstractmethod
    def get_params(self) -> Dict[str, Any]:
        raise NotImplementedError


# ============================================================
# OSR metrics
# ============================================================

def _safe_binary_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    return {
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }


def _per_class_recall(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    class_ids: List[int],
) -> Dict[int, float]:
    out: Dict[int, float] = {}
    for cls in class_ids:
        mask = (y_true == cls)
        if mask.sum() == 0:
            continue
        out[int(cls)] = float(np.mean(y_pred[mask] == cls))
    return out


def _per_class_reject_rate(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    class_ids: List[int],
    unknown_label: int,
) -> Dict[int, float]:
    out: Dict[int, float] = {}
    for cls in class_ids:
        mask = (y_true == cls)
        if mask.sum() == 0:
            continue
        out[int(cls)] = float(np.mean(y_pred[mask] == unknown_label))
    return out


def evaluate_osr_predictions(
    known_split: SplitOutputs,
    open_split: SplitOutputs,
    known_pred: Dict[str, np.ndarray],
    open_pred: Dict[str, np.ndarray],
    known_class_names: List[str],
    unknown_label_name: str = "unknown",
) -> Dict[str, Any]:
    num_known = len(known_class_names)
    unknown_label = num_known
    class_ids = list(range(num_known))

    # --------------------------------------------------
    # known-only metrics BEFORE rejection (backbone only)
    # --------------------------------------------------
    known_closed_acc = float(accuracy_score(known_split.y_true, known_pred["closed_pred"]))
    known_closed_macro_f1 = float(
        f1_score(known_split.y_true, known_pred["closed_pred"], average="macro")
    )
    known_closed_per_class_recall = _per_class_recall(
        known_split.y_true,
        known_pred["closed_pred"],
        class_ids,
    )

    # --------------------------------------------------
    # known-only metrics AFTER rejection (threshold-sensitive)
    # --------------------------------------------------
    known_osr_acc = float(accuracy_score(known_split.y_true, known_pred["final_pred"]))
    known_osr_macro_f1 = float(
        f1_score(
            known_split.y_true,
            known_pred["final_pred"],
            labels=class_ids,
            average="macro",
            zero_division=0,
        )
    )
    known_reject_rate = float((known_pred["final_pred"] == unknown_label).mean())

    known_osr_per_class_recall = _per_class_recall(
        known_split.y_true,
        known_pred["final_pred"],
        class_ids,
    )
    known_osr_per_class_reject_rate = _per_class_reject_rate(
        known_split.y_true,
        known_pred["final_pred"],
        class_ids,
        unknown_label=unknown_label,
    )

    known_osr_min_per_class_recall = (
        min(known_osr_per_class_recall.values())
        if len(known_osr_per_class_recall) > 0 else None
    )
    known_osr_max_per_class_reject_rate = (
        max(known_osr_per_class_reject_rate.values())
        if len(known_osr_per_class_reject_rate) > 0 else None
    )

    # --------------------------------------------------
    # binary unknown-detection metrics
    # --------------------------------------------------
    known_is_unknown = known_pred["is_unknown"].astype(int)
    open_is_unknown = open_pred["is_unknown"].astype(int)

    bin_true = np.concatenate([
        np.zeros(len(known_is_unknown), dtype=int),
        np.ones(len(open_is_unknown), dtype=int),
    ])
    bin_pred = np.concatenate([known_is_unknown, open_is_unknown])

    detect = _safe_binary_metrics(bin_true, bin_pred)

    known_accept_rate = float((known_pred["is_unknown"] == 0).mean())
    unknown_detect_rate = float((open_pred["is_unknown"] == 1).mean())
    bias_delta = float(known_accept_rate - unknown_detect_rate)

    # --------------------------------------------------
    # full OSR labels
    # --------------------------------------------------
    y_known_final = known_pred["final_pred"]
    y_open_true = np.full(len(open_split.y_true), unknown_label, dtype=int)
    y_open_final = open_pred["final_pred"]

    y_all_true = np.concatenate([known_split.y_true, y_open_true])
    y_all_pred = np.concatenate([y_known_final, y_open_final])

    osr_acc = float(accuracy_score(y_all_true, y_all_pred))
    osr_macro_f1 = float(f1_score(y_all_true, y_all_pred, average="macro"))

    labels = class_ids + [unknown_label]
    cm = confusion_matrix(y_all_true, y_all_pred, labels=labels)

    out = {
        # backbone-only known metrics
        "known_closed_acc": known_closed_acc,
        "known_closed_macro_f1": known_closed_macro_f1,
        "known_closed_per_class_recall": known_closed_per_class_recall,

        # threshold-sensitive known metrics
        "known_osr_acc": known_osr_acc,
        "known_osr_macro_f1": known_osr_macro_f1,
        "known_reject_rate": known_reject_rate,
        "known_osr_per_class_recall": known_osr_per_class_recall,
        "known_osr_per_class_reject_rate": known_osr_per_class_reject_rate,
        "known_osr_min_per_class_recall": known_osr_min_per_class_recall,
        "known_osr_max_per_class_reject_rate": known_osr_max_per_class_reject_rate,

        # unknown detection
        "unknown_precision": detect["precision"],
        "unknown_recall": detect["recall"],
        "unknown_f1": detect["f1"],
        "known_accept_rate": known_accept_rate,
        "unknown_detect_rate": unknown_detect_rate,
        "bias_delta": bias_delta,

        # full OSR
        "osr_acc": osr_acc,
        "osr_macro_f1": osr_macro_f1,
        "osr_confusion_matrix": cm,
        "label_names_with_unknown": known_class_names + [unknown_label_name],
    }

    if "unknown_score" in known_pred and "unknown_score" in open_pred:
        score_all = np.concatenate([known_pred["unknown_score"], open_pred["unknown_score"]])
        try:
            out["unknown_auroc"] = float(roc_auc_score(bin_true, score_all))
        except Exception:
            out["unknown_auroc"] = None
    else:
        out["unknown_auroc"] = None

    return out