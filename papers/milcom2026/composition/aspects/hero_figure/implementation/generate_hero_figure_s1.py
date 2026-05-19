#!/usr/bin/env python3
"""
Generate Hero Figure Candidate S1.

This script creates a deterministic SVG block diagram for the MILCOM 2026
DQNGuard hero figure. It is intentionally script-generated so the figure can
be versioned, regenerated, and refined through the comparative-analysis loop.

Output:
  papers/milcom2026/figures/hero_figure/hero_dqnguard_pipeline_s1.svg
  papers/milcom2026/figures/hero_figure/hero_dqnguard_pipeline_s1.pdf  if conversion tool exists
  papers/milcom2026/figures/hero_figure/hero_dqnguard_pipeline_s1.png  if conversion tool exists
"""

from __future__ import annotations

import argparse
import html
import shutil
import subprocess
from pathlib import Path
from textwrap import wrap


W = 2130
H = 765

COLORS = {
    "bg": "#ffffff",
    "ink": "#1f2933",
    "muted": "#4b5563",
    "line": "#3f4752",
    "panel_input": "#eeeeee",
    "panel_backbone": "#d9deea",
    "panel_guard": "#b9d1e8",
    "panel_outputs": "#f7f7f5",
    "box": "#f8fafc",
    "box_blue": "#dcecff",
    "known": "#d9ead3",
    "unknown": "#fce5cd",
    "downstream": "#eadcf3",
    "qrcwos": "#d9eadf",
    "accent_orange": "#d9822b",
}


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def svg_header() -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="7.1in" height="2.55in" '
        f'viewBox="0 0 {W} {H}" role="img" aria-label="DQNGuard hero figure">\n'
        f'<rect x="0" y="0" width="{W}" height="{H}" fill="{COLORS["bg"]}"/>\n'
        '<style>\n'
        '  text { font-family: Helvetica, Arial, sans-serif; fill: #1f2933; }\n'
        '  .title { font-size: 37px; font-weight: 700; }\n'
        '  .subtitle { font-size: 25px; fill: #374151; }\n'
        '  .label { font-size: 31px; font-weight: 500; }\n'
        '  .detail { font-size: 25px; fill: #2f3742; }\n'
        '  .small { font-size: 23px; fill: #384252; }\n'
        '  .num { font-size: 34px; font-weight: 700; }\n'
        '</style>\n'
        '<defs>\n'
        '  <marker id="arrow" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto" markerUnits="strokeWidth">\n'
        f'    <path d="M 0 0 L 12 6 L 0 12 z" fill="{COLORS["line"]}"/>\n'
        '  </marker>\n'
        '  <marker id="arrow_orange" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto" markerUnits="strokeWidth">\n'
        f'    <path d="M 0 0 L 12 6 L 0 12 z" fill="{COLORS["accent_orange"]}"/>\n'
        '  </marker>\n'
        '</defs>\n'
    )


def rect(x, y, w, h, fill, stroke=None, sw=3, rx=18, cls=None) -> str:
    stroke = stroke or COLORS["line"]
    klass = f' class="{cls}"' if cls else ""
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" ry="{rx}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{klass}/>\n'
    )


def line(x1, y1, x2, y2, color=None, sw=4, marker="arrow") -> str:
    color = color or COLORS["line"]
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        f'stroke="{color}" stroke-width="{sw}" stroke-linecap="round" '
        f'marker-end="url(#{marker})"/>\n'
    )


def polyline(points, color=None, sw=4, marker="arrow") -> str:
    color = color or COLORS["line"]
    pts = " ".join(f"{x},{y}" for x, y in points)
    return (
        f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{sw}" '
        f'stroke-linecap="round" stroke-linejoin="round" marker-end="url(#{marker})"/>\n'
    )


def text_center(x, y, text, cls="label", anchor="middle") -> str:
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" class="{cls}">{esc(text)}</text>\n'


def multiline_center(x, y, lines, cls="detail", line_h=31, anchor="middle") -> str:
    out = [f'<text x="{x}" y="{y}" text-anchor="{anchor}" class="{cls}">\n']
    for i, s in enumerate(lines):
        dy = 0 if i == 0 else line_h
        out.append(f'  <tspan x="{x}" dy="{dy}">{esc(s)}</tspan>\n')
    out.append('</text>\n')
    return "".join(out)


def wrapped_center(x, y, text, max_chars, cls="detail", line_h=30) -> str:
    lines = []
    for part in text.split("\n"):
        if part.strip():
            lines.extend(wrap(part, width=max_chars, break_long_words=False))
        else:
            lines.append("")
    return multiline_center(x, y, lines, cls=cls, line_h=line_h)


def draw_box_with_text(x, y, w, h, fill, title, detail_lines=None, title_cls="label", detail_cls="detail", stroke=None, rx=18):
    if detail_lines is None:
        detail_lines = []
    out = rect(x, y, w, h, fill=fill, stroke=stroke, rx=rx)
    if detail_lines:
        out += multiline_center(x + w / 2, y + h * 0.36, [title], cls=title_cls, line_h=28)
        out += multiline_center(x + w / 2, y + h * 0.58, detail_lines, cls=detail_cls, line_h=28)
    else:
        out += multiline_center(x + w / 2, y + h * 0.52, [title], cls=title_cls, line_h=28)
    return out


def build_svg() -> str:
    s = [svg_header()]

    # Main panels
    input_x, input_y, input_w, input_h = 25, 28, 385, 690
    backbone_x, backbone_y, backbone_w, backbone_h = 435, 28, 590, 690
    guard_x, guard_y, guard_w, guard_h = 1060, 28, 465, 690
    outputs_x, outputs_y, outputs_w, outputs_h = 1550, 28, 555, 690

    s.append(rect(input_x, input_y, input_w, input_h, COLORS["panel_input"], sw=3.2, rx=20))
    s.append(rect(backbone_x, backbone_y, backbone_w, backbone_h, COLORS["panel_backbone"], sw=3.2, rx=20))
    s.append(rect(guard_x, guard_y, guard_w, guard_h, COLORS["panel_guard"], sw=3.6, rx=20))
    s.append(rect(outputs_x, outputs_y, outputs_w, outputs_h, COLORS["bg"], stroke="#ffffff", sw=0, rx=0))

    # Panel titles
    s.append(text_center(input_x + input_w / 2, 78, "OTA RF Observation", "title"))
    s.append(text_center(backbone_x + backbone_w / 2, 78, "PA Backbone", "title"))
    s.append(text_center(guard_x + guard_w / 2, 73, "DQNGuard", "title"))
    s.append(text_center(guard_x + guard_w / 2, 112, "budgeted open-set decision layer", "subtitle"))
    s.append(multiline_center(outputs_x + outputs_w / 2, 70, ["Outputs and", "Downstream Use"], "title", line_h=40))

    # Input inner box
    s.append(draw_box_with_text(
        62, 338, 320, 120, COLORS["box"],
        "OTA RF Window",
        ["complex IQ window", "WiFi / Bluetooth / Zigbee"],
        title_cls="label", detail_cls="small", rx=18
    ))

    # Backbone internal
    md_x, md_y, md_w, md_h = 468, 335, 320, 130
    s.append(draw_box_with_text(
        md_x, md_y, md_w, md_h, COLORS["box"],
        "multi-domain RF", ["representation", "IQ / FFT / DCT / polar"],
        title_cls="label", detail_cls="small", rx=18
    ))

    out_x, out_w, out_h = 828, 195, 105
    stack = [
        (210, "closed-set", "logits z"),
        (330, "softmax", "p"),
        (450, "feature", "h"),
        (570, "predicted PA", "ŷ"),
    ]
    for y, a, b in stack:
        s.append(draw_box_with_text(out_x, y, out_w, out_h, COLORS["box"], a, [b], title_cls="detail", detail_cls="detail", rx=12))
        s.append(line(md_x + md_w, md_y + md_h / 2, out_x - 12, y + out_h / 2, sw=3.2))

    # Main arrows
    s.append(line(382, 398, 432, 398, sw=4))
    s.append(line(backbone_x + backbone_w, 398, guard_x - 12, 398, sw=4))

    # DQNGuard stages
    stage_x, stage_w, stage_h = guard_x + 22, guard_w - 44, 155
    stages = [
        (155, "1", "Predicted-class", ["calibration", "select bands for ŷ"]),
        (333, "2", "Guard evidence", ["P₁, P₁ − P₂, H", "variance V, energy E"]),
        (511, "3", "Known-budget threshold", ["r(x) ≥ τβ", "β = 0.05"]),
    ]

    for y, num, title, details in stages:
        s.append(rect(stage_x, y, stage_w, stage_h, COLORS["box_blue"], stroke="#2f5f89", sw=3, rx=16))
        s.append(text_center(stage_x + 25, y + 58, num, "num", anchor="middle"))
        s.append(multiline_center(stage_x + stage_w / 2 + 20, y + 48, [title], "label", line_h=32))
        s.append(multiline_center(stage_x + stage_w / 2 + 20, y + 86, details, "small", line_h=29))

    # Outputs
    known_x, known_y, known_w, known_h = 1578, 170, 265, 165
    unknown_x, unknown_y, unknown_w, unknown_h = 1578, 415, 265, 165
    ds_x, ds_w, ds_h = 1888, 228, 118

    s.append(draw_box_with_text(
        known_x, known_y, known_w, known_h, COLORS["known"],
        "Known PA", ["evidence", "Scan / Burst /", "Sustain / Hop / Replay"],
        title_cls="label", detail_cls="small", stroke="#4d7a4d", rx=18
    ))
    s.append(draw_box_with_text(
        unknown_x, unknown_y, unknown_w, unknown_h, COLORS["unknown"],
        "Unknown", ["behavior pool", "candidate novel", "signal behavior"],
        title_cls="label", detail_cls="small", stroke=COLORS["accent_orange"], rx=18
    ))

    s.append(draw_box_with_text(
        ds_x, 170, ds_w, ds_h, COLORS["downstream"],
        "ATT&CK/EW", ["precursor", "hypotheses"],
        title_cls="detail", detail_cls="small", stroke="#7a5c84", rx=14
    ))
    s.append(draw_box_with_text(
        ds_x, 365, ds_w, ds_h, "#eeeeee",
        "LLM-assisted", ["label-making"],
        title_cls="detail", detail_cls="small", stroke="#707070", rx=14
    ))
    s.append(draw_box_with_text(
        ds_x, 560, ds_w, ds_h, COLORS["qrcwos"],
        "QR-CWoS", ["response", "planning"],
        title_cls="detail", detail_cls="small", stroke="#5a7868", rx=14
    ))

    # Arrows from DQNGuard to known/unknown and downstream
    s.append(polyline([(guard_x + guard_w, 290), (1558, 290), (1578, 252)], sw=4))
    s.append(polyline([(guard_x + guard_w, 455), (1558, 455), (1578, 497)], color=COLORS["accent_orange"], sw=4, marker="arrow_orange"))

    s.append(line(known_x + known_w, known_y + known_h / 2, ds_x - 12, 230, sw=3.6))
    s.append(polyline([(unknown_x + unknown_w, unknown_y + unknown_h / 2), (1862, 497), (1862, 424), (ds_x - 12, 424)], color=COLORS["accent_orange"], sw=3.6, marker="arrow_orange"))
    s.append(polyline([(unknown_x + unknown_w, unknown_y + unknown_h / 2), (1862, 497), (1862, 619), (ds_x - 12, 619)], color=COLORS["accent_orange"], sw=3.6, marker="arrow_orange"))

    # Small footnote-like cue inside output region
    s.append(multiline_center(1740, 682, ["known labels support prediction;", "unknowns support discovery"], cls="small", line_h=26))

    s.append("</svg>\n")
    return "".join(s)


def try_convert(svg_path: Path, pdf_path: Path, png_path: Path) -> None:
    inkscape = shutil.which("inkscape")
    if inkscape:
        subprocess.run([inkscape, str(svg_path), "--export-type=pdf", f"--export-filename={pdf_path}"], check=True)
        subprocess.run([inkscape, str(svg_path), "--export-type=png", f"--export-filename={png_path}", "--export-dpi=300"], check=True)
        print(f"Wrote: {pdf_path}")
        print(f"Wrote: {png_path}")
        return

    try:
        import cairosvg  # type: ignore
    except Exception:
        print("SVG written. PDF/PNG not created because neither inkscape nor cairosvg is available.")
        print("Install one of:")
        print("  sudo apt install -y inkscape")
        print("  pip install cairosvg")
        return

    cairosvg.svg2pdf(url=str(svg_path), write_to=str(pdf_path))
    cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), output_width=W, output_height=H)
    print(f"Wrote: {pdf_path}")
    print(f"Wrote: {png_path}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="papers/milcom2026/figures/hero_figure")
    ap.add_argument("--name", default="hero_dqnguard_pipeline_s1")
    ap.add_argument("--no-convert", action="store_true", help="Only write SVG.")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    svg_path = outdir / f"{args.name}.svg"
    pdf_path = outdir / f"{args.name}.pdf"
    png_path = outdir / f"{args.name}.png"

    svg_path.write_text(build_svg(), encoding="utf-8")
    print(f"Wrote: {svg_path}")

    if not args.no_convert:
        try_convert(svg_path, pdf_path, png_path)


if __name__ == "__main__":
    main()
