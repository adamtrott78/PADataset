from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/mth602_robustness_local_pipeline.py"

def test_watcher_marks_spooled_tree_user_readable():
    s=SCRIPT.read_text()
    assert "def make_tree_user_readable(path):" in s
    assert "p.chmod(mode | 0o055)" in s
    assert "p.chmod(mode | 0o044)" in s
    assert "make_tree_user_readable(dst)" in s

def test_pipeline_python_syntax():
    subprocess.run(["python3","-m","py_compile",str(SCRIPT)],check=True)
