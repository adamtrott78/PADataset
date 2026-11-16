#!/usr/bin/env python3
from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence, Tuple

PA_NAMES: Tuple[str, ...] = ("PA1", "PA2", "PA3", "PA4", "PA8")


@dataclass(frozen=True)
class DirectionalL2OContract:
    backbone_training_target: str
    backbone_training_surrogate: str
    canonical_excluded_pair: Tuple[str, str]
    evaluation_target: str
    evaluation_surrogate: str
    known_pas: Tuple[str, ...]
    directional_reuse: bool
    target_config: Dict[str, Any]
    surrogate_config: Dict[str, Any]


def _require_pa(name: str, field: str) -> str:
    value = str(name)
    if value not in PA_NAMES:
        raise ValueError(f"{field} must be one of {PA_NAMES}, got {value!r}")
    return value


def _single_unknown(cfg: Dict[str, Any]) -> str:
    unknown = list(cfg.get("unknown_pas", []))
    if len(unknown) != 1:
        raise ValueError(f"L2O backbone must contain exactly one unknown_pas entry, got {unknown!r}")
    return _require_pa(unknown[0], "unknown_pas[0]")


def resolve_directional_l2o_contract(
    cfg: Dict[str, Any],
    *,
    evaluation_target: str | None,
    evaluation_surrogate: str,
    model_class_names: Sequence[str] | None = None,
) -> DirectionalL2OContract:
    """
    Resolve one directional evaluator cell from a trained L2O backbone.

    A backbone is identified by the unordered excluded pair {target, surrogate}.
    Reversing the evaluator direction is allowed only when that unordered pair is
    unchanged and the three known classes exactly match the checkpoint outputs.
    """
    if cfg.get("split_mode") != "open_pa":
        raise ValueError("directional L2O reuse requires split_mode='open_pa'")

    training_target = _require_pa(
        cfg.get("target_unknown_pa", _single_unknown(cfg)),
        "target_unknown_pa",
    )
    if training_target != _single_unknown(cfg):
        raise ValueError("target_unknown_pa must match the single unknown_pas entry")

    training_surrogate_raw = cfg.get("surrogate_open_pa")
    if training_surrogate_raw is None:
        raise ValueError("surrogate_open_pa is required for provenance-safe directional reuse")
    training_surrogate = _require_pa(training_surrogate_raw, "surrogate_open_pa")
    if training_target == training_surrogate:
        raise ValueError("training target and surrogate must be distinct")

    known = tuple(str(x) for x in cfg.get("known_pas_l2o", []))
    if len(known) != 3 or len(set(known)) != 3:
        raise ValueError(f"known_pas_l2o must contain exactly three distinct PAs, got {known!r}")
    for pa in known:
        _require_pa(pa, "known_pas_l2o")
    if training_target in known or training_surrogate in known:
        raise ValueError("known_pas_l2o must exclude both training target and surrogate")
    if set(known) | {training_target, training_surrogate} != set(PA_NAMES):
        raise ValueError("known_pas_l2o plus target/surrogate must cover the five active PAs exactly")

    expected_pas = list(known) + [training_target]
    if list(cfg.get("pas", [])) != expected_pas:
        raise ValueError(
            "backbone pas ordering/provenance drift: "
            f"expected {expected_pas!r}, got {cfg.get('pas')!r}"
        )

    if model_class_names is not None and list(model_class_names) != list(known):
        raise ValueError(
            "checkpoint class_names must exactly match known_pas_l2o ordering; "
            f"checkpoint={list(model_class_names)!r}, known={list(known)!r}"
        )

    eval_target = _require_pa(
        training_target if evaluation_target is None else evaluation_target,
        "evaluation_target",
    )
    eval_surrogate = _require_pa(evaluation_surrogate, "evaluation_surrogate")
    if eval_target == eval_surrogate:
        raise ValueError("evaluation target and surrogate must be distinct")

    canonical = tuple(sorted((training_target, training_surrogate)))
    requested = tuple(sorted((eval_target, eval_surrogate)))
    if requested != canonical:
        raise ValueError(
            "requested directional cell does not match the backbone's excluded pair: "
            f"backbone={canonical!r}, requested={requested!r}"
        )

    target_cfg = copy.deepcopy(cfg)
    target_cfg["unknown_pas"] = [eval_target]
    target_cfg["pas"] = list(known) + [eval_target]
    target_cfg["target_unknown_pa"] = eval_target
    target_cfg["surrogate_open_pa"] = eval_surrogate
    target_cfg["known_pas_l2o"] = list(known)

    surrogate_cfg = copy.deepcopy(cfg)
    surrogate_cfg["unknown_pas"] = [eval_surrogate]
    surrogate_cfg["pas"] = list(known) + [eval_surrogate]
    surrogate_cfg["target_unknown_pa"] = eval_target
    surrogate_cfg["surrogate_open_pa"] = eval_surrogate
    surrogate_cfg["known_pas_l2o"] = list(known)

    return DirectionalL2OContract(
        backbone_training_target=training_target,
        backbone_training_surrogate=training_surrogate,
        canonical_excluded_pair=canonical,
        evaluation_target=eval_target,
        evaluation_surrogate=eval_surrogate,
        known_pas=known,
        directional_reuse=(
            eval_target != training_target or eval_surrogate != training_surrogate
        ),
        target_config=target_cfg,
        surrogate_config=surrogate_cfg,
    )
