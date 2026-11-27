from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
S=ROOT/"scripts/mth602_recover_completed_final_artifacts.sh"

def test_recovery_is_exact_and_firewall_checked():
    s=S.read_text()
    assert s.count("recover_one 459") == 7
    assert "target_labels_used_for_tuning" in s
    assert "methods_frozen_before_target_test" in s
    assert "target_test_consumed_before_method_fit" in s
    assert "FINAL_RECOVERY=PASS attempted=7" in s

def test_script_syntax():
    subprocess.run(["bash","-n",str(S)],check=True)
