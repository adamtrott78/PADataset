from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WF=ROOT/".github/workflows/lambda-ci-l2o-directional-eval-cpu.yml"

def test_cpu_workflow_yaml_parses():
    import yaml
    data=yaml.safe_load(WF.read_text())
    assert isinstance(data,dict)
    assert "jobs" in data
    assert "l2o-directional-eval-cpu" in data["jobs"]
