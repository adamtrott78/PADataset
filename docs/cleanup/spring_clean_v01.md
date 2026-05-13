# Spring clean v01

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

