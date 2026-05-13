from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = REPO_ROOT / "data"
DEFAULT_CACHE_ROOT = (
    REPO_ROOT
    / "_feature_cache_nvme"
    / "len16384"
    / "norm"
    / "ota__ota_core_high_run01__high_run01"
)

PA_ALL = ["PA1", "PA2", "PA3", "PA4", "PA8"]
PROTO_ALL = ["wifi", "bluetooth", "zigbee"]

PAPER_SETS = {
    "OG": ["PA2", "PA3", "PA4", "PA8"],
    "DISTINCT": ["PA1", "PA3", "PA4", "PA8"],
    "MASTER": ["PA1", "PA2", "PA3", "PA4", "PA8"],
}

FAMILY_GRIDS = {
    "smoke": [
        {
            "family_tag": "smoke_ent005_lr2e4",
            "lr": 2e-4,
            "label_smoothing": 0.10,
            "entropy_loss_weight": 0.05,
            "mlp_dropout": 0.30,
            "epochs": 3,
            "early_stopping_patience": None,
        }
    ],
    "baseline": [
        {
            "family_tag": "ref_ent005_lr2e4",
            "lr": 2e-4,
            "label_smoothing": 0.10,
            "entropy_loss_weight": 0.05,
            "mlp_dropout": 0.30,
            "epochs": 60,
            "early_stopping_patience": 10,
        }
    ],
    "search": [
        {
            "family_tag": "ref_ent005_lr2e4",
            "lr": 2e-4,
            "label_smoothing": 0.10,
            "entropy_loss_weight": 0.05,
            "mlp_dropout": 0.30,
            "epochs": 60,
            "early_stopping_patience": 10,
        },
        {
            "family_tag": "ref_ent005_lr5e4",
            "lr": 5e-4,
            "label_smoothing": 0.10,
            "entropy_loss_weight": 0.05,
            "mlp_dropout": 0.30,
            "epochs": 60,
            "early_stopping_patience": 10,
        },
        {
            "family_tag": "ref_noent_lr5e4",
            "lr": 5e-4,
            "label_smoothing": 0.10,
            "entropy_loss_weight": 0.00,
            "mlp_dropout": 0.30,
            "epochs": 60,
            "early_stopping_patience": 10,
        },
        {
            "family_tag": "ref_ls000_noent_lr5e4",
            "lr": 5e-4,
            "label_smoothing": 0.00,
            "entropy_loss_weight": 0.00,
            "mlp_dropout": 0.30,
            "epochs": 60,
            "early_stopping_patience": 10,
        },
    ],
}


def split_csv(s: Optional[str]) -> List[str]:
    if s is None:
        return []
    return [x.strip() for x in str(s).split(",") if x.strip()]


def base_training_config(
    *,
    run_name: str,
    paper_set: str,
    pas: List[str],
    unknown_pa: str,
    family: Dict[str, Any],
    seed: int,
    cache_root: Path,
    save_root: str,
    batch_size: int,
    protocols: Optional[List[str]] = None,
    epochs_override: Optional[int] = None,
    patience_override: Optional[int] = None,
    num_workers: int = 0,
) -> Dict[str, Any]:
    epochs = family["epochs"] if epochs_override is None else epochs_override
    patience = (
        family["early_stopping_patience"]
        if patience_override is None
        else patience_override
    )

    return {
        "run_schema_version": "final_parallel_experiment_system",
        "run_name": run_name,
        "paper_set": paper_set,
        "family_tag": family["family_tag"],
        "protocol_tag": "all" if protocols is None else ",".join(protocols),
        "task": "pa",
        "split_mode": "open_pa",
        "unknown_pas": [unknown_pa],
        "pas": pas,
        "protocols": protocols,

        "normalize": True,
        "cache_len": 16384,
        "cache_root": str(cache_root),
        "force_rebuild_cache": False,
        "skip_cache_build": True,

        "batch_size": batch_size,
        "num_workers": num_workers,
        "pin_memory": True,
        "seed": seed,

        "source_type": "ota",
        "source_name": "ota_core_high_run01",
        "dataset_tag": "ota_core_high_run01",
        "noise_tag": "high_run01",

        "open_val_frac": 0.15,
        "build_balanced_val_open": True,
        "manifold_balance_seed": seed,
        "require_true_val_open": True,
        "allow_val_open_fallback": False,
        "confidence_temperature": 1.0,

        "lr": family["lr"],
        "weight_decay": 0.0,
        "lambda_center": 0.1,
        "label_smoothing": family["label_smoothing"],
        "entropy_loss_weight": family["entropy_loss_weight"],
        "mlp_dropout": family["mlp_dropout"],
        "class_weight_mode": None,
        "grad_clip_norm": None,

        "scheduler_name": "cosine",
        "scheduler_factor": 0.5,
        "scheduler_patience": 5,
        "scheduler_min_lr": 1e-7,

        "early_stopping_mode": "open_conf",
        "model_selection_metric": "val_macro_f1",
        "open_conf_selection_metric": "dqn_proxy_expanded5",

        "epochs": epochs,
        "early_stopping_patience": patience,

        "save_root": save_root,
        "use_timestamped_run_dir": False,
        "overwrite_existing_run": False,
    }
