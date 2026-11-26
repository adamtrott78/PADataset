from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]

def test_recovery_script_bash_syntax():
    subprocess.run(["bash","-n",str(ROOT/"scripts/mth602_recover_wave_a_artifacts.sh")],check=True)

def test_recovery_is_bounded_exact_and_firewall_checked():
    s=(ROOT/"scripts/mth602_recover_wave_a_artifacts.sh").read_text()
    assert "45860162828" in s
    assert "45860165260" in s
    assert "padataset-scientific-45860162828" in s
    assert "padataset-scientific-2-45860165260" in s
    assert "methods_frozen_before_target_test" in s
    assert "target_test_consumed_before_method_fit" in s
    assert "target_labels_used_for_tuning" in s
    assert "RECOVERY=PASS spooled=2" in s
    assert s.count("gh run download") == 1
