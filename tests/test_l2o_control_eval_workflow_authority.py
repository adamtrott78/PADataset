from pathlib import Path
import subprocess

WORKFLOWS = [
    Path(".github/workflows/lambda-ci-scientific.yml"),
    Path(".github/workflows/lambda-ci-scientific-2.yml"),
]


def _global_permissions_text(text: str) -> str:
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line == "permissions:")
    end = next(i for i in range(start + 1, len(lines)) if lines[i] == "jobs:")
    return "\n".join(lines[start:end])


def _primary_job_text(text: str, job_key: str) -> str:
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line == f"  {job_key}:")
    end = len(lines)
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if line.startswith("  ") and not line.startswith("    ") and line.endswith(":"):
            end = i
            break
    return "\n".join(lines[start:end])


def _execute_script(text: str) -> str:
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == "- name: Execute bounded scientific request")
    run_line = next(i for i in range(start, len(lines)) if lines[i].strip() == "run: |")
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
    return "\n".join(body) + "\n"


def test_both_scientific_lanes_accept_only_bounded_control_request_shape():
    for path in WORKFLOWS:
        text = path.read_text(encoding="utf-8")
        required = [
            "l2o_control_eval:manifests/configs/l2o_control_eval_v1/",
            'op == "l2o_control_eval"',
            '"padataset.l2o-control-eval-request.v1"',
            '"READY_FOR_BOUNDED_CONTROL_EVALUATOR"',
            '"l2o_repaired_controls_frozen_v1"',
            '"manifests/l2o_control_matrix_plan_v1.json"',
            '"manifests/l2o_control_eval_policy_v1.json"',
            '"dqn_ids_style_softmax3_external_surrogate_cap625_v1"',
            '"varmax_surrogate_all_smoke_matched_l2o_v1"',
            'req.get("target_labels_used_for_tuning") is not False',
            'req.get("target_test_consumed_before_final_eval") is not False',
        ]
        for marker in required:
            assert marker in text, (path, marker)


def test_control_path_validates_before_download_and_evaluation():
    for path in WORKFLOWS:
        text = path.read_text(encoding="utf-8")
        pre = text.index("experiments/l2o_control_request_contract.py")
        meta = text.index("actions/artifacts/$artifact_id", pre)
        transport = text.index("experiments/l2o_control_artifact_transport_contract.py", pre)
        archive = text.index("archive_download_url", pre)
        rehydrate = text.index("experiments/l2o_artifact_rehydrate.py", pre)
        evaluator = text.index("experiments/pa_eval_l2o_controls_v1.py", pre)
        record = text.index("experiments/l2o_control_eval_result_record.py", pre)
        assert pre < meta < transport < archive < rehydrate < evaluator < record


def test_control_path_uses_read_only_scientific_permissions_and_trusted_data():
    for path in WORKFLOWS:
        text = path.read_text(encoding="utf-8")
        job_key = "padataset-scientific-2" if path.name.endswith("-2.yml") else "padataset-scientific"
        primary = _primary_job_text(text, job_key)
        global_permissions = _global_permissions_text(text)
        assert "actions: read" in global_permissions
        assert "contents: read" in global_permissions
        assert "pull-requests: read" in global_permissions
        assert "contents: write" not in global_permissions
        assert "actions: write" not in global_permissions
        assert "pull-requests: write" not in global_permissions
        assert "permissions:" not in primary
        control = text[text.index('elif [[ "$OPERATION" == "l2o_control_eval" ]]'):]
        assert '--data-root "$TRUSTED_DATA"' in control


def test_execute_blocks_remain_valid_bash():
    for path in WORKFLOWS:
        script = _execute_script(path.read_text(encoding="utf-8"))
        proc = subprocess.run(["bash", "-n"], input=script, text=True, capture_output=True, check=False)
        assert proc.returncode == 0, (path, proc.stderr)
