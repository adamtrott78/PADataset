# MILCOM source and reusable paper tools

Read the [paper methodology](../CONTEXT.md) first for composition decisions.
This document fills its operational gaps: where to edit, how to rebuild figures
and the manuscript, and how to prepare PDF + page PNGs + Mathpix Markdown for
critical analysis. Commands describe the inspected branch, not an assertion that
this checkout is byte-identical to the final submitted paper.

## Source map and edit ownership

| File or subtree | Edit here for |
|---|---|
| [main.tex](main.tex) | Title/authors, section ordering, top-level hero float/caption/label, bibliography wiring |
| [sections/](sections/) | Prose: 0-abstract, 1-intro, 2-related, 3-methodology, 4-experiments, 5-results, 6-discussion, 7-conclusion |
| [references.bib](references.bib) | Citation metadata and keys |
| [PAPER_GROUND_TRUTH.md](PAPER_GROUND_TRUTH.md), [PAPER_EVIDENCE_MAP.md](PAPER_EVIDENCE_MAP.md) | Claim/evidence records; check provenance before treating historical constants as final |
| [Makefile](Makefile) | Build/watch commands for main.tex |
| [figures/hero_figure/hero_dqnguard_pipeline_s22_tikz.tex](figures/hero_figure/hero_dqnguard_pipeline_s22_tikz.tex) | Standalone vector hero figure: node text, geometry, styles and arrows |
| [sections/5-results.tex](sections/5-results.tex) | Main-table inclusion, matrix float/caption/size and results narrative |
| [tools/process_reference_papers.sh](tools/process_reference_papers.sh) | PDF ingestion, page rendering, OCR-command hook, manifest and analysis archive |
| [tools/make_pdf_contact_sheet.py](tools/make_pdf_contact_sheet.py) | Contact-sheet layout from a page PNG directory |
| [composition/scripts/ca_bundle_pages.sh](composition/scripts/ca_bundle_pages.sh) | Selected-page packaging; old framework location does not make CA rounds mandatory |

Edit the owning LaTeX source, then regenerate its outputs. Do not edit a generated
PDF/PNG or the OCR copy as a substitute for changing manuscript prose.
Use explicit paths and small patches; review the diff for unintended replacement
of similarly named labels, symbols or repeated phrases. A figure caption may
live in main.tex even when its graphic source is in figures/.

The tracked main.tex includes the s22 hero PDF. The recovered Lambda source
contains a later s23 source; a higher suffix or an old “winning configuration”
document does not identify the active figure. Check the actual include path in
the intended manuscript before editing or compiling. Final-paper source selection
and the historical 8192/16384 result linkage remain provenance questions, documented
in [results and analysis](../../experiments/context/RESULTS.md). Do not silently
overwrite scientific prose or switch a dirty Lambda checkout to settle them.

## Edit an aspect and rebuild the manuscript

From the repository root, inspect the current includes before choosing files:

```bash
rg -n 'input|includegraphics|bibliography|label|caption' \
  papers/milcom2026/main.tex papers/milcom2026/sections
git diff -- papers/milcom2026
```

Change the smallest appropriate source region. Keep technical claims tied to
evidence; use the methodology's exemplar heuristics to improve communication.
For generated result graphics/tables, edit the generator or reviewed input
selection and follow the staged [results workflow](../../experiments/context/RESULTS.md).
The paper Makefile does not run those generators or build the hero PDF.

After dependent assets are ready, build from the paper directory:

```bash
cd ~/adamArchives/Adam/varMax/PADataset/papers/milcom2026
latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error \
  -synctex=1 -outdir=build main.tex
pdfinfo build/main.pdf
```

`make` uses the same source/output with the checked-in flags.
`make watch` invokes continuous latexmk; stop it when finished.
`make clean` uses latexmk's full cleanup, and `make distclean` removes build/.
Those are cleanup operations, not prerequisites for routine review.

Confirm successful exit and inspect build/main.log for unresolved citations,
references and overfull boxes. Inspect the actual new build/main.pdf and its
page count. Existing PDF presence after an error is not a successful build.
A historical six-page goal does not verify the new PDF or current venue rules.
After each edit/rebuild, complete the three-view review below before claiming
the revision has been reviewed.

## Create or revise the hero figure

The current figure is built with TikZ/standalone, not a hidden image-generation
function. The source declares node styles, colors, millimeter geometry and
connections. Edit that vector source for label wording, spacing, grouping and
arrow routing. Rebuild the currently referenced s22 asset from the paper root:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error \
  -outdir=figures/hero_figure \
  figures/hero_figure/hero_dqnguard_pipeline_s22_tikz.tex
```

This writes the PDF beside the source and can overwrite it. The required TeX
environment includes standalone, TikZ (arrows.meta/calc), amsmath, xcolor and
Helvetica support, plus IEEEtran for the manuscript. Rebuild main.tex afterward.
For a deliberate new candidate, choose a new source name and update the
manuscript's include only after reviewing the candidate; keep the caption and
labels aligned. Judge readability at final column/full-width scale in the
compiled paper, not only in an enlarged standalone preview.

Useful lessons preserved from the existing hero heuristics:

- Show one evidence-flow diagram with observation, backbone evidence, guard
  decision and downstream consumers; keep DQNGuard visually central.
- Its internal narrative is predicted-class calibration → guard evidence →
  known-budget thresholding.
- Compress the backbone into an evidence-producing block; represent IQ/FFT/DCT/
  polar, logits/probabilities/features only where they aid understanding.
- Keep detailed CNN branches, replay memory, epsilon-greedy training, full
  equations and response-policy actions out of this particular overview.
- Distinguish known PA evidence from unknown-behavior candidates, and show
  downstream QR-CWoS/label-making as context rather than evaluated capabilities.
- Use the caption to state that boundary clearly. Adapt these lessons to a new
  figure's role rather than copying this historical composition mechanically.

Matrix/table creation is owned by the existing Python generators documented in
RESULTS.md; it is a separate operation from this TikZ diagram.

## Prepare the three-view analysis package

For a selected reference, keep its original PDF and derive both the semantic OCR
and page PNGs from that PDF. For our manuscript, use the freshly compiled PDF
after every edit, with a new revision slug. Review content via MMD and exact
appearance via the PDF and every page PNG; a contact sheet is only an overview.

The repository already has the needed ingestion wrapper. It calls the configured
Mathpix command, which uploads the PDF for OCR; this is not local plain-text
extraction. The command syntax is supported by the
[official Mathpix CLI documentation](https://mathpix.com/docs/snip/mpx-cli):
`mpx convert input.pdf output.mmd`. The API-key path uses the existing
`MATHPIX_OCR_API_KEY` environment variable. Install `@mathpix/mpx-cli` only if
absent; `mpx login` is the alternative account-authentication route. Keep credentials
out of source files, command templates and logs.

If using a direct REST adapter instead of mpx, the
[official PDF API workflow](https://docs.mathpix.com/guides/pdf-processing)
submits the file to `POST /v3/pdf`, retains its pdf_id, polls processing status,
and downloads MMD when complete. Connect that adapter through MATHPIX_CMD's
`{pdf}` and `{out}` placeholders; write real MMD to the requested output path.
The repository does not contain a separate authenticated REST client to assume.

Required local tools: bash, Python 3 with Pillow, pdftoppm/pdfinfo, zip (checked
by the wrapper), tar, and the configured Mathpix client. Use the established
environment rather than reinstalling dependencies as a routine step.

Example for one selected PDF; replace the absolute PDF placeholder first:

```bash
cd ~/adamArchives/Adam/varMax/PADataset
export PA_PDF_SOURCE="/absolute/path/to/selected.pdf"
export PA_REVIEW_SLUG="reference_review01"
export PA_INPUT_STAGE="results/paper_review_inputs/reference_review01"
python - <<'PY'
import os
import re
import shutil
from pathlib import Path
source = Path(os.environ['PA_PDF_SOURCE'])
stage = Path(os.environ['PA_INPUT_STAGE'])
slug = os.environ['PA_REVIEW_SLUG']
assert re.fullmatch(r'[a-z][a-z0-9_]*', slug)
assert source.is_file() and not stage.exists()
assert not (Path('papers/milcom2026/reference_notes/papers') / slug).exists()
stage.mkdir(parents=True)
shutil.copy2(source, stage / (slug + '.pdf'))
PY
MATHPIX_CMD='mpx convert "{pdf}" "{out}"' \
  bash papers/milcom2026/tools/process_reference_papers.sh \
  --staging "$PA_INPUT_STAGE" --slug "$PA_REVIEW_SLUG" --dpi 220
```

For our newly compiled paper, use the same recipe with
`PA_PDF_SOURCE="papers/milcom2026/build/main.pdf"`, a new slug such as
`milcom_revision01`, and a matching new input-stage path. Those relative paths
assume the repository root, not papers/milcom2026/. Repeat with fresh names after
the next edit so changed page counts cannot leave stale pages behind.

Output goes to `papers/milcom2026/reference_notes/papers/<slug>/`:

| Artifact | Role |
|---|---|
| `<slug>.pdf` | Exact source PDF for this package |
| `<slug>.mmd` | Mathpix OCR semantic representation |
| `images/pages/<slug>-001.png`, etc. | One PNG per page at configured DPI |
| `images/contact_sheet.png` | Overview of page composition |
| `manifest.json` | Paths, rendered page count and pdfinfo page count |
| `process.log` | OCR command record; not a complete capture of CLI output |

The archive is normally
`reference_notes/reference_paper_exports/<slug>_analysis_bundle.tar.gz`.
REFERENCE_EXPORT_ROOT changes only the archive destination. `--staging`
changes only the input folder: the library/tool paths remain hardcoded to MILCOM.
For another paper, deliberately adapt those paths in its copied tools before
claiming a project-local workflow.

The wrapper copies inputs by default; `--move` removes them from staging.
Only top-level PDFs are processed, and `--slug` requires exactly one.
If a slug exists, a numerical suffix is chosen; the wrapper does not update that
package in place. Use the actual printed slug/path when inspecting outputs.

### Verify OCR and page completeness

The wrapper swallows OCR failure and can still write a manifest/archive.
Without MATHPIX_CMD it writes a nonempty “Mathpix conversion pending” placeholder.
It also accepts a timed-out conversion if output exists (default timeout 180
seconds). Nonempty output alone does not prove complete OCR. Inspect errors,
check beginning/end, equations, captions and references against the PDF.

For the fresh-slug recipe above:

```bash
python - <<'PY'
import hashlib
import json
import os
from pathlib import Path
slug = os.environ['PA_REVIEW_SLUG']
folder = Path('papers/milcom2026/reference_notes/papers') / slug
manifest = json.loads((folder / 'manifest.json').read_text())
pages = sorted((folder / 'images/pages').glob('*.png'))
assert len(pages) == manifest['rendered_pages'] == int(manifest['pdfinfo_pages'])
assert len(pages) > 0 and (folder / 'images/contact_sheet.png').is_file()
markdown = (folder / (slug + '.mmd')).read_text()
assert markdown.strip() and 'Mathpix conversion pending' not in markdown
assert hashlib.sha256((folder / (slug + '.pdf')).read_bytes()).digest() == hashlib.sha256(Path(os.environ['PA_PDF_SOURCE']).read_bytes()).digest()
print('PDF SHA256:', hashlib.sha256((folder / (slug + '.pdf')).read_bytes()).hexdigest())
print('Package checks passed; inspect every page and OCR content before review.')
PY
```

Record this hash plus source commit/diff, revision, render DPI and Mathpix
job/client details with the review. The wrapper manifest itself has no PDF hash
or reliable OCR-success field. Do not approve a package from its manifest alone.

For missing/placeholder OCR, call mpx directly on the package PDF and write a new
MMD output for inspection; replace the placeholder only after checking the result.
Rebuild the archive if package contents change. Rerunning the entire ingestion
script creates a suffixed package rather than repairing the original. Its
MATHPIX_CMD is expanded and executed as a shell command and recorded in the log;
use a trusted template without embedded credentials and plain filenames.

## Focus a review on specific pages

For a quick visual-only check from a fresh output directory, pdftoppm supports
`-f 2 -l 3` to render pages 2–3. This does not replace complete three-view review
after a revision. The contact-sheet helper accepts `--page-dir`, `--out`,
`--title`, `--cols`, `--thumb-width` and `--pad`; keep its output outside the
input page directory to avoid including an old contact sheet as a page.

The existing page-bundling helper can package selected reference pages:

```bash
bash papers/milcom2026/composition/scripts/ca_bundle_pages.sh \
  --no-branch --no-commit --aspect hero_figure --round focused_review01 \
  reference_review01 '1-2'
```

Run from the repository root, using an existing reference key with those pages.
The opt-outs are intentional: defaults switch/create comp-<aspect>, stage
metadata, commit and push. The helper writes request/manifest files under the
aspect's inputs/ and a tar.gz under upload_batches/. Its request's branch field
still describes comp-<aspect> even when branch switching is disabled.

Its image lookup expects PNGs directly under images/, whereas ingestion writes
images/pages/. It therefore normally falls back to rendering from the package
PDF. The bundle contains selected PNGs and metadata, not the full PDF/MMD;
supply the original three-view package alongside it when semantic context is
needed. Reusing a round can retain old images, so choose a new round name.
The old CA naming is an implementation detail, not a required comparative
composition process.

## Verification and handoff boundary

Before export, inspect the target compile entry point, all included sections,
bibliography and external graphics/table dependencies. A clean package must
contain those assets and use the intended main.tex; do not upload only edited
prose and assume the correct figure version is already present. Preserve a
reviewed source commit before export and verify the resulting PDF in the
destination environment. The export recipe below packages files; it does not
upload or submit anything.

## Export a clean Overleaf source package

First rebuild and review the intended revision using the workflows above. This
recipe migrates the handoff's rsync/ZIP process, with a fresh temporary directory
instead of deleting/reusing an export directory. Run from the repository root;
it requires `rsync`, `mktemp` and `zip` in addition to the build tools.

```bash
paper_export_dir=$(mktemp -d /tmp/padataset_overleaf_XXXXXX)
paper_export_zip="${paper_export_dir}.zip"
rsync -a \
  --exclude='build/' --exclude='page_previews/' \
  --exclude='reference_notes/' --exclude='composition/' \
  --exclude='*.bak' --exclude='*.bak_*' \
  --exclude='*.aux' --exclude='*.bbl' --exclude='*.blg' \
  --exclude='*.log' --exclude='*.out' --exclude='*.synctex.gz' \
  --exclude='*.fls' --exclude='*.fdb_latexmk' \
  papers/milcom2026/ "$paper_export_dir/"
test -f "$paper_export_dir/main.tex"
(cd "$paper_export_dir" && zip -qr "$paper_export_zip" .)
python - "$paper_export_zip" <<'PY'
import sys, zipfile
with zipfile.ZipFile(sys.argv[1]) as z:
    names=set(z.namelist())
    assert {'main.tex','references.bib','IEEEtran.cls'} <= names
    assert 'sections/0-abstract.tex' in names
    assert 'sections/7-conclusion.tex' in names
    assert z.testzip() is None
print(sys.argv[1])
PY
```

The ZIP has `main.tex` at its root, not under a second project directory. Source
figures, generated PDF graphics and table inputs under `figures/` and `tables/`
are copied; regenerate required assets first if they are missing locally. This
minimal archive check is not a dependency-completeness or compilation test.
If a future manuscript includes a file from an excluded directory, adjust the
selection after inspecting its dependencies. The recipe excludes `.bbl` and
therefore expects bibliography compilation; use the destination's requirements
when a submission specifically needs a `.bbl`.

Compile the extracted package in isolation and review its PDF before upload.
In Overleaf, select the intended `main.tex` and preserve the matching relative
section/asset paths. An abstract containing Results text or displaced sections
calls for inspecting the uploaded files and compile target; figure placement
alone does not prove a mismatch. Preserve the existing project before replacing
files, or use a new project when recovering a confused upload. Recheck the
destination PDF and its three-view analysis package. The ZIP remains under
`/tmp` until copied to the user's chosen durable export location.

Source interfaces checked at
`565179b5f2e78950cb59a38473169bc45ec5a35d`; Mathpix CLI/API documentation checked
during this migration. Command syntax and local renderer/helper contracts were
checked. No Mathpix request, manuscript rewrite, full-paper build or submission
was performed during documentation authoring.
