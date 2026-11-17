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
    assert 'req.get("target_pa") != "PA2"' in text
    assert 'req.get("state_mode") != "softmax3"' in text
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
    assert 'd["threshold"]["source"] == "known_only"' in text
    assert 'p["target_first_consumed_after_winner_frozen"] is True' in text
    assert 'operation=archb_cross_surrogate' not in text  # no hard-coded forged receipt
