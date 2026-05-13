from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional

from experiments.pa_constants import DEFAULT_CACHE_ROOT, FAMILY_GRIDS, PAPER_SETS


SOURCE_PROFILES: Dict[str, Dict[str, Any]] = {
    "digital_noisy_legacy": {
        "source_type": "digital",
        "source_name": "pilot_noisy_torch",
        "cache_len": 16384,
        "purpose": "legacy reconstruction / optional bridge rerun",
        "priority_tier": "reference",
    },
    "ota_core_high_run01": {
        "source_type": "ota",
        "source_name": "ota_core_high_run01",
        "dataset_tag": "ota_core_high_run01",
        "noise_tag": "high_run01",
        "cache_len": 16384,
        "cache_root": str(DEFAULT_CACHE_ROOT),
        "purpose": "final OTA experiments",
        "priority_tier": "primary",
    },
}


FAMILY_CONFIGS: Dict[str, Dict[str, Any]] = {
    "smoke_ent005_lr2e4": {
        "family_tag": "smoke_ent005_lr2e4",
        "lr": 2e-4,
        "label_smoothing": 0.10,
        "entropy_loss_weight": 0.05,
        "mlp_dropout": 0.30,
        "epochs": 3,
        "early_stopping_patience": None,
        "maps_from_legacy": None,
    },
    "ref_ent005_lr2e4": {
        "family_tag": "ref_ent005_lr2e4",
        "lr": 2e-4,
        "label_smoothing": 0.10,
        "entropy_loss_weight": 0.05,
        "mlp_dropout": 0.30,
        "epochs": 60,
        "early_stopping_patience": 10,
        "maps_from_legacy": ["ref_base_ent005", "ref_base_lr2e4"],
    },
    "ref_ent005_lr5e4": {
        "family_tag": "ref_ent005_lr5e4",
        "lr": 5e-4,
        "label_smoothing": 0.10,
        "entropy_loss_weight": 0.05,
        "mlp_dropout": 0.30,
        "epochs": 60,
        "early_stopping_patience": 10,
        "maps_from_legacy": ["ref_base_ent005"],
    },
    "ref_noent_lr5e4": {
        "family_tag": "ref_noent_lr5e4",
        "lr": 5e-4,
        "label_smoothing": 0.10,
        "entropy_loss_weight": 0.00,
        "mlp_dropout": 0.30,
        "epochs": 60,
        "early_stopping_patience": 10,
        "maps_from_legacy": ["ref_base_lr2e4", "confman_baseline_openconf"],
    },
    "ref_ls000_noent_lr5e4": {
        "family_tag": "ref_ls000_noent_lr5e4",
        "lr": 5e-4,
        "label_smoothing": 0.00,
        "entropy_loss_weight": 0.00,
        "mlp_dropout": 0.30,
        "epochs": 60,
        "early_stopping_patience": 10,
        "maps_from_legacy": ["legacy no-LS / no-entropy ablations"],
    },
    "legacy_bridge_ref_pms_drop040": {
        "family_tag": "legacy_bridge_ref_pms_drop040",
        "lr": 1e-4,
        "weight_decay": 1e-4,
        "lambda_center": 0.1,
        "label_smoothing": 0.05,
        "entropy_loss_weight": 0.05,
        "mlp_dropout": 0.40,
        "grad_clip_norm": 1.0,
        "scheduler_name": "plateau",
        "epochs": 60,
        "early_stopping_patience": 10,
        "maps_from_legacy": ["ref_pms_drop040"],
        "status": "optional bridge only",
    },
}


RUN_GROUPS: Dict[str, Dict[str, Any]] = {
    "smoke_functional": {
        "source_profile": "ota_core_high_run01",
        "paper_sets": ["OG"],
        "families": ["smoke_ent005_lr2e4"],
        "unknown_mode": "all_in_set",
        "seeds": [0],
        "output_root": "results_pa_final_smoke",
        "priority": "tier0",
        "status": "mandatory",
    },
    "legacy_digital_recovered": {
        "source_profile": "digital_noisy_legacy",
        "paper_sets": ["OG"],
        "families": [],
        "unknown_mode": "inventory_only",
        "seeds": [],
        "output_root": "docs/experiments",
        "priority": "reference",
        "status": "no_rerun",
    },
    "legacy_digital_bridge_rerun": {
        "source_profile": "digital_noisy_legacy",
        "paper_sets": ["OG"],
        "families": ["ref_ent005_lr5e4", "ref_ent005_lr2e4", "ref_noent_lr5e4"],
        "unknown_mode": "all_in_set",
        "seeds": [0],
        "output_root": "results_pa_bridge_digital",
        "priority": "optional",
        "status": "optional",
    },
    "ota_primary_matrix": {
        "source_profile": "ota_core_high_run01",
        "paper_sets": ["OG", "DISTINCT"],
        "families": [
            "ref_ent005_lr2e4",
            "ref_ent005_lr5e4",
            "ref_noent_lr5e4",
            "ref_ls000_noent_lr5e4",
        ],
        "unknown_mode": "all_in_set",
        "seeds": [0],
        "output_root": "results_pa_ota_primary",
        "priority": "tier1",
        "status": "mandatory",
    },
    "ota_master_context": {
        "source_profile": "ota_core_high_run01",
        "paper_sets": ["MASTER"],
        "families": ["ref_ent005_lr2e4", "ref_ent005_lr5e4", "ref_noent_lr5e4"],
        "unknown_mode": "all_in_set",
        "seeds": [0],
        "output_root": "results_pa_ota_master",
        "priority": "tier1",
        "status": "mandatory",
    },
    "ota_protocol_ablation": {
        "source_profile": "ota_core_high_run01",
        "paper_sets": ["OG", "DISTINCT", "MASTER"],
        "families": ["top_selected"],
        "protocols": [["wifi"], ["bluetooth"], ["zigbee"]],
        "unknown_mode": "all_in_set",
        "seeds": [0],
        "output_root": "results_pa_ota_protocol_ablation",
        "priority": "tier2",
        "status": "mandatory_after_primary",
    },
}


OSR_EVAL_MATRIX: Dict[str, Any] = {
    "score_families": ["varmax", "energy", "pmax", "p1p2", "entropy", "logit_variance"],
    "calibration_modes": ["oracle", "surrogate_deployable"],
    "output_root": "results_pa_osr_eval",
}


def get_family_config(name: str) -> Dict[str, Any]:
    if name not in FAMILY_CONFIGS:
        raise KeyError(f"Unknown family config: {name}. Valid={sorted(FAMILY_CONFIGS)}")
    return deepcopy(FAMILY_CONFIGS[name])


def get_source_profile(name: str) -> Dict[str, Any]:
    if name not in SOURCE_PROFILES:
        raise KeyError(f"Unknown source profile: {name}. Valid={sorted(SOURCE_PROFILES)}")
    return deepcopy(SOURCE_PROFILES[name])


def get_run_group(name: str) -> Dict[str, Any]:
    if name not in RUN_GROUPS:
        raise KeyError(f"Unknown run group: {name}. Valid={sorted(RUN_GROUPS)}")
    return deepcopy(RUN_GROUPS[name])


def list_run_groups() -> List[str]:
    return sorted(RUN_GROUPS)


def catalog_training_config_overrides(
    *,
    source_profile_name: str,
    family_name: str,
) -> Dict[str, Any]:
    """Overrides applied after base_training_config().

    This lets the old base config remain the single source for common defaults
    while the catalog cleanly changes source-specific or family-specific knobs.
    """
    source = get_source_profile(source_profile_name)
    family = get_family_config(family_name)

    out: Dict[str, Any] = {}

    for k in ["source_type", "source_name", "dataset_tag", "noise_tag", "cache_len"]:
        if k in source:
            out[k] = source[k]

    if "cache_root" in source:
        out["cache_root"] = str(Path(source["cache_root"]).expanduser())

    # Family-specific optional overrides beyond the original FAMILY_GRIDS schema.
    for k in [
        "weight_decay",
        "lambda_center",
        "grad_clip_norm",
        "scheduler_name",
    ]:
        if k in family:
            out[k] = family[k]

    out["source_profile"] = source_profile_name
    out["catalog_family_name"] = family_name

    return out


def grid_name_to_family_names(grid: str) -> List[str]:
    """Compatibility helper for older --grid interface."""
    if grid == "smoke":
        return ["smoke_ent005_lr2e4"]
    if grid == "baseline":
        return ["ref_ent005_lr2e4"]
    if grid == "search":
        return [
            "ref_ent005_lr2e4",
            "ref_ent005_lr5e4",
            "ref_noent_lr5e4",
            "ref_ls000_noent_lr5e4",
        ]

    # Fall back to existing constants if a future grid exists only there.
    if grid in FAMILY_GRIDS:
        return [x["family_tag"] for x in FAMILY_GRIDS[grid]]

    raise KeyError(f"Unknown grid={grid}")
