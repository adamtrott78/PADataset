#!/usr/bin/env python3
"""Rebuild the locked scientific deck and apply the official MILCOM 2026 template."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"


def run(script: str) -> None:
    subprocess.run([sys.executable, str(TOOLS / script)], check=True)


def main() -> None:
    run("build_svg_slides.py")
    run("apply_milcom26_template.py")
    print("Built 12 MILCOM-template SVG slides.")


if __name__ == "__main__":
    main()
