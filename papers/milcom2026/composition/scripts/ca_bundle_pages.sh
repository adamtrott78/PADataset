#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ca_bundle_pages.sh --aspect <aspect_id> --round <round_id> <paper_key> <pages> [<paper_key> <pages> ...]

Examples:
  ca_bundle_pages.sh --aspect hero_figure --round 002_tiwari_vs_trott_model_diagrams tiwari 4,5 trott 2,4,8
  ca_bundle_pages.sh --aspect hero_figure --round 002_tiwari_vs_trott_model_diagrams tiwari '[4,5]' trott '[2,4,8]'
  ca_bundle_pages.sh --aspect results --round 001_heatmap_layout baye 1-6 wei '[1-3,5]'

Page syntax:
  11
  1-5
  1,2,3
  [1,2,3]
  [5-9,15-36,38]

Assumed repository layout:
  Future canonical paper folders:
    papers/milcom2026/reference_notes/papers/<paper_key>/<paper_key>.pdf
    papers/milcom2026/reference_notes/papers/<paper_key>/images/page_001.png

  Current legacy fallback folders:
    papers/milcom2026/reference_notes/layout_screenshots/<long_reference_folder>/page_001.png
    papers/milcom2026/reference_notes/pdfs/<long_reference_name>.pdf

Output:
  papers/milcom2026/composition/aspects/<aspect>/upload_batches/<round>/<round>.tar.gz

The upload batch is ignored by Git. Only the manifest/request files are committed.
EOF
}

ASPECT=""
ROUND=""
DPI="180"
DO_BRANCH="1"
DO_COMMIT="1"

PAPERS_ROOT="papers/milcom2026/reference_notes/papers"
LEGACY_IMG_ROOT="papers/milcom2026/reference_notes/layout_screenshots"
LEGACY_PDF_ROOT="papers/milcom2026/reference_notes/pdfs"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --aspect)
      ASPECT="${2:?missing value for --aspect}"
      shift 2
      ;;
    --round)
      ROUND="${2:?missing value for --round}"
      shift 2
      ;;
    --dpi)
      DPI="${2:?missing value for --dpi}"
      shift 2
      ;;
    --papers-root)
      PAPERS_ROOT="${2:?missing value for --papers-root}"
      shift 2
      ;;
    --legacy-img-root)
      LEGACY_IMG_ROOT="${2:?missing value for --legacy-img-root}"
      shift 2
      ;;
    --legacy-pdf-root)
      LEGACY_PDF_ROOT="${2:?missing value for --legacy-pdf-root}"
      shift 2
      ;;
    --no-branch)
      DO_BRANCH="0"
      shift
      ;;
    --no-commit)
      DO_COMMIT="0"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    -*)
      echo "ERROR: unknown option: $1" >&2
      usage
      exit 2
      ;;
    *)
      break
      ;;
  esac
done

if [[ -z "$ASPECT" || -z "$ROUND" ]]; then
  echo "ERROR: --aspect and --round are required." >&2
  usage
  exit 2
fi

if [[ $# -lt 2 || $(( $# % 2 )) -ne 0 ]]; then
  echo "ERROR: expected one or more <paper_key> <pages> pairs." >&2
  usage
  exit 2
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is required." >&2
  exit 1
fi

if ! command -v pdftoppm >/dev/null 2>&1; then
  echo "ERROR: pdftoppm is required. Install with: sudo apt install -y poppler-utils" >&2
  exit 1
fi

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

BRANCH="comp-${ASPECT}"

if [[ "$DO_BRANCH" == "1" ]]; then
  if git show-ref --verify --quiet "refs/heads/${BRANCH}"; then
    git checkout "$BRANCH"
  else
    git checkout -b "$BRANCH"
  fi
fi

ASPECT_DIR="papers/milcom2026/composition/aspects/${ASPECT}"
INPUT_DIR="${ASPECT_DIR}/inputs/${ROUND}"
BUNDLE_DIR="${ASPECT_DIR}/upload_batches/${ROUND}"
IMAGE_OUT_DIR="${BUNDLE_DIR}/images"
CACHE_DIR="papers/milcom2026/composition/.cache/page_images"

mkdir -p "$INPUT_DIR" "$IMAGE_OUT_DIR" "$CACHE_DIR"

REQUEST_FILE="${INPUT_DIR}/REQUEST.txt"
MANIFEST_FILE="${INPUT_DIR}/MANIFEST.tsv"
BUNDLE_MANIFEST="${BUNDLE_DIR}/MANIFEST.tsv"
BUNDLE_REQUEST="${BUNDLE_DIR}/REQUEST.txt"

{
  echo "aspect=${ASPECT}"
  echo "round=${ROUND}"
  echo "branch=${BRANCH}"
  echo "dpi=${DPI}"
  echo "created_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo
  echo "arguments:"
  printf '  %q' "$0" --aspect "$ASPECT" --round "$ROUND"
  printf ' %q' "$@"
  echo
} > "$REQUEST_FILE"

printf "paper_key\tpage\toutput_file\tsource_type\tsource_path\n" > "$MANIFEST_FILE"

parse_pages() {
  python3 - "$1" <<'PYCODE'
import re
import sys

spec = sys.argv[1].strip()
if spec.startswith("[") and spec.endswith("]"):
    spec = spec[1:-1]

spec = spec.replace(" ", "")
if not spec:
    raise SystemExit("empty page spec")

pages = []
for part in spec.split(","):
    if not part:
        continue
    if "-" in part:
        a, b = part.split("-", 1)
        a, b = int(a), int(b)
        if a <= 0 or b <= 0:
            raise SystemExit("page numbers must be positive")
        if b < a:
            raise SystemExit(f"bad range: {part}")
        pages.extend(range(a, b + 1))
    else:
        p = int(part)
        if p <= 0:
            raise SystemExit("page numbers must be positive")
        pages.append(p)

seen = set()
out = []
for p in pages:
    if p not in seen:
        out.append(p)
        seen.add(p)

print(" ".join(map(str, out)))
PYCODE
}

find_one_match() {
  local pattern="$1"
  local label="$2"
  mapfile -t matches < <(compgen -G "$pattern" || true)

  if [[ ${#matches[@]} -eq 0 ]]; then
    return 1
  fi

  if [[ ${#matches[@]} -gt 1 ]]; then
    echo "ERROR: multiple ${label} matches for pattern: $pattern" >&2
    printf '  %s\n' "${matches[@]}" >&2
    exit 1
  fi

  printf '%s\n' "${matches[0]}"
}

resolve_image_dir() {
  local key="$1"

  if [[ -d "${PAPERS_ROOT}/${key}/images" ]]; then
    printf '%s\n' "${PAPERS_ROOT}/${key}/images"
    return 0
  fi

  if [[ -d "${PAPERS_ROOT}/${key}" ]]; then
    printf '%s\n' "${PAPERS_ROOT}/${key}"
    return 0
  fi

  if [[ -d "${LEGACY_IMG_ROOT}/${key}" ]]; then
    printf '%s\n' "${LEGACY_IMG_ROOT}/${key}"
    return 0
  fi

  local found=""
  found="$(find_one_match "${LEGACY_IMG_ROOT}/*${key}*" "image directory" || true)"
  if [[ -n "$found" && -d "$found" ]]; then
    printf '%s\n' "$found"
    return 0
  fi

  return 1
}

resolve_pdf() {
  local key="$1"

  if [[ -f "${PAPERS_ROOT}/${key}/${key}.pdf" ]]; then
    printf '%s\n' "${PAPERS_ROOT}/${key}/${key}.pdf"
    return 0
  fi

  local found=""
  found="$(find_one_match "${PAPERS_ROOT}/${key}/*.pdf" "canonical PDF" || true)"
  if [[ -n "$found" && -f "$found" ]]; then
    printf '%s\n' "$found"
    return 0
  fi

  if [[ -f "${LEGACY_PDF_ROOT}/${key}.pdf" ]]; then
    printf '%s\n' "${LEGACY_PDF_ROOT}/${key}.pdf"
    return 0
  fi

  found="$(find_one_match "${LEGACY_PDF_ROOT}/*${key}*.pdf" "legacy PDF" || true)"
  if [[ -n "$found" && -f "$found" ]]; then
    printf '%s\n' "$found"
    return 0
  fi

  return 1
}

find_existing_page_png() {
  local img_dir="$1"
  local key="$2"
  local page="$3"
  local p3
  printf -v p3 "%03d" "$page"

  local candidates=(
    "${img_dir}/page_${p3}.png"
    "${img_dir}/page-${page}.png"
    "${img_dir}/${key}-${p3}.png"
    "${img_dir}/${key}_page_${p3}.png"
    "${img_dir}/${key}_page-${page}.png"
  )

  for c in "${candidates[@]}"; do
    if [[ -f "$c" ]]; then
      printf '%s\n' "$c"
      return 0
    fi
  done

  return 1
}

generate_page_png() {
  local pdf="$1"
  local key="$2"
  local page="$3"
  local p3
  printf -v p3 "%03d" "$page"

  local prefix="${CACHE_DIR}/${key}_page_${p3}_tmp"
  rm -f "${prefix}"-*.png

  pdftoppm -png -r "$DPI" -f "$page" -l "$page" "$pdf" "$prefix" >/dev/null

  local generated=""
  generated="$(find_one_match "${prefix}-*.png" "generated page image")"

  local cached="${CACHE_DIR}/${key}-${p3}.png"
  mv "$generated" "$cached"
  printf '%s\n' "$cached"
}

while [[ $# -gt 0 ]]; do
  KEY="$1"
  SPEC="$2"
  shift 2

  PAGES="$(parse_pages "$SPEC")"

  IMG_DIR=""
  PDF_PATH=""

  IMG_DIR="$(resolve_image_dir "$KEY" || true)"
  PDF_PATH="$(resolve_pdf "$KEY" || true)"

  if [[ -z "$IMG_DIR" && -z "$PDF_PATH" ]]; then
    echo "ERROR: could not resolve images or PDF for paper key '${KEY}'." >&2
    echo "Expected future path: ${PAPERS_ROOT}/${KEY}/${KEY}.pdf" >&2
    echo "Expected legacy paths containing key under:" >&2
    echo "  ${LEGACY_IMG_ROOT}" >&2
    echo "  ${LEGACY_PDF_ROOT}" >&2
    exit 1
  fi

  for PAGE in $PAGES; do
    printf -v P3 "%03d" "$PAGE"
    OUT_NAME="${KEY}-${P3}.png"
    OUT_PATH="${IMAGE_OUT_DIR}/${OUT_NAME}"

    SRC=""
    SRC_TYPE=""

    if [[ -n "$IMG_DIR" ]]; then
      SRC="$(find_existing_page_png "$IMG_DIR" "$KEY" "$PAGE" || true)"
      if [[ -n "$SRC" ]]; then
        SRC_TYPE="existing_png"
      fi
    fi

    if [[ -z "$SRC" ]]; then
      if [[ -z "$PDF_PATH" ]]; then
        echo "ERROR: page ${PAGE} for '${KEY}' not found as PNG and no PDF available to render." >&2
        exit 1
      fi
      SRC="$(generate_page_png "$PDF_PATH" "$KEY" "$PAGE")"
      SRC_TYPE="rendered_from_pdf"
    fi

    cp "$SRC" "$OUT_PATH"

    printf "%s\t%s\t%s\t%s\t%s\n" "$KEY" "$PAGE" "$OUT_PATH" "$SRC_TYPE" "$SRC" >> "$MANIFEST_FILE"
  done
done

cp "$REQUEST_FILE" "$BUNDLE_REQUEST"
cp "$MANIFEST_FILE" "$BUNDLE_MANIFEST"

TAR_PATH="${BUNDLE_DIR}/${ROUND}.tar.gz"
rm -f "$TAR_PATH"

tar -czf "$TAR_PATH" -C "$BUNDLE_DIR" images MANIFEST.tsv REQUEST.txt

echo
echo "Created upload bundle:"
echo "  ${TAR_PATH}"
echo
echo "Download/upload this to ChatGPT from Jupyter Lab:"
echo "  ${TAR_PATH}"
echo
echo "Manifest:"
column -t -s $'\t' "$MANIFEST_FILE" || cat "$MANIFEST_FILE"

if [[ "$DO_COMMIT" == "1" ]]; then
  git add "$INPUT_DIR"

  if git diff --cached --quiet -- "$INPUT_DIR"; then
    echo
    echo "No metadata changes to commit for ${INPUT_DIR}."
  else
    git commit -m "Add CA page bundle metadata for ${ASPECT} ${ROUND}"
    git push origin "$BRANCH"
  fi
fi
