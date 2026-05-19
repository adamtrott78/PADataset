#!/usr/bin/env python3
"""
Generate Hero Figure Candidate S2.

S2 fixes S1's largest problems:
  - custom small arrowheads instead of SVG markers;
  - tighter canvas;
  - reduced text sizes;
  - cleaner output/downstream region;
  - quieter backbone fan-out connectors;
  - no bottom note.

Outputs:
  papers/milcom2026/figures/hero_figure/hero_dqnguard_pipeline_s2.svg
  papers/milcom2026/figures/hero_figure/hero_dqnguard_pipeline_s2.pdf
  papers/milcom2026/figures/hero_figure/hero_dqnguard_pipeline_s2.png
"""

from __future__ import annotations

import argparse
import html
import math
import shutil
import subprocess
from pathlib import Path


W = 2130
H = 645

COLORS = {
    "bg": "#ffffff",
    "ink": "#1f2933",
    "muted": "#4b5563",
    "line": "#4a5562",
    "input": "#eeeeee",
    "backbone": "#d8deea",
    "guard": "#b8d2e8",
    "box": "#f8fafc",
    "stage": "#d9ebff",
    "known": "#dcefd7",
    "unknown": "#fde7c8",
    "downstream": "#eadcf3",
    "llm": "#eeeeee",
    "qrcwos": "#dcefe5",
    "green_stroke": "#4f7c52",
    "orange": "#d9822b",
    "blue_stroke": "#2f5f89",
}


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def svg_header() -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="7.1in" height="2.15in" '
        f'viewBox="0 0 {W} {H}" role="img" aria-label="DQNGuard evidence-flow hero figure">\n'
        f'<rect x="0" y="0" width="{W}" height="{H}" fill="{COLORS["bg"]}"/>\n'
        '<style>\n'
        '  text { font-family: Helvetica, Arial, sans-serif; fill: #1f2933; }\n'
        '  .paneltitle { font-size: 32px; font-weight: 700; }\n'
        '  .subtitle { font-size: 22px; fill: #374151; }\n'
        '  .label { font-size: 26px; font-weight: 500; }\n'
        '  .detail { font-size: 21px; fill: #2f3742; }\n'
        '  .small { font-size: 19px; fill: #384252; }\n'
        '  .num { font-size: 29px; font-weight: 700; }\n'
        '</style>\n'
    )


def rect(x, y, w, h, fill, stroke=None, sw=2.6, rx=16) -> str:
    stroke = stroke or COLORS["line"]
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" ry="{rx}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>\n'
    )


def text(x, y, s, cls="label", anchor="middle") -> str:
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" class="{cls}">{esc(s)}</text>\n'


def multiline(x, y, lines, cls="detail", line_h=25, anchor="middle") -> str:
    out = [f'<text x="{x}" y="{y}" text-anchor="{anchor}" class="{cls}">\n']
    for i, line in enumerate(lines):
        dy = 0 if i == 0 else line_h
        out.append(f'  <tspan x="{x}" dy="{dy}">{esc(line)}</tspan>\n')
    out.append('</text>\n')
    return "".join(out)


def box_text(x, y, w, h, fill, title, details=None, stroke=None, title_cls="label", detail_cls="small", rx=14) -> str:
    details = details or []
    out = rect(x, y, w, h, fill, stroke=stroke, rx=rx)
    if details:
        out += multiline(x + w / 2, y + h * 0.34, [title], cls=title_cls, line_h=24)
        out += multiline(x + w / 2, y + h * 0.56, details, cls=detail_cls, line_h=23)
    else:
        out += text(x + w / 2, y + h * 0.55, title, cls=title_cls)
    return out


def arrow(points, color=None, sw=3.0, head=15.0) -> str:
    """Draw a polyline with a custom triangular arrowhead."""
    color = color or COLORS["line"]
    if len(points) < 2:
        return ""

    # Draw the shaft. It ends at the arrow tip; triangle covers the endpoint.
    d = " ".join(f"{x},{y}" for x, y in points)
    out = (
        f'<polyline points="{d}" fill="none" stroke="{color}" stroke-width="{sw}" '
        f'stroke-linecap="round" stroke-linejoin="round"/>\n'
    )

    x1, y1 = points[-2]
    x2, y2 = points[-1]
    ang = math.atan2(y2 - y1, x2 - x1)
    bx = x2 - head * math.cos(ang)
    by = y2 - head * math.sin(ang)
    px = (head * 0.42) * math.sin(ang)
    py = -(head * 0.42) * math.cos(ang)

    p1 = (x2, y2)
    p2 = (bx + px, by + py)
    p3 = (bx - px, by - py)
    pts = f"{p1[0]},{p1[1]} {p2[0]},{p2[1]} {p3[0]},{p3[1]}"
    out += f'<polygon points="{pts}" fill="{color}" stroke="{color}" stroke-width="0"/>\n'
    return out


def build_svg() -> str:
    s = [svg_header()]

    # Main grouped regions
    input_panel = (24, 28, 355, 575)
    backbone_panel = (405, 28, 555, 575)
    guard_panel = (990, 28, 515, 575)
    out_panel = (1535, 28, 560, 575)

    ix, iy, iw, ih = input_panel
    bx, by, bw, bh = backbone_panel
    gx, gy, gw, gh = guard_panel
    ox, oy, ow, oh = out_panel

    s.append(rect(ix, iy, iw, ih, COLORS["input"], sw=2.8, rx=18))
    s.append(rect(bx, by, bw, bh, COLORS["backbone"], sw=2.8, rx=18))
    s.append(rect(gx, gy, gw, gh, COLORS["guard"], sw=3.0, rx=18))

    # Titles
    s.append(text(ix + iw / 2, 72, "OTA RF Observation", "paneltitle"))
    s.append(text(bx + bw / 2, 72, "PA Backbone", "paneltitle"))
    s.append(text(gx + gw / 2, 67, "DQNGuard", "paneltitle"))
    s.append(text(gx + gw / 2, 103, "budgeted open-set decision layer", "subtitle"))
    s.append(multiline(ox + ow / 2, 70, ["Outputs and", "Downstream Use"], "paneltitle", line_h=35))

    # Input
    input_box = (58, 290, 288, 112)
    s.append(box_text(
        *input_box,
        fill=COLORS["box"],
        title="OTA RF Window",
        details=["complex IQ window", "WiFi / Bluetooth / Zigbee"],
        rx=13,
    ))

    # Backbone
    rep_box = (438, 282, 300, 128)
    s.append(box_text(
        *rep_box,
        fill=COLORS["box"],
        title="multi-domain RF",
        details=["representation", "IQ / FFT / DCT / polar"],
        rx=13,
    ))

    # Backbone outputs as a quieter evidence stack
    stack_x, stack_w, stack_h = 785, 155, 80
    stack_items = [
        (155, "closed-set", "logits z"),
        (250, "softmax", "p"),
        (345, "feature", "h"),
        (440, "predicted PA", "ŷ"),
    ]
    for sy, title, detail in stack_items:
        s.append(box_text(
            stack_x, sy, stack_w, stack_h,
            fill=COLORS["box"],
            title=title,
            details=[detail],
            title_cls="small",
            detail_cls="small",
            rx=10,
        ))
        # Quiet connectors: no arrowheads
        s.append(
            f'<line x1="{rep_box[0] + rep_box[2]}" y1="{rep_box[1] + rep_box[3]/2}" '
            f'x2="{stack_x}" y2="{sy + stack_h/2}" stroke="#6b7280" '
            f'stroke-width="2.0" stroke-linecap="round"/>\n'
        )

    # Main flow arrows
    s.append(arrow([(346, 346), (402, 346)], sw=3.2, head=17))
    s.append(arrow([(738, 346), (783, 346)], sw=2.8, head=14))
    s.append(arrow([(940, 346), (987, 346)], sw=3.2, head=17))

    # DQNGuard stages
    stage_x, stage_w, stage_h = 1014, 467, 126
    stages = [
        (138, "1", "Predicted-class", ["calibration", "select bands for ŷ"]),
        (286, "2", "Guard evidence", ["P₁, P₁ − P₂, H", "variance V, energy E"]),
        (434, "3", "Known-budget threshold", ["r(x) ≥ τβ", "β = 0.05"]),
    ]
    for y, num, title, details in stages:
        s.append(rect(stage_x, y, stage_w, stage_h, COLORS["stage"], stroke=COLORS["blue_stroke"], sw=2.6, rx=14))
        s.append(text(stage_x + 34, y + 52, num, "num"))
        s.append(text(stage_x + stage_w / 2 + 26, y + 39, title, "label"))
        s.append(multiline(stage_x + stage_w / 2 + 26, y + 72, details, "small", line_h=22))

    # Outputs
    known = (1558, 160, 255, 140)
    unknown = (1558, 378, 255, 140)

    s.append(box_text(
        *known,
        fill=COLORS["known"],
        stroke=COLORS["green_stroke"],
        title="Known PA evidence",
        details=["Scan / Burst /", "Sustain / Hop / Replay"],
        title_cls="label",
        detail_cls="small",
        rx=14,
    ))

    s.append(box_text(
        *unknown,
        fill=COLORS["unknown"],
        stroke=COLORS["orange"],
        title="Unknown behavior pool",
        details=["candidate novel", "signal behavior"],
        title_cls="label",
        detail_cls="small",
        rx=14,
    ))

    # Downstream boxes
    ds_x, ds_w, ds_h = 1852, 214, 100
    s.append(box_text(
        ds_x, 160, ds_w, ds_h,
        COLORS["downstream"],
        title="ATT&CK/EW",
        details=["precursor", "hypotheses"],
        stroke="#7a5c84",
        title_cls="detail",
        detail_cls="small",
        rx=12,
    ))
    s.append(box_text(
        ds_x, 305, ds_w, ds_h,
        COLORS["llm"],
        title="LLM-assisted",
        details=["label-making"],
        stroke="#707070",
        title_cls="detail",
        detail_cls="small",
        rx=12,
    ))
    s.append(box_text(
        ds_x, 450, ds_w, ds_h,
        COLORS["qrcwos"],
        title="QR-CWoS",
        details=["response", "planning"],
        stroke="#5a7868",
        title_cls="detail",
        detail_cls="small",
        rx=12,
    ))

    # DQNGuard decision split. Clean small arrows.
    s.append(arrow([(1505, 250), (1556, 230)], sw=3.0, head=15))
    s.append(arrow([(1505, 397), (1556, 448)], color=COLORS["orange"], sw=3.0, head=15))

    # Downstream arrows
    s.append(arrow([(1813, 230), (1850, 210)], sw=2.8, head=13))
    s.append(arrow([(1813, 448), (1850, 355)], color=COLORS["orange"], sw=2.8, head=13))
    s.append(arrow([(1813, 448), (1850, 500)], color=COLORS["orange"], sw=2.8, head=13))

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
        import cairosvg
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", default="papers/milcom2026/figures/hero_figure")
    parser.add_argument("--name", default="hero_dqnguard_pipeline_s2")
    parser.add_argument("--no-convert", action="store_true")
    args = parser.parse_args()

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
