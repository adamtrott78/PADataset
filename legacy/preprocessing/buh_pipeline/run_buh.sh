#!/usr/bin/env bash
set -euo pipefail

UNIT="buh_orchestrate_$(date +%Y%m%d_%H%M%S)"
echo "UNIT=$UNIT"

systemd-run --user \
  --unit="$UNIT" \
  --collect \
  --property=WorkingDirectory="$PWD" \
  --property=LimitRTPRIO=99 \
  --property=LimitMEMLOCK=infinity \
  --property=LimitNICE=-20 \
  --property=KillMode=control-group \
  --property=TimeoutStopSec=10 \
  bash -lc './buh_orchestrate.sh'

echo ""
echo "Follow journal:"
echo "journalctl --user -u ${UNIT}.service -f"
echo ""
echo "Stop:"
echo "systemctl --user stop ${UNIT}.service"
echo "Follow latest orchestrator log:"
echo "  LOG=\$(ls -t results/buh_logs/orch_*.log | grep -v important | head -n 1); tail -f \"\$LOG\""

journalctl --user -u "$UNIT.service" -f