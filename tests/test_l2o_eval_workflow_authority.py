from pathlib import Path

WORKFLOW = Path(".github/workflows/lambda-ci-l2o-directional-eval-2.yml")


def test_l2o_gpu2_workflow_is_narrow_and_fail_closed():
    text = WORKFLOW.read_text(encoding="utf-8")

    required = [
        "actions: read",
        "contents: read",
        "pull-requests: read",
        "runs-on: lambda-padataset-scientific-single-gpu-2",
        "GPU-cfed3394-a935-63aa-9325-c4cae7b568b6",
        "startsWith(github.event.comment.body, '/lambda-l2o-eval-2 ')",
        "manifests/configs/l2o_directional_eval_v1/",
        "experiments/l2o_eval_request_contract.py",
        "experiments/l2o_artifact_transport_contract.py",
        "experiments/l2o_artifact_rehydrate.py",
        "experiments/pa_eval_dqn_guard_surrogate_open.py",
        "experiments/l2o_eval_result_record.py",
        "actions/artifacts/$artifact_id",
        'archive_download_url',
        '--data-root "$TRUSTED_DATA"',
        '"operation":"l2o_directional_eval"',
        "padataset-l2o-eval-2-",
    ]
    for marker in required:
        assert marker in text, marker

    forbidden = [
        "--mix-true-open",
        "pa_train_one.py",
        "train_backbone:",
        "stage03_archc:",
        "contents: write",
        "actions: write",
        "pull-requests: write",
    ]
    for marker in forbidden:
        assert marker not in text, marker


def test_l2o_gpu2_workflow_validates_before_artifact_download():
    text = WORKFLOW.read_text(encoding="utf-8")
    pre = text.index("experiments/l2o_eval_request_contract.py")
    meta = text.index("actions/artifacts/$artifact_id")
    transport = text.index("experiments/l2o_artifact_transport_contract.py")
    archive = text.index('archive_download_url')
    rehydrate = text.index("experiments/l2o_artifact_rehydrate.py")
    evaluator = text.index("experiments/pa_eval_dqn_guard_surrogate_open.py")
    record = text.index("experiments/l2o_eval_result_record.py")

    assert pre < meta < transport < archive < rehydrate < evaluator < record


def test_l2o_gpu2_workflow_preserves_target_quarantine_policy_surface():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'd["target_labels_used_for_tuning"] is False' in text
    assert 'd["checkpoint"] == "best_model"' in text
    assert 'd["policy_id"] == "l2o_dqnguard_track_a_frozen_v1"' in text
    assert "l2o_directional_eval_policy_v1.json" in text
    assert "l2o_canonical_backbone_matrix_v1.json" in text
