#!/usr/bin/env python3
"""
Generate Hero Figure Candidate S13.

S13 is a subtitle-color and compact-title repair of S12:
  - formal panel names;
  - cleaner font stack;
  - shorter labels;
  - reordered metrics: y-hat, z, p, h;
  - predicted PA routes cleanly to calibration stage;
  - z/p/h route to guard-evidence stage;
  - stronger output panel;
  - scarlet unknown branch;
  - cleaner arrow geometry.
"""

from __future__ import annotations

import argparse
import html
import math
import shutil
import subprocess
from pathlib import Path


W, H = 2130, 640

COLORS = {
    "bg": "#ffffff",
    "ink": "#18212b",
    "line": "#46515e",

    "input_panel": "#f3f4f6",
    "encoder_panel": "#e6ebf3",
    "guard_panel": "#b9d2e7",
    "output_panel": "#f1f0eb",

    "box": "#fbfcfe",
    "fusion": "#eef3f8",
    "model": "#eaf2fb",
    "stage": "#ddecff",

    "guard_stroke": "#2f638f",

    "known_fill": "#dcefd7",
    "known_stroke": "#3f7a46",

    "unknown_fill": "#f9deda",
    "unknown_stroke": "#b23a3a",

    "attack_fill": "#eee2f4",
    "attack_stroke": "#7a5c84",
    "llm_fill": "#eeeeee",
    "llm_stroke": "#707070",
    "qrcwos_fill": "#dcefe5",
    "qrcwos_stroke": "#5a7868",
}


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def header() -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="7.1in" height="2.13in" '
        f'viewBox="0 0 {W} {H}" role="img" aria-label="DQNGuard RF open-set recognition pipeline">\n'
        f'<rect x="0" y="0" width="{W}" height="{H}" fill="{COLORS["bg"]}"/>\n'
        '<style>\n'
        '  text { font-family: "Liberation Sans", Arial, Helvetica, "DejaVu Sans", sans-serif; fill: #18212b; }\n'
        '  .paneltitle { font-size: 25px; font-weight: 700; letter-spacing: 0px; }\n'
        '  .subtitle { font-size: 16.5px; font-weight: 500; fill: #18212b; }\\n'
        '  .label { font-size: 20px; font-weight: 700; fill: #18212b; }\\n'
        '  .compacttitle { font-size: 16.5px; font-weight: 700; fill: #18212b; }\\n'
        '  .detail { font-size: 18px; font-weight: 650; fill: #18212b; }\\n'
        '  .small { font-size: 15.8px; font-weight: 500; fill: #18212b; }\\n'
        '  .tiny { font-size: 14.8px; font-weight: 500; fill: #18212b; }\\n'
        '  .num { font-size: 22px; font-weight: 700; }\n'
        '  .math { font-family: "Liberation Serif", "Times New Roman", Times, serif; font-size: 19px; font-style: italic; font-weight: 700; fill: #18212b; }\n'
        '  .mathtiny { font-family: "Liberation Serif", "Times New Roman", Times, serif; font-size: 18.5px; font-style: italic; font-weight: 700; fill: #18212b; }\\n'
        '</style>\n'
    )


def rect(x, y, w, h, fill, stroke=None, sw=2.0, rx=10) -> str:
    stroke = stroke or COLORS["line"]
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" ry="{rx}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>\n'
    )


def text(x, y, s, cls="label", anchor="middle") -> str:
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" class="{cls}">{esc(s)}</text>\n'


def lines(x, y, items, cls="detail", line_h=18, anchor="middle") -> str:
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


def box(x, y, w, h, fill, title, details=None, stroke=None, title_cls="label", detail_cls="small", rx=9, sw=1.8) -> str:
    details = details or []
    out = rect(x, y, w, h, fill, stroke=stroke, sw=sw, rx=rx)
    if details:
        out += lines(x + w / 2, y + h * 0.38, [title], cls=title_cls, line_h=17)
        out += lines(x + w / 2, y + h * 0.64, details, cls=detail_cls, line_h=17)
    else:
        out += text(x + w / 2, y + h * 0.58, title, cls=title_cls)
    return out


def arrow(points, color=None, sw=2.0, head=8.0) -> str:
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

    # Panel geometry
    input_panel = (24, 32, 270, 540)
    encoder_panel = (315, 32, 720, 540)
    guard_panel = (1058, 32, 470, 540)
    output_panel = (1550, 32, 555, 540)

    ix, iy, iw, ih = input_panel
    ex, ey, ew, eh = encoder_panel
    gx, gy, gw, gh = guard_panel
    ox, oy, ow, oh = output_panel

    s.append(rect(*input_panel, fill=COLORS["input_panel"], sw=2.5, rx=15))
    s.append(rect(*encoder_panel, fill=COLORS["encoder_panel"], sw=2.5, rx=15))
    s.append(rect(*guard_panel, fill=COLORS["guard_panel"], sw=2.7, rx=15))
    s.append(rect(*output_panel, fill=COLORS["output_panel"], stroke="#b9b7ae", sw=1.8, rx=15))

    s.append(text(ix + iw / 2, 70, "RF Signal Input", "paneltitle"))
    s.append(text(ex + ew / 2, 70, "Multi-Domain PA Encoder", "paneltitle"))
    s.append(text(gx + gw / 2, 68, "DQNGuard", "paneltitle"))
    s.append(text(gx + gw / 2, 96, "budgeted open-set decision layer", "subtitle"))
    s.append(lines(ox + ow / 2, 66, ["Evidence Outputs", "and Consumers"], "paneltitle", line_h=28))

    # RF window
    win = (58, 270, 200, 82)
    s.append(box(*win, fill=COLORS["box"], title="RF Window", details=["complex IQ"], detail_cls="small", rx=9))

    # Transform boxes
    trans_x, trans_w, trans_h = 335, 110, 50
    trans_ys = [137, 215, 293, 371]
    transforms = ["IQ", "FFT", "DCT", "Polar"]

    for label, y in zip(transforms, trans_ys):
        s.append(box(trans_x, y, trans_w, trans_h, COLORS["box"], label, [], title_cls="label", rx=8, sw=1.7))
        s.append(arrow([(win[0] + win[2], win[1] + win[3] / 2), (trans_x, y + trans_h / 2)], sw=1.65, head=6.5))

    # Fusion and model
    fusion = (490, 247, 145, 104)
    model = (675, 247, 128, 104)

    s.append(box(
        *fusion,
        fill=COLORS["fusion"],
        title="Concat + AvgPool",
        details=[("N = 8192", "mathtiny")],
        title_cls="compacttitle",
        detail_cls="mathtiny",
        rx=9,
        sw=1.8,
    ))

    s.append(box(
        *model,
        fill=COLORS["model"],
        title="PA CNN",
        details=["encoder + head"],
        title_cls="label",
        detail_cls="small",
        rx=9,
        sw=1.8,
    ))

    for y in trans_ys:
        s.append(arrow([(trans_x + trans_w, y + trans_h / 2), (fusion[0], fusion[1] + fusion[3] / 2)], sw=1.65, head=6.5))

    s.append(arrow([(fusion[0] + fusion[2], fusion[1] + fusion[3] / 2), (model[0], model[1] + model[3] / 2)], sw=1.8, head=7))

    # Metrics ordered for clean routing: yhat, z, p, h.
    # Inline styles force readable text and math-like variables.
    metric_x, metric_w, metric_h = 812, 205, 76
    metric_ys = [106, 200, 294, 388]
    metrics = [
        ("predicted PA", "ŷ"),
        ("logits", "z"),
        ("softmax", "p"),
        ("feature", "h"),
    ]

    for (name, var), y in zip(metrics, metric_ys):
        s.append(rect(metric_x, y, metric_w, metric_h, COLORS["box"], sw=1.8, rx=8))
        s.append(
            f'<text x="{metric_x + metric_w / 2}" y="{y + 28}" text-anchor="middle" '
            f'style="font-family: Liberation Sans, Arial, Helvetica, sans-serif; '
            f'font-size: 20px; font-weight: 700; fill: #18212b;">{esc(name)}</text>\n'
        )
        s.append(
            f'<text x="{metric_x + metric_w / 2}" y="{y + 56}" text-anchor="middle" '
            f'style="font-family: Liberation Serif, Times New Roman, Times, serif; '
            f'font-size: 24px; font-style: italic; font-weight: 700; fill: #18212b;">{esc(var)}</text>\n'
        )
        s.append(arrow([(model[0] + model[2], model[1] + model[3] / 2), (metric_x, y + metric_h / 2)], sw=1.55, head=6.2))

    # DQNGuard stages
    stage_x = gx + 24
    stage_w = gw - 48
    stage_h = 101
    stage1 = (stage_x, 124, stage_w, stage_h)
    stage2 = (stage_x, 265, stage_w, stage_h)
    stage3 = (stage_x, 406, stage_w, stage_h)

    stages = [
        (stage1, "1", "Predicted-class calibration", ["select bands for ŷ"]),
        (stage2, "2", "Guard evidence", [("P₁, P₁ − P₂, H", "mathtiny"), ("V, E, r(x)", "mathtiny")]),
        (stage3, "3", "Known-budget threshold", [("r(x) ≥ τβ", "mathtiny"), ("β = 0.05", "mathtiny")]),
    ]

    for (x, y, w, h), num, title, detail in stages:
        s.append(rect(x, y, w, h, COLORS["stage"], stroke=COLORS["guard_stroke"], sw=2.0, rx=10))
        s.append(text(x + 28, y + 45, num, "num"))
        s.append(text(x + w / 2 + 18, y + 34, title, "label"))
        s.append(lines(x + w / 2 + 18, y + 64, detail, "small", line_h=18))

    # Subtle internal cascade arrows.
    mid_x = gx + gw / 2
    s.append(arrow([(mid_x, stage1[1] + stage1[3] + 5), (mid_x, stage2[1])], color=COLORS["guard_stroke"], sw=1.4, head=6.2))
    s.append(arrow([(mid_x, stage2[1] + stage2[3] + 5), (mid_x, stage3[1])], color=COLORS["guard_stroke"], sw=1.4, head=6.2))

    # Metric routing.
    # yhat -> stage 1
    yhat_y = metric_ys[0] + metric_h / 2
    z_y = metric_ys[1] + metric_h / 2
    p_y = metric_ys[2] + metric_h / 2
    h_y = metric_ys[3] + metric_h / 2

    # Arrow tips terminate exactly on the left edge of the DQNGuard stage boxes.
    s.append(arrow([(metric_x + metric_w, yhat_y), (stage1[0], stage1[1] + stage1[3] / 2)], sw=1.9, head=7))

    # z, p, h -> stage 2. Use separate landing heights to avoid one thick bundle.
    stage2_targets = [stage2[1] + 28, stage2[1] + stage2[3] / 2, stage2[1] + stage2[3] - 28]
    for src_y, tgt_y in zip([z_y, p_y, h_y], stage2_targets):
        s.append(arrow([(metric_x + metric_w, src_y), (stage2[0], tgt_y)], sw=1.75, head=6.5))

    # Outputs
    known = (1578, 148, 228, 96)
    unknown = (1578, 376, 228, 96)

    s.append(box(
        *known,
        fill=COLORS["known_fill"],
        stroke=COLORS["known_stroke"],
        title="Known PA evidence",
        details=["Scan / Burst /", "Sustain / Hop / Replay"],
        title_cls="label",
        detail_cls="tiny",
        rx=10,
        sw=1.9,
    ))

    s.append(box(
        *unknown,
        fill=COLORS["unknown_fill"],
        stroke=COLORS["unknown_stroke"],
        title="Unknown behavior pool",
        details=["candidate novel", "signal behavior"],
        title_cls="label",
        detail_cls="tiny",
        rx=10,
        sw=1.9,
    ))

    # Downstream consumers
    ds_x, ds_w, ds_h = 1842, 220, 82
    attack = (ds_x, 132, ds_w, ds_h)
    llm = (ds_x, 279, ds_w, ds_h)
    qrcwos = (ds_x, 426, ds_w, ds_h)

    s.append(box(*attack, COLORS["attack_fill"], "ATT&CK/EW", ["precursor hypotheses"], stroke=COLORS["attack_stroke"], title_cls="label", detail_cls="tiny", rx=9, sw=1.8))
    s.append(box(*llm, COLORS["llm_fill"], "LLM-assisted", ["label-making"], stroke=COLORS["llm_stroke"], title_cls="label", detail_cls="tiny", rx=9, sw=1.8))
    s.append(box(*qrcwos, COLORS["qrcwos_fill"], "QR-CWoS", ["response planning"], stroke=COLORS["qrcwos_stroke"], title_cls="label", detail_cls="tiny", rx=9, sw=1.8))

    # DQNGuard decision branch arrows.
    s.append(arrow([(gx + gw, stage2[1] - 20), (known[0], known[1] + known[3] / 2)], color=COLORS["known_stroke"], sw=1.9, head=7.5))
    s.append(arrow([(gx + gw, stage3[1] + 15), (unknown[0], unknown[1] + unknown[3] / 2)], color=COLORS["unknown_stroke"], sw=1.9, head=7.5))

    # Consumer arrows land exactly on left boundaries.
    s.append(arrow([(known[0] + known[2], known[1] + known[3] / 2), (attack[0], attack[1] + attack[3] / 2)], color=COLORS["known_stroke"], sw=1.65, head=6.5))
    s.append(arrow([(unknown[0] + unknown[2], unknown[1] + unknown[3] / 2), (llm[0], llm[1] + llm[3] / 2)], color=COLORS["unknown_stroke"], sw=1.65, head=6.5))
    s.append(arrow([(unknown[0] + unknown[2], unknown[1] + unknown[3] / 2), (qrcwos[0], qrcwos[1] + qrcwos[3] / 2)], color=COLORS["unknown_stroke"], sw=1.65, head=6.5))

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
    parser.add_argument("--name", default="hero_dqnguard_pipeline_s13_horizontal")
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
