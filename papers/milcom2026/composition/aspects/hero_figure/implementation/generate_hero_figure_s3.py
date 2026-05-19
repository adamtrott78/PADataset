#!/usr/bin/env python3
"""
Generate Hero Figure Candidate S3.

Creates two deterministic SVG/PDF/PNG candidates:
  1. hero_dqnguard_pipeline_s3_horizontal
  2. hero_dqnguard_pipeline_s3_vertical

S3 implements requested fine-tuning:
  - four arrows from OTA RF Window to IQ / FFT / DCT / Polar;
  - fusion block labeled concatenation + adaptive average pooling to 8192;
  - four backbone output metrics;
  - each metric points into DQNGuard;
  - cleaner colors and branch semantics;
  - smaller/safer text;
  - math-style rendering for variables/equations;
  - horizontal and vertical variants.
"""

from __future__ import annotations

import argparse
import html
import math
import shutil
import subprocess
from pathlib import Path


COLORS = {
    "bg": "#ffffff",
    "ink": "#1f2933",
    "muted": "#4b5563",
    "line": "#4b5563",

    # Neutral upstream evidence path
    "obs_panel": "#f1f3f5",
    "backbone_panel": "#e3e8f0",
    "transform_box": "#f8fafc",
    "fusion_box": "#edf2f7",
    "metric_box": "#f8fafc",

    # DQNGuard decision layer
    "guard_panel": "#bcd3e8",
    "guard_stage": "#dcecff",
    "guard_stroke": "#2f5f89",

    # Outputs
    "known_fill": "#dcefd7",
    "known_stroke": "#4f7c52",
    "unknown_fill": "#fff1cc",
    "unknown_stroke": "#b7791f",

    # Downstream context
    "downstream_fill": "#eee5f4",
    "downstream_stroke": "#7a5c84",
    "llm_fill": "#eeeeee",
    "llm_stroke": "#707070",
    "qrcwos_fill": "#dcefe5",
    "qrcwos_stroke": "#5a7868",
}


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def svg_header(width_px: int, height_px: int, width_in: float, height_in: float, label: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width_in}in" height="{height_in}in" '
        f'viewBox="0 0 {width_px} {height_px}" role="img" aria-label="{esc(label)}">\n'
        f'<rect x="0" y="0" width="{width_px}" height="{height_px}" fill="{COLORS["bg"]}"/>\n'
        '<style>\n'
        '  text { font-family: Helvetica, Arial, sans-serif; fill: #1f2933; }\n'
        '  .paneltitle { font-size: 30px; font-weight: 700; }\n'
        '  .subtitle { font-size: 19px; fill: #374151; }\n'
        '  .label { font-size: 23px; font-weight: 500; }\n'
        '  .detail { font-size: 18px; fill: #2f3742; }\n'
        '  .small { font-size: 16px; fill: #384252; }\n'
        '  .num { font-size: 27px; font-weight: 700; }\n'
        '  .math { font-family: "Times New Roman", Times, serif; font-size: 18px; font-style: italic; fill: #1f2933; }\n'
        '  .mathsmall { font-family: "Times New Roman", Times, serif; font-size: 16px; font-style: italic; fill: #1f2933; }\n'
        '</style>\n'
    )


def rect(x, y, w, h, fill, stroke=None, sw=2.3, rx=13) -> str:
    stroke = stroke or COLORS["line"]
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" ry="{rx}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>\n'
    )


def text(x, y, s, cls="label", anchor="middle") -> str:
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" class="{cls}">{esc(s)}</text>\n'


def lines(x, y, items, cls="detail", line_h=21, anchor="middle") -> str:
    out = [f'<text x="{x}" y="{y}" text-anchor="{anchor}" class="{cls}">\n']
    for i, item in enumerate(items):
        dy = 0 if i == 0 else line_h
        if isinstance(item, tuple):
            s, item_cls = item
            out.append(f'  <tspan x="{x}" dy="{dy}" class="{item_cls}">{esc(s)}</tspan>\n')
        else:
            out.append(f'  <tspan x="{x}" dy="{dy}">{esc(item)}</tspan>\n')
    out.append('</text>\n')
    return "".join(out)


def box_text(x, y, w, h, fill, title, details=None, stroke=None, title_cls="label", detail_cls="small", rx=12, sw=2.2) -> str:
    details = details or []
    out = rect(x, y, w, h, fill, stroke=stroke, sw=sw, rx=rx)
    if details:
        out += lines(x + w / 2, y + h * 0.34, [title], cls=title_cls, line_h=20)
        out += lines(x + w / 2, y + h * 0.57, details, cls=detail_cls, line_h=20)
    else:
        out += text(x + w / 2, y + h * 0.55, title, cls=title_cls)
    return out


def arrow(points, color=None, sw=2.5, head=11.0) -> str:
    color = color or COLORS["line"]
    if len(points) < 2:
        return ""
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

    pts = f"{x2},{y2} {bx + px},{by + py} {bx - px},{by - py}"
    out += f'<polygon points="{pts}" fill="{color}" stroke="{color}" stroke-width="0"/>\n'
    return out


def simple_line(points, color=None, sw=1.8) -> str:
    color = color or COLORS["line"]
    pts = " ".join(f"{x},{y}" for x, y in points)
    return (
        f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{sw}" '
        f'stroke-linecap="round" stroke-linejoin="round"/>\n'
    )


def build_horizontal() -> str:
    W, H = 2130, 670
    s = [svg_header(W, H, 7.1, 2.23, "DQNGuard horizontal evidence-flow hero figure")]

    # Panels
    obs = (22, 28, 300, 580)
    back = (348, 28, 720, 580)
    guard = (1092, 28, 470, 580)
    out = (1585, 28, 520, 580)

    ox, oy, ow, oh = obs
    bx, by, bw, bh = back
    gx, gy, gw, gh = guard
    rx, ry, rw, rh = out

    s.append(rect(*obs, fill=COLORS["obs_panel"], sw=2.7, rx=18))
    s.append(rect(*back, fill=COLORS["backbone_panel"], sw=2.7, rx=18))
    s.append(rect(*guard, fill=COLORS["guard_panel"], sw=2.9, rx=18))

    s.append(text(ox + ow/2, 70, "OTA RF Observation", "paneltitle"))
    s.append(text(bx + bw/2, 70, "PA Backbone", "paneltitle"))
    s.append(text(gx + gw/2, 66, "DQNGuard", "paneltitle"))
    s.append(text(gx + gw/2, 98, "budgeted open-set decision layer", "subtitle"))
    s.append(lines(rx + rw/2, 67, ["Outputs and", "Downstream Use"], "paneltitle", line_h=33))

    # Observation window
    win = (58, 280, 230, 96)
    s.append(box_text(
        *win, fill=COLORS["transform_box"], title="OTA RF Window",
        details=["complex IQ window"], detail_cls="small", rx=12
    ))

    # Four representations
    reps = [
        ("Original IQ", "I/Q samples"),
        ("FFT", "frequency domain"),
        ("DCT", "cosine domain"),
        ("Polar", "magnitude / phase"),
    ]
    rep_x, rep_w, rep_h = 372, 135, 62
    rep_ys = [150, 235, 320, 405]
    for (title, detail), y in zip(reps, rep_ys):
        s.append(box_text(rep_x, y, rep_w, rep_h, COLORS["transform_box"], title, [detail], title_cls="small", detail_cls="small", rx=10, sw=2.0))
        s.append(arrow([(win[0] + win[2], win[1] + win[3]/2), (rep_x - 8, y + rep_h/2)], sw=2.0, head=8))

    # Fusion
    fusion = (548, 275, 190, 120)
    s.append(box_text(
        *fusion, fill=COLORS["fusion_box"], title="fusion",
        details=["concatenate", "adaptive avg pool", ("N = 8192", "mathsmall")],
        title_cls="label", detail_cls="small", rx=12
    ))
    for y in rep_ys:
        s.append(arrow([(rep_x + rep_w, y + rep_h/2), (fusion[0] - 8, fusion[1] + fusion[3]/2)], sw=2.0, head=8))

    # Metrics / evidence outputs
    metrics = [
        ("closed-set", ("logits z", "mathsmall")),
        ("softmax", ("p", "mathsmall")),
        ("feature", ("h", "mathsmall")),
        ("predicted PA", ("ŷ", "mathsmall")),
    ]
    met_x, met_w, met_h = 790, 190, 72
    met_ys = [145, 240, 335, 430]
    for (title, detail), y in zip(metrics, met_ys):
        s.append(box_text(met_x, y, met_w, met_h, COLORS["metric_box"], title, [detail], title_cls="small", detail_cls="mathsmall", rx=10, sw=2.0))
        s.append(arrow([(fusion[0] + fusion[2], fusion[1] + fusion[3]/2), (met_x - 7, y + met_h/2)], sw=2.0, head=8))
        s.append(arrow([(met_x + met_w, y + met_h/2), (gx - 8, y + met_h/2)], sw=2.0, head=8))

    # DQNGuard stages
    stage_x, stage_w, stage_h = gx + 25, gw - 50, 120
    stages = [
        (130, "1", "Predicted-class calibration", ["select bands for ŷ"]),
        (280, "2", "Guard evidence", [("P₁, P₁ − P₂, H", "mathsmall"), ("V, E, r(x)", "mathsmall")]),
        (430, "3", "Known-budget threshold", [("r(x) ≥ τβ", "mathsmall"), ("β = 0.05", "mathsmall")]),
    ]
    for y, num, title, detail in stages:
        s.append(rect(stage_x, y, stage_w, stage_h, COLORS["guard_stage"], stroke=COLORS["guard_stroke"], sw=2.3, rx=12))
        s.append(text(stage_x + 30, y + 50, num, "num"))
        s.append(text(stage_x + stage_w/2 + 18, y + 39, title, "label"))
        s.append(lines(stage_x + stage_w/2 + 18, y + 72, detail, "small", line_h=20))

    # Outputs
    known = (1600, 160, 230, 118)
    unknown = (1600, 374, 230, 118)

    s.append(box_text(
        *known, fill=COLORS["known_fill"], stroke=COLORS["known_stroke"],
        title="Known PA evidence", details=["Scan / Burst /", "Sustain / Hop / Replay"],
        title_cls="label", detail_cls="small", rx=12
    ))
    s.append(box_text(
        *unknown, fill=COLORS["unknown_fill"], stroke=COLORS["unknown_stroke"],
        title="Unknown behavior pool", details=["candidate novel", "signal behavior"],
        title_cls="detail", detail_cls="small", rx=12
    ))

    ds_x, ds_w, ds_h = 1880, 210, 88
    s.append(box_text(ds_x, 140, ds_w, ds_h, COLORS["downstream_fill"], "ATT&CK/EW", ["precursor hypotheses"], stroke=COLORS["downstream_stroke"], title_cls="detail", detail_cls="small", rx=11))
    s.append(box_text(ds_x, 292, ds_w, ds_h, COLORS["llm_fill"], "LLM-assisted", ["label-making"], stroke=COLORS["llm_stroke"], title_cls="detail", detail_cls="small", rx=11))
    s.append(box_text(ds_x, 444, ds_w, ds_h, COLORS["qrcwos_fill"], "QR-CWoS", ["response planning"], stroke=COLORS["qrcwos_stroke"], title_cls="detail", detail_cls="small", rx=11))

    # Decision arrows: only branch paths are colored.
    s.append(arrow([(gx + gw, 245), (known[0] - 8, known[1] + known[3]/2)], color=COLORS["known_stroke"], sw=2.4, head=10))
    s.append(arrow([(gx + gw, 400), (unknown[0] - 8, unknown[1] + unknown[3]/2)], color=COLORS["unknown_stroke"], sw=2.4, head=10))

    s.append(arrow([(known[0] + known[2], known[1] + known[3]/2), (ds_x - 8, 184)], color=COLORS["known_stroke"], sw=2.1, head=9))
    s.append(arrow([(unknown[0] + unknown[2], unknown[1] + unknown[3]/2), (ds_x - 8, 336)], color=COLORS["unknown_stroke"], sw=2.1, head=9))
    s.append(arrow([(unknown[0] + unknown[2], unknown[1] + unknown[3]/2), (ds_x - 8, 488)], color=COLORS["unknown_stroke"], sw=2.1, head=9))

    s.append("</svg>\n")
    return "".join(s)


def build_vertical() -> str:
    W, H = 1050, 1780
    s = [svg_header(W, H, 3.5, 5.93, "DQNGuard vertical evidence-flow hero figure")]

    # Top title panels are stacked vertically.
    x0, panel_w = 70, 910

    s.append(text(W/2, 60, "DQNGuard RF Preliminary-Action Evidence Flow", "paneltitle"))

    # Observation
    s.append(rect(x0, 95, panel_w, 160, COLORS["obs_panel"], sw=2.7, rx=18))
    s.append(text(W/2, 135, "OTA RF Observation", "paneltitle"))
    win = (355, 165, 340, 62)
    s.append(box_text(*win, COLORS["transform_box"], "OTA RF Window", ["complex IQ window"], rx=10))

    # Representation block
    s.append(rect(x0, 300, panel_w, 330, COLORS["backbone_panel"], sw=2.7, rx=18))
    s.append(text(W/2, 340, "PA Backbone", "paneltitle"))

    reps = [
        ("Original IQ", "I/Q samples"),
        ("FFT", "frequency domain"),
        ("DCT", "cosine domain"),
        ("Polar", "magnitude / phase"),
    ]
    rep_xs = [120, 335, 550, 765]
    rep_y, rep_w, rep_h = 385, 160, 70
    for (title, detail), x in zip(reps, rep_xs):
        s.append(box_text(x, rep_y, rep_w, rep_h, COLORS["transform_box"], title, [detail], title_cls="small", detail_cls="small", rx=10))
        s.append(arrow([(W/2, win[1] + win[3]), (x + rep_w/2, rep_y - 8)], sw=1.9, head=8))

    fusion = (360, 505, 330, 82)
    s.append(box_text(
        *fusion, COLORS["fusion_box"], "fusion",
        ["concatenate + adaptive average pooling", ("N = 8192", "mathsmall")],
        title_cls="label", detail_cls="small", rx=11
    ))
    for x in rep_xs:
        s.append(arrow([(x + rep_w/2, rep_y + rep_h), (fusion[0] + fusion[2]/2, fusion[1] - 8)], sw=1.9, head=8))

    # Metrics row
    metrics = [
        ("logits", ("z", "mathsmall")),
        ("softmax", ("p", "mathsmall")),
        ("feature", ("h", "mathsmall")),
        ("predicted PA", ("ŷ", "mathsmall")),
    ]
    met_xs = [120, 335, 550, 765]
    met_y, met_w, met_h = 675, 160, 70
    for (title, detail), x in zip(metrics, met_xs):
        s.append(box_text(x, met_y, met_w, met_h, COLORS["metric_box"], title, [detail], title_cls="small", detail_cls="mathsmall", rx=10))
        s.append(arrow([(fusion[0] + fusion[2]/2, fusion[1] + fusion[3]), (x + met_w/2, met_y - 8)], sw=1.9, head=8))

    # DQNGuard
    guard = (x0, 790, panel_w, 440)
    gx, gy, gw, gh = guard
    s.append(rect(*guard, COLORS["guard_panel"], sw=2.9, rx=18))
    s.append(text(W/2, gy + 42, "DQNGuard", "paneltitle"))
    s.append(text(W/2, gy + 75, "budgeted open-set decision layer", "subtitle"))

    stage_w, stage_h = 770, 86
    stage_x = (W - stage_w) / 2
    stage_ys = [900, 1005, 1110]
    stages = [
        ("1", "Predicted-class calibration", ["select bands for ŷ"]),
        ("2", "Guard evidence", [("P₁, P₁ − P₂, H", "mathsmall"), ("V, E, r(x)", "mathsmall")]),
        ("3", "Known-budget threshold", [("r(x) ≥ τβ", "mathsmall"), ("β = 0.05", "mathsmall")]),
    ]
    for y, (num, title, detail) in zip(stage_ys, stages):
        s.append(rect(stage_x, y, stage_w, stage_h, COLORS["guard_stage"], stroke=COLORS["guard_stroke"], sw=2.3, rx=12))
        s.append(text(stage_x + 35, y + 52, num, "num"))
        s.append(text(W/2 + 20, y + 33, title, "label"))
        s.append(lines(W/2 + 20, y + 58, detail, "small", line_h=19))

    for x in met_xs:
        s.append(arrow([(x + met_w/2, met_y + met_h), (W/2, gy - 8)], sw=1.9, head=8))

    # Outputs
    known = (105, 1280, 380, 105)
    unknown = (565, 1280, 380, 105)
    s.append(box_text(*known, COLORS["known_fill"], "Known PA evidence", ["Scan / Burst / Sustain / Hop / Replay"], stroke=COLORS["known_stroke"], title_cls="label", detail_cls="small", rx=12))
    s.append(box_text(*unknown, COLORS["unknown_fill"], "Unknown behavior pool", ["candidate novel signal behavior"], stroke=COLORS["unknown_stroke"], title_cls="label", detail_cls="small", rx=12))

    s.append(arrow([(W/2, gy + gh), (known[0] + known[2]/2, known[1] - 8)], color=COLORS["known_stroke"], sw=2.2, head=9))
    s.append(arrow([(W/2, gy + gh), (unknown[0] + unknown[2]/2, unknown[1] - 8)], color=COLORS["unknown_stroke"], sw=2.2, head=9))

    # Downstream
    ds_y = 1445
    ds = [
        (105, "ATT&CK/EW", ["precursor hypotheses"], COLORS["downstream_fill"], COLORS["downstream_stroke"]),
        (365, "LLM-assisted", ["label-making"], COLORS["llm_fill"], COLORS["llm_stroke"]),
        (625, "QR-CWoS", ["response planning"], COLORS["qrcwos_fill"], COLORS["qrcwos_stroke"]),
    ]
    for x, title, detail, fill, stroke in ds:
        s.append(box_text(x, ds_y, 320, 92, fill, title, detail, stroke=stroke, title_cls="detail", detail_cls="small", rx=11))

    s.append(arrow([(known[0] + known[2]/2, known[1] + known[3]), (105 + 160, ds_y - 8)], color=COLORS["known_stroke"], sw=2.0, head=8))
    s.append(arrow([(unknown[0] + unknown[2]/2, unknown[1] + unknown[3]), (365 + 160, ds_y - 8)], color=COLORS["unknown_stroke"], sw=2.0, head=8))
    s.append(arrow([(unknown[0] + unknown[2]/2, unknown[1] + unknown[3]), (625 + 160, ds_y - 8)], color=COLORS["unknown_stroke"], sw=2.0, head=8))

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


def write_one(outdir: Path, name: str, svg: str, no_convert: bool) -> None:
    svg_path = outdir / f"{name}.svg"
    pdf_path = outdir / f"{name}.pdf"
    png_path = outdir / f"{name}.png"

    svg_path.write_text(svg, encoding="utf-8")
    print(f"Wrote: {svg_path}")

    if not no_convert:
        convert(svg_path, pdf_path, png_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", default="papers/milcom2026/figures/hero_figure")
    parser.add_argument("--no-convert", action="store_true")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    write_one(outdir, "hero_dqnguard_pipeline_s3_horizontal", build_horizontal(), args.no_convert)
    write_one(outdir, "hero_dqnguard_pipeline_s3_vertical", build_vertical(), args.no_convert)


if __name__ == "__main__":
    main()
