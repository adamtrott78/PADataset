from pathlib import Path

WORKFLOW = Path(".github/workflows/lambda-ci-scientific-2.yml")


def _text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_trusted_lane_b_retains_existing_route_and_adds_only_bounded_l2o_op():
    text = _text()
    required = [
        "startsWith(github.event.comment.body, '/lambda-scientific-2 ')",
        "runs-on: lambda-padataset-scientific-single-gpu-2",
        "GPU-cfed3394-a935-63aa-9325-c4cae7b568b6",
        "actions: read",
        "contents: read",
        "pull-requests: read",
        "train_backbone:manifests/configs/",
        "stage03_archc:manifests/configs/",
        "l2o_directional_eval:manifests/configs/l2o_directional_eval_v1/",
        'op not in {"train_backbone", "stage03_archc", "l2o_directional_eval"}',
    ]
    for marker in required:
        assert marker in text, marker

    forbidden = [
        "--mix-true-open",
        "contents: write",
        "actions: write",
        "pull-requests: write",
        "/lambda-l2o-eval-2 ",
    ]
    for marker in forbidden:
        assert marker not in text, marker


def test_l2o_path_validates_provenance_before_download_and_eval():
    text = _text()
    pre = text.index("experiments/l2o_eval_request_contract.py")
    metadata = text.index("actions/artifacts/$artifact_id")
    transport = text.index("experiments/l2o_artifact_transport_contract.py")
    archive = text.index('archive_download_url')
    rehydrate = text.index("experiments/l2o_artifact_rehydrate.py")
    evaluator = text.index("experiments/pa_eval_dqn_guard_surrogate_open.py")
    record = text.index("experiments/l2o_eval_result_record.py")
    assert pre < metadata < transport < archive < rehydrate < evaluator < record


def test_l2o_path_uses_frozen_policy_and_trusted_read_only_data():
    text = _text()
    required = [
        'req.get("policy_id") != "l2o_dqnguard_track_a_frozen_v1"',
        'req.get("checkpoint") != "best_model"',
        'req.get("target_labels_used_for_tuning") is not False',
        "manifests/l2o_canonical_backbone_matrix_v1.json",
        "manifests/l2o_directional_eval_policy_v1.json",
        '--data-root "$TRUSTED_DATA"',
    ]
    for marker in required:
        assert marker in text, marker
