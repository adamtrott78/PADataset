from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]

def test_dashboard_ctrlc_detaches_instead_of_exiting():
    s=(ROOT/"scripts/mth602_robustness_local_dashboard.py").read_text()
    assert "import argparse, glob, json, os, pwd, re, shlex, shutil, signal," in s
    assert "def detach_current_client" in s
    assert 'subprocess.run(["tmux","detach-client"]' in s
    assert "signal.signal(signal.SIGINT,detach_current_client)" in s
    assert "Ctrl+C detaches" in s
    assert "except KeyboardInterrupt" not in s

def test_dashboard_python_syntax():
    subprocess.run(["python3","-m","py_compile",str(ROOT/"scripts/mth602_robustness_local_dashboard.py")],check=True)
