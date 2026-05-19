#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <input.pdf> <paper_key> [dpi]"
  echo "Example: $0 refs/baye_varmax.pdf 2024_baye_varmax 160"
  exit 1
fi

PDF="$1"
KEY="$2"
DPI="${3:-160}"

OUT="papers/milcom2026/reference_notes/layout_screenshots/$KEY"
mkdir -p "$OUT"

tmp_prefix="$OUT/page_tmp"

echo "Rendering $PDF -> $OUT at ${DPI} dpi"
pdftoppm -png -r "$DPI" "$PDF" "$tmp_prefix"

i=1
for f in "$OUT"/page_tmp-*.png; do
  printf -v new "$OUT/page_%03d.png" "$i"
  mv "$f" "$new"
  i=$((i+1))
done

echo "Creating contact sheet"
montage "$OUT"/page_*.png \
  -thumbnail 350x \
  -tile 2x \
  -geometry +20+20 \
  "$OUT/contact_sheet.png"

echo "Done:"
echo "  $OUT/page_###.png"
echo "  $OUT/contact_sheet.png"
