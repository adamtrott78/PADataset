from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]

def test_launcher_bash_syntax():
    subprocess.run(["bash","-n",str(ROOT/"scripts/mth602_robustness_tmux.sh")],check=True)

def test_launcher_uses_systemd_and_fails_closed():
    s=(ROOT/"scripts/mth602_robustness_tmux.sh").read_text()
    assert "sudo -v" in s
    assert "systemd-run" in s
    assert "Restart=on-failure" in s
    assert "PIPELINE_WATCHER_START=FAIL" in s
    assert "PIPELINE_WATCHER_START=PASS" in s
    assert "journalctl" in s
    assert "sudo -n" not in s
