from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_watcher_uses_one_foreground_authenticated_sudo_launch_not_tmux_sudo():
    s=(ROOT/'scripts/mth602_robustness_tmux.sh').read_text()
    assert 'sudo -v' in s
    assert 'sudo -E bash -c' in s
    assert 'nohup python3' in s
    assert 'pipeline-watcher.pid' in s
    assert 'sudo -n' not in s
    assert 'mth602-robustness-pipeline' not in s.split('UI_SESSION=')[0]

def test_dashboard_runs_unprivileged_and_watcher_health_uses_pid_plus_heartbeat():
    s=(ROOT/'scripts/mth602_robustness_tmux.sh').read_text()
    assert 'os.kill(pid,0)' in s
    assert 'age <= 5.0' in s
    assert 'exec python3' in s
    assert 'exec sudo' not in s
