from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_final_robustness_seed_grid_is_exact_and_predeclared():
    plan = json.loads((ROOT / "manifests/mth602_final_robustness_v1.json").read_text())
    assert plan["status"] == "PROPOSED_NOT_AUTHORIZED_FOR_SCIENCE"
    assert plan["seed_axes"]["partition_seeds"] == [0, 1, 2, 3, 4]
    assert plan["seed_axes"]["training_seeds"] == list(range(10))
    assert plan["seed_axes"]["factorial_backbones_per_pair"] == 50
    assert plan["seed_axes"]["canonical_pairs"] == 10
    assert plan["seed_axes"]["total_backbone_cells"] == 500
    assert plan["seed_axes"]["initial_seed0_matrix_counts_as"] == {
        "partition_seed": 0,
        "training_seed": 0,
        "when_exact_recipe_and_artifact_compatible": True,
    }


def test_backbone_seed_axes_are_independent_in_source_contract():
    src = (ROOT / "discriminate.py").read_text()
    prep = (ROOT / "prepData.py").read_text()

    assert 'partition_seed = int(cfg.get("partition_seed", legacy_seed))' in src
    assert 'training_seed = int(cfg.get("training_seed", legacy_seed))' in src
    assert "seed=partition_seed" in src
    assert "loader_seed=training_seed" in src
    assert "seed=training_seed" in src

    assert "loader_seed: Optional[int] = None" in prep
    assert "effective_loader_seed = setup.seed if loader_seed is None else int(loader_seed)" in prep
    assert "seed=effective_loader_seed, stream_id=11" in prep


def test_standard_dqnguard_keeps_fixed_dqn_seed_and_partition_bound_calibration():
    src = (ROOT / "experiments/pa_eval_dqn_guard_surrogate_open.py").read_text()
    plan = json.loads((ROOT / "manifests/mth602_final_robustness_v1.json").read_text())

    assert plan["dqn_policy"]["factorial_dqn_seed"] == 42
    assert plan["dqn_policy"]["separate_dqn_seed_sensitivity"] == "DEFERRED_NOT_PART_OF_5x10_FACTORIAL"
    assert "DQN_SEED = 42" in src
    assert "seed=DQN_SEED" in src
    assert 'partition_seed = int(payload.meta.get("partition_seed", legacy_seed) or 0)' in src
    assert "partition_seed + 101" in src
    assert "partition_seed + 202" in src
    assert '"dqn_seed": DQN_SEED' in src


def test_target_test_firewall_is_frozen_before_seed_results():
    plan = json.loads((ROOT / "manifests/mth602_final_robustness_v1.json").read_text())
    firewall = plan["firewall"]
    assert firewall == {
        "target_labels_used_for_tuning": False,
        "target_test_used_for_recipe_selection": False,
        "target_test_used_for_checkpoint_selection": False,
        "target_test_used_for_retry_selection": False,
        "target_test_used_for_seed_selection": False,
        "seed_values_selected_before_any_multi_seed_results": True,
    }
    assert plan["admission_gate"]["current"] == "BLOCKED_PENDING_EXPLICIT_REVIEW_ACCEPTANCE"
