> **Historical evidence.** This record describes an earlier run, design iteration or recovery. Its next steps, paths, scores and settings are historical observations, not current instructions. Current workflow: [owning context](CONTEXT.md).

# Spring clean

This cleanup pass preserves core dataset generation and CNN/OSR library code while moving notebook-era interfaces and local artifacts out of the active repo root.

Preserved as core:
- prepData.py
- discriminate.py
- evaluate.py
- osr_core.py
- varmax_osr.py
- dqn_osr.py
- cacheBuild.py
- manifestBuild.py
- core/
- protocol/
- txrx/ current capture/splice files
- tools/
- config/

Preserved as historical artifacts:
- buh_orchestrate.sh
- run_buh.sh
- buh_capture.m
- buh.m
- buh.txt
- pipeline_status_buh.sh

New intended operating model:
manifest -> parallel launcher -> one-run worker -> verified artifacts -> dashboard -> reducer -> OSR evaluation.
