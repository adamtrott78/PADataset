#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
REF_ROOT="$ROOT/papers/milcom2026/reference_notes"
STAGING="$REF_ROOT/staging"
LIBRARY="$REF_ROOT/papers"
EXPORT_ROOT="${REFERENCE_EXPORT_ROOT:-$HOME/adamArchives/reference_paper_exports}"
DPI="${DPI:-220}"
CONTACT_COLS="${CONTACT_COLS:-3}"
THUMB_WIDTH="${THUMB_WIDTH:-900}"
MOVE_INPUTS=0
SINGLE_SLUG=""

usage() {
  cat <<'EOF'
Usage:
  bash papers/milcom2026/tools/process_reference_papers.sh [options]

Options:
  --staging PATH       Folder containing PDFs to process.
  --slug SLUG          Force slug for a single staged PDF. Example: wei or wei2.
  --move              Move PDFs out of staging instead of copying.
  --dpi N             Render DPI for page PNGs. Default: 220.
  --help              Show this help.

Mathpix:
  If MATHPIX_CMD is set, it will be used to create the markdown file.

  MATHPIX_CMD must use placeholders:
    {pdf} for the input PDF path
    {out} for the output Markdown path

  Example:
    MATHPIX_CMD='mathpix convert "{pdf}" --format md --output "{out}"' bash papers/milcom2026/tools/process_reference_papers.sh

If MATHPIX_CMD is not set, the script still creates page images, contact sheets, manifests, and bundles.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --staging)
      STAGING="$2"
      shift 2
      ;;
    --slug)
      SINGLE_SLUG="$2"
      shift 2
      ;;
    --move)
      MOVE_INPUTS=1
      shift
      ;;
    --dpi)
      DPI="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    echo "Install suggestion: sudo apt install -y poppler-utils zip" >&2
    exit 1
  }
}

need_cmd pdftoppm
need_cmd pdfinfo
need_cmd zip
need_cmd python3

python3 - <<'PY'
try:
    import PIL
except Exception:
    raise SystemExit("Missing Python package Pillow. Install with: python -m pip install pillow")
PY

mkdir -p "$STAGING" "$LIBRARY" "$EXPORT_ROOT"

mapfile -t PDFS < <(find "$STAGING" -maxdepth 1 -type f \( -iname '*.pdf' \) | sort)

if [[ "${#PDFS[@]}" -eq 0 ]]; then
  echo "No PDFs found in staging folder: $STAGING"
  echo "Drop PDFs there, then rerun this script."
  exit 0
fi

if [[ -n "$SINGLE_SLUG" && "${#PDFS[@]}" -ne 1 ]]; then
  echo "--slug can only be used when exactly one PDF is in staging." >&2
  echo "Found ${#PDFS[@]} PDFs in $STAGING" >&2
  exit 2
fi

slugify() {
  local name="$1"
  name="${name%.*}"
  name="$(echo "$name" | tr '[:upper:]' '[:lower:]')"
  name="$(echo "$name" | sed -E 's/[^a-z0-9]+/_/g; s/^_+//; s/_+$//; s/_+/_/g')"
  if [[ -z "$name" ]]; then
    name="paper"
  fi
  echo "$name"
}

choose_slug() {
  local base="$1"
  local candidate="$base"
  local n=2
  while [[ -e "$LIBRARY/$candidate" ]]; do
    candidate="${base}${n}"
    n=$((n + 1))
  done
  echo "$candidate"
}

run_mathpix() {
  local pdf="$1"
  local out_md="$2"
  local log_file="$3"

  if [[ -s "$out_md" ]]; then
    echo "Mathpix markdown already exists: $out_md"
    return 0
  fi

  if [[ -n "${MATHPIX_CMD:-}" ]]; then
    python3 - "$pdf" "$out_md" "$log_file" <<'PY'
from __future__ import annotations
import os
import shlex
import subprocess
import sys

pdf, out_md, log_file = sys.argv[1:4]
template = os.environ["MATHPIX_CMD"]
cmd = template.replace("{pdf}", pdf).replace("{out}", out_md)

with open(log_file, "a", encoding="utf-8") as log:
    log.write(f"Running Mathpix command:\n{cmd}\n\n")
    proc = subprocess.run(cmd, shell=True, text=True, stdout=log, stderr=log)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)
PY
    if [[ -s "$out_md" ]]; then
      echo "Wrote Mathpix markdown: $out_md"
      return 0
    fi
    echo "Mathpix command completed but markdown was not created: $out_md" | tee -a "$log_file"
    return 1
  fi

  cat > "$out_md" <<EOF
# Mathpix conversion pending

Source PDF: $(basename "$pdf")

This placeholder was created by process_reference_papers.sh because MATHPIX_CMD was not set.

Rerun with a configured Mathpix command, for example:

MATHPIX_CMD='mathpix convert "{pdf}" --format md --output "{out}"' bash papers/milcom2026/tools/process_reference_papers.sh --staging "$STAGING"
EOF

  echo "MATHPIX_CMD not set; wrote placeholder markdown: $out_md"
}

process_pdf() {
  local src_pdf="$1"
  local base_slug
  local slug

  if [[ -n "$SINGLE_SLUG" ]]; then
    base_slug="$(slugify "$SINGLE_SLUG.pdf")"
  else
    base_slug="$(slugify "$(basename "$src_pdf")")"
  fi

  slug="$(choose_slug "$base_slug")"

  local paper_dir="$LIBRARY/$slug"
  local image_dir="$paper_dir/images"
  local page_dir="$image_dir/pages"
  local pdf_dst="$paper_dir/$slug.pdf"
  local md_dst="$paper_dir/$slug.md"
  local contact_dst="$image_dir/contact_sheet.png"
  local manifest="$paper_dir/manifest.json"
  local log_file="$paper_dir/process.log"

  mkdir -p "$paper_dir" "$page_dir" "$image_dir"

  if [[ "$MOVE_INPUTS" -eq 1 ]]; then
    mv "$src_pdf" "$pdf_dst"
  else
    cp "$src_pdf" "$pdf_dst"
  fi

  echo "Processing: $pdf_dst"
  echo "Slug: $slug"

  local page_count
  page_count="$(pdfinfo "$pdf_dst" | awk -F: '/^Pages:/ {gsub(/ /,"",$2); print $2}')"
  if [[ -z "$page_count" ]]; then
    page_count="unknown"
  fi

  rm -f "$page_dir"/raw-*.png "$page_dir"/"$slug"-*.png

  pdftoppm -png -r "$DPI" "$pdf_dst" "$page_dir/raw"

  local i=1
  local f
  shopt -s nullglob
  for f in "$page_dir"/raw-*.png; do
    mv "$f" "$page_dir/${slug}-$(printf '%03d' "$i").png"
    i=$((i + 1))
  done
  shopt -u nullglob

  python3 "$ROOT/papers/milcom2026/tools/make_pdf_contact_sheet.py" \
    --page-dir "$page_dir" \
    --out "$contact_dst" \
    --title "$slug" \
    --cols "$CONTACT_COLS" \
    --thumb-width "$THUMB_WIDTH"

  run_mathpix "$pdf_dst" "$md_dst" "$log_file" || true

  python3 - "$manifest" "$slug" "$pdf_dst" "$md_dst" "$page_dir" "$contact_dst" "$DPI" "$page_count" <<'PY'
from __future__ import annotations
import json
import sys
from pathlib import Path

manifest, slug, pdf, md, page_dir, contact, dpi, page_count = sys.argv[1:9]
pages = sorted(str(p) for p in Path(page_dir).glob("*.png"))
data = {
    "slug": slug,
    "pdf": pdf,
    "markdown": md,
    "page_dir": page_dir,
    "contact_sheet": contact,
    "render_dpi": dpi,
    "pdfinfo_pages": page_count,
    "rendered_pages": len(pages),
    "pages": pages,
}
Path(manifest).write_text(json.dumps(data, indent=2), encoding="utf-8")
print(f"Wrote manifest: {manifest}")
PY

  local bundle="$EXPORT_ROOT/${slug}_analysis_bundle.tar.gz"
  tar -czf "$bundle" -C "$paper_dir" .
  echo "Wrote downloadable bundle: $bundle"
  echo
}

for pdf in "${PDFS[@]}"; do
  process_pdf "$pdf"
done

echo "Done."
echo "Paper library: $LIBRARY"
echo "Downloadable bundles: $EXPORT_ROOT"
