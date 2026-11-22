from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WF=ROOT/".github/workflows/lambda-ci-scientific.yml"

def test_bridge_is_on_active_scientific_workflow_and_hosted():
    text=WF.read_text()
    required=[
        "pa1pa2-t007-artifact-bridge:",
        "runs-on: ubuntu-latest",
        "github.event.issue.number == 42",
        "startsWith(github.event.comment.body, '/lambda-l2o-eval-cpu ')",
        "761deab35e728fba99177ae3f09192caf512fbde",
        "14765881457",
        "7c439dc693c96777ec04ded9e76b69a7dc9b8d774cf4192bd502f880cda77f79",
        "mth602-pa1-pa2-t007-cpu-bridge-v1",
        "MTH602_PA1PA2_CPU_BRIDGE_V2",
        "MTH602_PA1PA2_CPU_BRIDGE_STARTED_V1",
    ]
    for marker in required:
        assert marker in text

def test_bridge_never_uses_scientific_gpu_runner_or_evaluator():
    text=WF.read_text()
    block=text.split("  pa1pa2-t007-artifact-bridge:",1)[1]
    assert "lambda-padataset-scientific-single-gpu" not in block
    assert "pa_eval_dqn_guard_surrogate_open.py" not in block
    assert "pa_train_one.py" not in block
