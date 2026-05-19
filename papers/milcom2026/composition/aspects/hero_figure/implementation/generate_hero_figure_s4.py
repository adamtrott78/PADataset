#!/usr/bin/env python3
"""
Generate Hero Figure Candidate S4.

S4 is a focused horizontal revision:
  - renames panels;
  - adds an explicit PA CNN encoder block;
  - reduces PA Backbone dominance;
  - creates an output/context panel;
  - routes metric arrows to the DQNGuard stages they support;
  - keeps numbered stages and adds subtle stage-flow arrows;
  - changes unknown output from orange to scarlet/red-gold;
  - improves math-style text.
"""

from __future__ import annotations

import argparse
import html
import math
import shutil
import subprocess
from pathlib import Path


W, H = 2130, 660

COLORS = {
    "bg": "#ffffff",
    "ink": "#1f2933",
    "line": "#4b5563",

    "obs_panel": "#f1f3f5",
    "backbone_panel": "#e4e9f1",
    "guard_panel": "#bcd3e8",
    "output_panel": "#f7f7f4",

    "box": "#f8fafc",
    "fusion": "#edf2f7",
    "model": "#eef4fb",
    "stage": "#dcecff",

    "guard_stroke": "#2f5f89",

    "known_fill": "#dcefd7",
    "known_stroke": "#4f7c52",

    "unknown_fill": "#fde2df",
    "unknown_stroke": "#b33a3a",

    "downstream_fill": "#eee5f4",
    "downstream_stroke": "#7a5c84",
    "llm_fill": "#eeeeee",
    "llm_stroke": "#707070",
    "qrcwos_fill": "#dcefe5",
    "qrcwos_stroke": "#5a7868",
}


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def header() -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="7.1in" height="2.2in" '
        f'viewBox="0 0 {W} {H}" role="img" aria-label="DQNGuard evidence-flow hero figure">\n'
        f'<rect x="0" y="0" width="{W}" height="{H}" fill="{COLORS["bg"]}"/>\n'
        '<style>\n'
        '  text { font-family: Helvetica, Arial, sans-serif; fill: #1f2933; }\n'
        '  .paneltitle { font-size: 27px; font-weight: 700; }\n'
        '  .subtitle { font-size: 18px; fill: #374151; }\n'
        '  .label { font-size: 22px; font-weight: 500; }\n'
        '  .detail { font-size: 18px; fill: #2f3742; }\n'
        '  .small { font-size: 15.5px; fill: #384252; }\n'
        '  .num { font-size: 24px; font-weight: 700; }\n'
        '  .math { font-family: "Times New Roman", Times, serif; font-size: 17px; font-style: italic; fill: #1f2933; }\n'
        '  .mathsmall { font-family: "Times New Roman", Times, serif; font-size: 15px; font-style: italic; fill: #1f2933; }\n'
        '</style>\n'
    )


def rect(x, y, w, h, fill, stroke=None, sw=2.2, rx=12) -> str:
    stroke = stroke or COLORS["line"]
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" ry="{rx}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>\n'
    )


def text(x, y, s, cls="label", anchor="middle") -> str:
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" class="{cls}">{esc(s)}</text>\n'


def lines(x, y, items, cls="detail", line_h=20, anchor="middle") -> str:
    out = [f'<text x="{x}" y="{y}" text-anchor="{anchor}" class="{cls}">\n']
    for i, item in enumerate(items):
        dy = 0 if i == 0 else line_h
        if isinstance(item, tuple):
            value, item_cls = item
            out.append(f'  <tspan x="{x}" dy="{dy}" class="{item_cls}">{esc(value)}</tspan>\n')
        else:
            out.append(f'  <tspan x="{x}" dy="{dy}">{esc(item)}</tspan>\n')
    out.append('</text>\n')
    return "".join(out)


def box(x, y, w, h, fill, title, details=None, stroke=None, title_cls="label", detail_cls="small", rx=10, sw=2.0) -> str:
    details = details or []
    out = rect(x, y, w, h, fill, stroke=stroke, sw=sw, rx=rx)
    if details:
        out += lines(x + w / 2, y + h * 0.34, [title], cls=title_cls, line_h=19)
        out += lines(x + w / 2, y + h * 0.58, details, cls=detail_cls, line_h=19)
    else:
        out += text(x + w / 2, y + h * 0.55, title, cls=title_cls)
    return out


def arrow(points, color=None, sw=2.2, head=9.0) -> str:
    color = color or COLORS["line"]
    if len(points) < 2:
        return ""

    pts = " ".join(f"{x},{y}" for x, y in points)
    out = (
        f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{sw}" '
        f'stroke-linecap="round" stroke-linejoin="round"/>\n'
    )

    x1, y1 = points[-2]
    x2, y2 = points[-1]
    ang = math.atan2(y2 - y1, x2 - x1)
    bx = x2 - head * math.cos(ang)
    by = y2 - head * math.sin(ang)
    px = (head * 0.42) * math.sin(ang)
    py = -(head * 0.42) * math.cos(ang)
    tri = f"{x2},{y2} {bx + px},{by + py} {bx - px},{by - py}"
    out += f'<polygon points="{tri}" fill="{color}" stroke="{color}" stroke-width="0"/>\n'
    return out


def build_svg() -> str:
    s = [header()]

    # Main panels
    obs = (22, 32, 285, 560)
    back = (330, 32, 720, 560)
    guard = (1073, 32, 470, 560)
    outp = (1565, 32, 540, 560)

    ox, oy, ow, oh = obs
    bx, by, bw, bh = back
    gx, gy, gw, gh = guard
    px, py, pw, ph = outp

    s.append(rect(*obs, fill=COLORS["obs_panel"], sw=2.6, rx=17))
    s.append(rect(*back, fill=COLORS["backbone_panel"], sw=2.6, rx=17))
    s.append(rect(*guard, fill=COLORS["guard_panel"], sw=2.9, rx=17))
    s.append(rect(*outp, fill=COLORS["output_panel"], stroke="#d6d6d0", sw=1.5, rx=17))

    s.append(text(ox + ow / 2, 72, "RF Observation", "paneltitle"))
    s.append(text(bx + bw / 2, 72, "Multi-Domain PA Backbone", "paneltitle"))
    s.append(text(gx + gw / 2, 68, "DQNGuard", "paneltitle"))
    s.append(text(gx + gw / 2, 98, "budgeted open-set decision layer", "subtitle"))
    s.append(lines(px + pw / 2, 68, ["Decision Outputs", "and Consumers"], "paneltitle", line_h=31))

    # Input window
    win = (58, 280, 214, 92)
    s.append(box(*win, fill=COLORS["box"], title="OTA RF Window", details=["complex IQ window"], detail_cls="small", rx=11))

    # Transform stack
    rep_x, rep_w, rep_h = 350, 130, 58
    rep_ys = [145, 225, 305, 385]
    reps = [
        ("Original IQ", "I/Q samples"),
        ("FFT", "frequency"),
        ("DCT", "cosine"),
        ("Polar", "mag / phase"),
    ]
    for (title, detail), y in zip(reps, rep_ys):
        s.append(box(rep_x, y, rep_w, rep_h, COLORS["box"], title, [detail], title_cls="small", detail_cls="small", rx=9, sw=1.8))
        s.append(arrow([(win[0] + win[2], win[1] + win[3]/2), (rep_x - 7, y + rep_h/2)], sw=1.8, head=7))

    # Fusion and model
    fusion = (520, 255, 165, 118)
    model = (710, 255, 150, 118)

    s.append(box(
        *fusion, fill=COLORS["fusion"], title="fusion",
        details=["concatenate", "adaptive avg pool", ("N = 8192", "mathsmall")],
        title_cls="label", detail_cls="small", rx=11
    ))
    s.append(box(
        *model, fill=COLORS["model"], title="PA CNN",
        details=["encoder", "closed-set head"],
        title_cls="label", detail_cls="small", rx=11
    ))

    for y in rep_ys:
        s.append(arrow([(rep_x + rep_w, y + rep_h/2), (fusion[0] - 7, fusion[1] + fusion[3]/2)], sw=1.8, head=7))
    s.append(arrow([(fusion[0] + fusion[2], fusion[1] + fusion[3]/2), (model[0] - 7, model[1] + model[3]/2)], sw=2.0, head=8))

    # Metrics
    met_x, met_w, met_h = 895, 130, 58
    met_ys = [145, 225, 305, 385]
    metrics = [
        ("logits", ("z", "mathsmall")),
        ("softmax", ("p", "mathsmall")),
        ("feature", ("h", "mathsmall")),
        ("predicted PA", ("ŷ", "mathsmall")),
    ]
    for (title, detail), y in zip(metrics, met_ys):
        s.append(box(met_x, y, met_w, met_h, COLORS["box"], title, [detail], title_cls="small", detail_cls="mathsmall", rx=9, sw=1.8))
        s.append(arrow([(model[0] + model[2], model[1] + model[3]/2), (met_x - 7, y + met_h/2)], sw=1.8, head=7))

    # DQNGuard stages
    stage_x, stage_w, stage_h = gx + 25, gw - 50, 112
    stage1 = (stage_x, 130, stage_w, stage_h)
    stage2 = (stage_x, 277, stage_w, stage_h)
    stage3 = (stage_x, 424, stage_w, stage_h)

    stages = [
        (stage1, "1", "Predicted-class calibration", ["select bands for ŷ"]),
        (stage2, "2", "Guard evidence", [("P₁, P₁ − P₂, H", "mathsmall"), ("V, E, r(x)", "mathsmall")]),
        (stage3, "3", "Known-budget threshold", [("r(x) ≥ τβ", "mathsmall"), ("β = 0.05", "mathsmall")]),
    ]

    for (x, y, w, h), num, title, detail in stages:
        s.append(rect(x, y, w, h, COLORS["stage"], stroke=COLORS["guard_stroke"], sw=2.2, rx=12))
        s.append(text(x + 30, y + 49, num, "num"))
        s.append(text(x + w / 2 + 20, y + 38, title, "label"))
        s.append(lines(x + w / 2 + 20, y + 69, detail, "small", line_h=18))

    # Subtle internal cascade arrows in DQNGuard
    mid_x = gx + gw / 2
    s.append(arrow([(mid_x, stage1[1] + stage1[3] + 4), (mid_x, stage2[1] - 7)], color=COLORS["guard_stroke"], sw=1.7, head=7))
    s.append(arrow([(mid_x, stage2[1] + stage2[3] + 4), (mid_x, stage3[1] - 7)], color=COLORS["guard_stroke"], sw=1.7, head=7))

    # Route metrics to corresponding DQNGuard stages.
    # predicted PA -> stage 1
    s.append(arrow([(met_x + met_w, met_ys[3] + met_h/2), (stage1[0] - 8, stage1[1] + stage1[3]/2)], sw=2.0, head=8))

    # z, p, h -> stage 2
    for y in [met_ys[0], met_ys[1], met_ys[2]]:
        s.append(arrow([(met_x + met_w, y + met_h/2), (stage2[0] - 8, stage2[1] + stage2[3]/2)], sw=1.9, head=8))

    # Outputs
    known = (1587, 160, 230, 108)
    unknown = (1587, 390, 230, 108)

    s.append(box(
        *known, fill=COLORS["known_fill"], stroke=COLORS["known_stroke"],
        title="Known PA evidence",
        details=["Scan / Burst /", "Sustain / Hop / Replay"],
        title_cls="detail", detail_cls="small", rx=11
    ))
    s.append(box(
        *unknown, fill=COLORS["unknown_fill"], stroke=COLORS["unknown_stroke"],
        title="Unknown behavior pool",
        details=["candidate novel", "signal behavior"],
        title_cls="detail", detail_cls="small", rx=11
    ))

    ds_x, ds_w, ds_h = 1850, 220, 86
    s.append(box(ds_x, 140, ds_w, ds_h, COLORS["downstream_fill"], "ATT&CK/EW", ["precursor hypotheses"], stroke=COLORS["downstream_stroke"], title_cls="detail", detail_cls="small", rx=10))
    s.append(box(ds_x, 287, ds_w, ds_h, COLORS["llm_fill"], "LLM-assisted", ["label-making"], stroke=COLORS["llm_stroke"], title_cls="detail", detail_cls="small", rx=10))
    s.append(box(ds_x, 434, ds_w, ds_h, COLORS["qrcwos_fill"], "QR-CWoS", ["response planning"], stroke=COLORS["qrcwos_stroke"], title_cls="detail", detail_cls="small", rx=10))

    # Decision branch arrows
    s.append(arrow([(gx + gw, 245), (known[0] - 7, known[1] + known[3]/2)], color=COLORS["known_stroke"], sw=2.1, head=9))
    s.append(arrow([(gx + gw, 418), (unknown[0] - 7, unknown[1] + unknown[3]/2)], color=COLORS["unknown_stroke"], sw=2.1, head=9))

    # Consumer arrows
    s.append(arrow([(known[0] + known[2], known[1] + known[3]/2), (ds_x - 7, 183)], color=COLORS["known_stroke"], sw=1.9, head=8))
    s.append(arrow([(unknown[0] + unknown[2], unknown[1] + unknown[3]/2), (ds_x - 7, 330)], color=COLORS["unknown_stroke"], sw=1.9, head=8))
    s.append(arrow([(unknown[0] + unknown[2], unknown[1] + unknown[3]/2), (ds_x - 7, 477)], color=COLORS["unknown_stroke"], sw=1.9, head=8))

    s.append("</svg>\n")
    return "".join(s)


def convert(svg_path: Path, pdf_path: Path, png_path: Path) -> None:
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
    cairosvg.svg2png(url=str(svg_path), write_to=str(png_path))
    print(f"Wrote: {pdf_path}")
    print(f"Wrote: {png_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", default="papers/milcom2026/figures/hero_figure")
    parser.add_argument("--name", default="hero_dqnguard_pipeline_s4_horizontal")
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
        convert(svg_path, pdf_path, png_path)


if __name__ == "__main__":
    main()
