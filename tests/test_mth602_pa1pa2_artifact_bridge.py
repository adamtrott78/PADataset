from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WF=ROOT/".github/workflows/lambda-ci-cpu.yml"

def test_pa1pa2_bridge_is_exact_and_hosted():
    text=WF.read_text()
    required=[
        "pa1pa2-t007-artifact-bridge:",
        "runs-on: ubuntu-latest",
        "github.event.issue.number == 42",
        "761deab35e728fba99177ae3f09192caf512fbde",
        "14765881457",
        "7c439dc693c96777ec04ded9e76b69a7dc9b8d774cf4192bd502f880cda77f79",
        "45047242656",
        "mth602-pa1-pa2-t007-cpu-bridge-v1",
        "MTH602_PA1PA2_CPU_BRIDGE_V1",
    ]
    for marker in required:
        assert marker in text

def test_bridge_does_not_evaluate_or_train():
    text=WF.read_text()
    block=text.split("  pa1pa2-t007-artifact-bridge:",1)[1]
    assert "pa_train_one.py" not in block
    assert "pa_eval_dqn_guard_surrogate_open.py" not in block
