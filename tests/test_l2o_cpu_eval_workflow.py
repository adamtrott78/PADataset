from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github/workflows/lambda-ci-l2o-directional-eval-cpu.yml"


def test_cpu_osr_workflow_is_narrow_and_cpu_only():
    text = WF.read_text(encoding="utf-8")
    required = [
        "startsWith(github.event.comment.body, '/lambda-l2o-eval-cpu ')",
        "runs-on: lambda-padataset-cpu-public",
        "actions: read",
        "contents: read",
        "pull-requests: read",
        "issues: write",
        "l2o_directional_eval_v1",
        "l2o_eval_request_contract.py",
        "l2o_artifact_transport_contract.py",
        "l2o_artifact_rehydrate.py",
        "pa_eval_dqn_guard_surrogate_open.py",
        "l2o_eval_result_record.py",
        'assert args[i+1] == "cuda"',
        'args[i+1] = "cpu"',
        "CPU evaluator runner unexpectedly has NVIDIA access",
        "equivalence_status",
        "PENDING_SAME_BACKBONE_CUDA_REFERENCE",
        "MTH602_CPU_OSR_RESULT_V1",
        "MTH602_CPU_OSR_STARTED_V1",
    ]
    for marker in required:
        assert marker in text


def test_cpu_osr_workflow_preserves_frozen_policy_except_device():
    text = WF.read_text(encoding="utf-8")
    assert 'policy_path="manifests/l2o_directional_eval_policy_v1.json"' in text
    assert "--mix-true-open" not in text
    assert "target_labels_used_for_tuning" in text
    assert "executed_evaluator_device" in text
    assert '"cpu"' in text
    assert "nvidia-smi -L" in text


def test_cpu_osr_workflow_has_no_training_operation():
    text = WF.read_text(encoding="utf-8")
    assert "pa_train_one.py" not in text
    assert "train_backbone:" not in text
