#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def natural_page_key(path: Path):
    stem = path.stem
    tail = stem.split("-")[-1]
    try:
        return int(tail)
    except ValueError:
        return stem


def main() -> None:
    ap = argparse.ArgumentParser(description="Create a contact sheet from rendered PDF page PNGs.")
    ap.add_argument("--page-dir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--title", default="")
    ap.add_argument("--cols", type=int, default=3)
    ap.add_argument("--thumb-width", type=int, default=900)
    ap.add_argument("--pad", type=int, default=30)
    args = ap.parse_args()

    page_paths = sorted(args.page_dir.glob("*.png"), key=natural_page_key)
    if not page_paths:
        raise SystemExit(f"No PNG pages found in {args.page_dir}")

    try:
        font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
        font_label = ImageFont.truetype("DejaVuSans.ttf", 24)
    except Exception:
        font_title = ImageFont.load_default()
        font_label = ImageFont.load_default()

    thumbs = []
    for p in page_paths:
        im = Image.open(p).convert("RGB")
        scale = args.thumb_width / im.width
        new_size = (args.thumb_width, max(1, int(im.height * scale)))
        im = im.resize(new_size, Image.LANCZOS)
        thumbs.append((p, im))

    cols = max(1, args.cols)
    rows = math.ceil(len(thumbs) / cols)

    label_h = 42
    title_h = 70 if args.title else 0
    cell_w = args.thumb_width + args.pad * 2
    cell_h = max(im.height for _, im in thumbs) + label_h + args.pad * 2

    out_w = cols * cell_w
    out_h = title_h + rows * cell_h

    sheet = Image.new("RGB", (out_w, out_h), "white")
    draw = ImageDraw.Draw(sheet)

    y0 = 0
    if args.title:
        draw.text((args.pad, 18), args.title, fill="black", font=font_title)
        y0 = title_h

    for idx, (p, im) in enumerate(thumbs):
        r = idx // cols
        c = idx % cols
        x = c * cell_w + args.pad
        y = y0 + r * cell_h + args.pad
        sheet.paste(im, (x, y))
        draw.text((x, y + im.height + 8), p.name, fill="black", font=font_label)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.out)
    print(f"Wrote contact sheet: {args.out}")


if __name__ == "__main__":
    main()
