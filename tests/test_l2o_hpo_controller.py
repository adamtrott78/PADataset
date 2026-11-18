from __future__ import annotations

import copy

import pytest

from experiments.l2o_hpo_generate import (
    HPO_FIELDS,
    build_trial_config,
    candidate_params,
    promote_trial_config,
    validate_base_config,
)
from experiments.l2o_hpo_ledger import (
    freeze_pair,
    mark_target_open_evaluated,
    new_ledger,
    register_trial,
    transition_trial,
)
from experiments.l2o_hpo_rank import rank_results, validate_known_only_record


def _space():
    return {
        "search_space": {
            "lr": {"type": "log_float", "low": 5e-5, "high": 1e-3},
            "weight_decay": {"type": "categorical", "values": [0, 1e-4]},
            "lambda_center": {"type": "categorical", "values": [0, 0.1]},
            "label_smoothing": {"type": "categorical", "values": [0, 0.1]},
            "entropy_loss_weight": {"type": "categorical", "values": [0, 0.05]},
            "mlp_dropout": {"type": "categorical", "values": [0.2, 0.3]},
            "grad_clip_norm": {"type": "categorical", "values": [None, 1]},
            "scheduler_name": {"type": "categorical", "values": ["cosine", "plateau"]},
            "batch_size": {"type": "categorical", "values": [8, 16]},
        },
        "invariants": {
            "cache_len": 16384,
            "split_mode": "open_pa",
            "open_val_frac": 0,
            "early_stopping_mode": "known_only",
            "quarantine_target_until_test": True,
            "deterministic_training": True,
            "deterministic_profile": "strict_tf32",
        },
        "resource_ladder": [
            {"stage": "screen", "max_trials": 96, "epochs": 8, "promote_top": 24},
            {"stage": "refine", "max_trials": 24, "epochs": 24, "promote_top": 6},
            {"stage": "finalist", "max_trials": 6, "epochs": 60, "promote_top": 1},
        ],
    }


def _base(target="PA2", surrogate="PA3"):
    known = [pa for pa in ["PA1", "PA2", "PA3", "PA4", "PA8"] if pa not in {target, surrogate}]
    return {
        "run_name": "baseline",
        "target_unknown_pa": target,
        "surrogate_open_pa": surrogate,
        "known_pas_l2o": known,
        "cache_len": 16384,
        "split_mode": "open_pa",
        "open_val_frac": 0,
        "early_stopping_mode": "known_only",
        "quarantine_target_until_test": True,
        "deterministic_training": True,
        "deterministic_profile": "strict_tf32",
        "force_rebuild_cache": False,
        "skip_cache_build": True,
        "use_timestamped_run_dir": False,
        "overwrite_existing_run": False,
        "epochs": 60,
        "save_root": "baseline",
    }


def _record(trial_id, macro, min_class, stage="screen", pair="PA2-PA3"):
    return {
        "trial_id": trial_id,
        "canonical_pair": pair,
        "stage": stage,
        "config_path": f"manifests/{trial_id}.json",
        "status": "COMPLETE",
        "best_epoch": 3,
        "val_macro_f1": macro,
        "val_min_class_f1": min_class,
        "val_per_class_f1": {"PA1": min_class, "PA4": max(min_class, macro), "PA8": max(min_class, macro)},
    }


def test_candidate_generation_is_deterministic_and_shared_across_pairs():
    space = _space()
    p1 = candidate_params(space, trial_index=7, seed=6022026)
    p2 = candidate_params(space, trial_index=7, seed=6022026)
    assert p1 == p2
    a = build_trial_config(_base("PA2", "PA3"), space, p1, "screen", 7, 6022026)
    b = build_trial_config(_base("PA2", "PA8"), space, p1, "screen", 7, 6022026)
    assert a["hpo_trial"]["params"] == b["hpo_trial"]["params"]
    assert a["epochs"] == b["epochs"] == 8
    assert a["target_unknown_pa"] == "PA2"
    assert b["surrogate_open_pa"] == "PA8"
    for field in HPO_FIELDS:
        assert a[field] == p1[field]


def test_base_config_fail_closed_on_target_quarantine_drift():
    base = _base()
    base["open_val_frac"] = 0.15
    with pytest.raises(ValueError, match="open_val_frac"):
        validate_base_config(base, _space())


def test_promotion_preserves_params_and_topology():
    space = _space()
    params = candidate_params(space, 4, 6022026)
    screen = build_trial_config(_base(), space, params, "screen", 4, 6022026)
    refine = promote_trial_config(screen, space, "refine")
    finalist = promote_trial_config(refine, space, "finalist")
    assert refine["epochs"] == 24
    assert finalist["epochs"] == 60
    assert finalist["hpo_trial"]["params"] == params
    assert finalist["known_pas_l2o"] == screen["known_pas_l2o"]
    assert finalist["target_unknown_pa"] == screen["target_unknown_pa"]
    assert finalist["surrogate_open_pa"] == screen["surrogate_open_pa"]


@pytest.mark.parametrize("forbidden", ["unknown_f1", "osr_macro_f1", "unknown_auroc", "test_known_macro_f1", "target_recall"])
def test_ranker_rejects_target_or_test_metrics(forbidden):
    record = _record("t0", 0.96, 0.91)
    record[forbidden] = 0.99
    with pytest.raises(ValueError, match="forbidden"):
        validate_known_only_record(record, expected_stage="screen")


def test_ranker_prefers_feasible_min_class_before_higher_macro():
    records = [
        _record("high_macro_bad_class", 0.99, 0.89),
        _record("feasible", 0.96, 0.91),
        _record("second_feasible", 0.955, 0.92),
    ]
    ranked = rank_results(records, stage="screen", promote_top=2)
    pair = ranked["pairs"][0]
    assert pair["winner_trial_id"] == "feasible"
    assert pair["promotion_trial_ids"] == ["feasible", "second_feasible"]
    assert pair["gate_pass"] is True
    assert pair["frozen"] is False


def test_only_terminal_finalist_can_freeze_and_target_eval_locks_pair():
    ledger = new_ledger(["PA2-PA3"], "policy")
    ledger = register_trial(ledger, "PA2-PA3", "PA2-PA3__t001", "a" * 64, "finalist", "cfg1.json")
    for state in ["REQUESTED", "QUEUED", "RUNNING", "TERMINAL"]:
        ledger = transition_trial(ledger, "PA2-PA3__t001", state)
    ledger = freeze_pair(ledger, "PA2-PA3", "PA2-PA3__t001")
    ledger = mark_target_open_evaluated(ledger, "PA2-PA3", "PA2-PA3__t001")
    with pytest.raises(ValueError, match="frozen"):
        register_trial(ledger, "PA2-PA3", "PA2-PA3__t002", "b" * 64, "screen", "cfg2.json")
    with pytest.raises(ValueError, match="cannot alter freeze"):
        freeze_pair(ledger, "PA2-PA3", "PA2-PA3__t001")


def test_finalist_gate_freezes_only_when_both_thresholds_pass():
    records = [
        _record("pass", 0.951, 0.905, stage="finalist"),
        _record("macro_only", 0.99, 0.89, stage="finalist"),
    ]
    ranked = rank_results(records, stage="finalist", promote_top=1)
    pair = ranked["pairs"][0]
    assert pair["winner_trial_id"] == "pass"
    assert pair["gate_pass"] is True
    assert pair["frozen"] is True
