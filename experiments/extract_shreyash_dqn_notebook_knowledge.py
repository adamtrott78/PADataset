#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

NOTEBOOKS = [
    "legacy/notebooks/non_pa/CNN_CICIDS_runtime.ipynb",
    "legacy/notebooks/non_pa/DQN_CICIDS_Part_v2.ipynb",
    "legacy/notebooks/non_pa/DQN_UNSW.ipynb",
    "legacy/notebooks/non_pa/cnn_unsw.ipynb",
]

OUT = Path("docs/experiments/shreyash_dqn_backbone_recovery.md")

KEYWORDS = [
    "class ",
    "def ",
    "Conv1d",
    "Linear",
    "Dropout",
    "BatchNorm",
    "CrossEntropy",
    "optimizer",
    "Adam",
    "learning_rate",
    "epsilon",
    "DQN",
    "QNet",
    "replay",
    "entropy",
    "p1_p2",
    "unknown",
    "accuracy",
    "loss",
    "train",
    "test",
]


def clean_source(src) -> str:
    if isinstance(src, list):
        text = "".join(src)
    else:
        text = str(src)
    return text.replace("\r\n", "\n").replace("\r", "\n")


def excerpt(text: str, max_lines: int = 90) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    return "\n".join(lines[:max_lines] + [f"... truncated {len(lines) - max_lines} lines ..."])


def has_signal(text: str) -> bool:
    low = text.lower()
    return any(k.lower() in low for k in KEYWORDS)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("# Shreyash DQN/CNN backbone recovery")
    lines.append("")
    lines.append("This document extracts implementation evidence from the four legacy non-PA notebooks associated with Shreyash's CICIDS/UNSW CNN+DQN workflow.")
    lines.append("")
    lines.append("The purpose is **not** to make this workflow mandatory for the final OTA matrix yet. The purpose is to preserve the recipe so it can later be ported into a clean PA model-family track.")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    for nb in NOTEBOOKS:
        lines.append(f"- `{nb}`")
    lines.append("")
    lines.append("## Recovery questions")
    lines.append("")
    lines.append("1. What CNN/backbone architecture was used?")
    lines.append("2. What preprocessing/input representation was assumed?")
    lines.append("3. What training objective, optimizer, epochs, batch size, and regularization were used?")
    lines.append("4. What DQN state/action/reward structure was used?")
    lines.append("5. What parts already exist in `dqn_osr.py`?")
    lines.append("6. What still needs to be ported into the final PA runner?")
    lines.append("")

    for nb_path in NOTEBOOKS:
        p = Path(nb_path)
        lines.append("---")
        lines.append("")
        lines.append(f"## `{nb_path}`")
        lines.append("")

        if not p.exists():
            lines.append("Missing on local filesystem.")
            lines.append("")
            continue

        nb = json.loads(p.read_text(errors="replace"))
        cells = nb.get("cells", [])
        lines.append(f"- cells: `{len(cells)}`")
        lines.append(f"- size_kb: `{p.stat().st_size / 1024:.1f}`")
        lines.append("")

        signal_cells = []
        for i, cell in enumerate(cells):
            ctype = cell.get("cell_type", "?")
            src = clean_source(cell.get("source", ""))
            if has_signal(src):
                signal_cells.append((i, ctype, src))

        lines.append(f"- signal_cells: `{len(signal_cells)}`")
        lines.append("")

        for i, ctype, src in signal_cells:
            title = ""
            for line in src.splitlines():
                stripped = line.strip()
                if stripped.startswith("#") or stripped.startswith("class ") or stripped.startswith("def "):
                    title = stripped[:120]
                    break
            if not title:
                title = src.splitlines()[0].strip()[:120] if src.splitlines() else ""

            lines.append(f"### cell {i} `{ctype}` — {title}")
            lines.append("")
            lines.append("```python" if ctype == "code" else "```text")
            lines.append(excerpt(src))
            lines.append("```")
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Initial interpretation")
    lines.append("")
    lines.append("- The DQN logic should be treated as a separate OSR/evaluator track unless the notebooks reveal a backbone-training loss that materially differs from the current PA CNN.")
    lines.append("- If the CNN recipe differs materially, port it as a new catalog family, not as an ad hoc notebook workflow.")
    lines.append("- Candidate future family name: `shreyash_cnn_dqn_backbone`.")
    lines.append("- Candidate future eval method name: `dqn_osr_expanded5`.")
    lines.append("")
    lines.append("## Porting checklist")
    lines.append("")
    lines.append("- [ ] Extract exact CNN architecture.")
    lines.append("- [ ] Extract preprocessing/input tensor assumptions.")
    lines.append("- [ ] Extract optimizer/lr/batch/epochs/dropout/regularization.")
    lines.append("- [ ] Extract DQN state vector.")
    lines.append("- [ ] Extract action semantics.")
    lines.append("- [ ] Extract reward/centroid/update logic.")
    lines.append("- [ ] Compare against `dqn_osr.py`.")
    lines.append("- [ ] Decide whether to port only DQN OSR head or also CNN backbone training.")
    lines.append("- [ ] Add catalog family only after a tiny PA smoke validation.")
    lines.append("")

    OUT.write_text("\n".join(lines))
    print(OUT)


if __name__ == "__main__":
    main()
