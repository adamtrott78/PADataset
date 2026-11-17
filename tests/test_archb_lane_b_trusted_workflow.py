from pathlib import Path


WORKFLOW = Path(".github/workflows/lambda-ci-scientific-2.yml")


def test_archb_gpu2_workflow_is_narrow_and_provenance_bound():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "runs-on: lambda-padataset-scientific-single-gpu-2" in text
    assert 'GPU-cfed3394-a935-63aa-9325-c4cae7b568b6' in text
    assert 'archb_cross_surrogate:manifests/configs/archb_cross_surrogate_v1/' in text
    assert '"archb_cross_surrogate"' in text
    assert 'padataset.archb-cross-surrogate-eval-request.v1' in text
    assert 'mth602_archb_b0_frozen_v1' in text
    assert 'mth602_archb_b1_frozen_v1' in text
    assert 'mth602_archb_b2_frozen_v1' in text
    assert 'mth602_archb_b3_frozen_v1' in text
    assert '"B0": ("mth602_archb_b0_frozen_v1", "softmax3", False)' in text
    assert '"B1": ("mth602_archb_b1_frozen_v1", "expanded5", False)' in text
    assert '"B2": ("mth602_archb_b2_frozen_v1", "softmax3", True)' in text
    assert '"B3": ("mth602_archb_b3_frozen_v1", "softmax3", True)' in text
    assert 'req.get("target_pa") != "PA2"' in text
    assert 'req.get("predeclared_stage_transition") is not True' in text
    assert 'req.get("b0_target_metrics_used_for_b1_parameters") is not False' in text
    assert 'req.get("target_metrics_used_for_state_mode_selection") is not False' in text
    assert '14354747328' in text
    assert '14361967189' in text
    assert '14369751106' in text
    assert 'req.get("target_metrics_used_for_b3_trigger_or_tuning") is not False' in text
    assert '"absolute_median_separation"' in text
    assert 'search.get("guard_scales") != [0.5, 1.0, 2.0]' in text
    assert 'own_pseudo_surrogate_only' in text
    assert 'float(req.get("known_budget", -1)) != 0.05' in text
    assert 'int(req.get("partition_seed", -1)) != 1701' in text
    assert 'int(req.get("dqn_episodes", -1)) != 30' in text
    assert 'req.get("target_labels_used_for_fitting") is not False' in text
    assert 'req.get("target_labels_used_for_thresholding") is not False' in text
    assert 'req.get("target_labels_used_for_candidate_selection") is not False' in text
    assert 'req.get("target_first_consumed_after_winner_frozen") is not True' in text
    assert '14180249360' in text
    assert 'sha256:f7de2637df85487b21903a448630815fc63c1247253b98ffc754b46586b9b39b' in text
    assert '43751609944' in text
    assert 'befe383fd67c8bca8d8ce370344b33c7e13cd52f' in text


def test_archb_gpu2_workflow_uses_hardened_contract_and_final_result_checks():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "experiments/archb_eval_request_contract.py" in text
    assert "experiments/archb_artifact_transport_contract.py" in text
    assert "experiments/archb_artifact_rehydrate.py" in text
    assert "experiments/pa_eval_cross_surrogate_dqnguard.py" in text
    assert 'd["schema"] == "padataset.cross-surrogate-dqnguard-b.result.v1"' in text
    assert 'd["candidate_selection"]["own_surrogate_diagonal_excluded"] is True' in text
    assert 'd["score"]["state_mode"] == req["state_mode"]' in text
    assert 'req["stage"] in {"B0", "B1", "B2", "B3"}' in text
    assert 'd["score"]["tune_band_weights"] is True' in text
    assert '"bounded_b3_search"' in text
    assert 'd["score"]["class_conditional_bands"] is True' in text
    assert 'd["threshold"]["source"] == "known_only"' in text
    assert 'p["target_first_consumed_after_winner_frozen"] is True' in text
    assert 'operation=archb_cross_surrogate' not in text  # no hard-coded forged receipt
