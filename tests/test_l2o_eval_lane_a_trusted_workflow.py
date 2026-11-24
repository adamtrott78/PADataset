from pathlib import Path
import subprocess

WORKFLOW = Path(".github/workflows/lambda-ci-scientific.yml")


def _text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def _primary_job_text() -> str:
    lines = _text().splitlines()
    start = next(i for i, line in enumerate(lines) if line == "  padataset-scientific:")
    end = len(lines)
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if line.startswith("  ") and not line.startswith("    ") and line.endswith(":"):
            end = i
            break
    return "\n".join(lines[start:end])


def test_trusted_lane_a_retains_existing_route_and_adds_only_bounded_l2o_op():
    text = _text()
    required = [
        "startsWith(github.event.comment.body, '/lambda-scientific ')",
        "runs-on: lambda-padataset-scientific-single-gpu",
        "GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea",
        "actions: read",
        "contents: read",
        "pull-requests: read",
        "train_backbone:manifests/configs/",
        "stage03_archc:manifests/configs/",
        "l2o_directional_eval:manifests/configs/l2o_directional_eval_v1/",
        'op not in {"train_backbone", "stage03_archc", "l2o_directional_eval", "l2o_control_eval"}',
        "l2o_control_eval:manifests/configs/l2o_control_eval_v1/",
        "experiments/l2o_control_request_contract.py",
        "experiments/l2o_control_artifact_transport_contract.py",
        "experiments/pa_eval_l2o_controls_v1.py",
        "experiments/l2o_control_eval_result_record.py",
    ]
    for marker in required:
        assert marker in text, marker

    forbidden = [
        "--mix-true-open",
        "archb_cross_surrogate:manifests/configs/",
        'op not in {"train_backbone", "stage03_archc", "l2o_directional_eval", "archb_cross_surrogate"}',
        "contents: write",
        "actions: write",
        "pull-requests: write",
        "/lambda-l2o-eval ",
    ]
    primary = _primary_job_text()
    for marker in forbidden:
        if marker in {"contents: write", "actions: write", "pull-requests: write"}:
            assert marker not in primary, marker
        else:
            assert marker not in text, marker


def test_l2o_path_validates_provenance_before_download_and_eval():
    text = _text()
    pre = text.index("experiments/l2o_eval_request_contract.py")
    metadata = text.index("actions/artifacts/$artifact_id")
    transport = text.index("experiments/l2o_artifact_transport_contract.py")
    archive = text.index("archive_download_url")
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


def test_execute_block_is_valid_bash_syntax():
    lines = _text().splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == "- name: Execute bounded scientific request":
            start = i
            break
    assert start is not None

    run_line = None
    for i in range(start, len(lines)):
        if lines[i].strip() == "run: |":
            run_line = i
            break
    assert run_line is not None

    body = []
    for line in lines[run_line + 1:]:
        if line.startswith("      - name: "):
            break
        if line.startswith("          "):
            body.append(line[10:])
        elif line == "":
            body.append("")
        else:
            raise AssertionError(f"unexpected workflow indentation: {line!r}")

    script = "\n".join(body) + "\n"
    proc = subprocess.run(
        ["bash", "-n"],
        input=script,
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
