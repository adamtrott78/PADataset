# NREIP 2027 résumé operator runbook

This directory contains the executable implementation for the content-locked and
production-locked NREIP 2027 résumé.

Use this file when the task is to **regenerate or inspect the existing résumé
artifact** rather than change candidate evidence, application targeting, locked
content, or the rendering contract.

## Authority boundary

Before changing content or production behavior, follow the owning contexts:

- candidate facts: `../../../context/EVIDENCE.md`;
- NREIP/application evidence: `../JOB_SPEC.md`;
- locked résumé content: `../RESUME_PLAN.md`;
- rendering and QA contract: `../SVG_PRODUCTION_SPEC.md`;
- executable implementation: `build_resume.py`.

The builder is a renderer, not the authority for résumé wording.

## Working-directory assumption

Commands below are written to run from the **repository root**.

Confirm the checkout before operating:

```bash
git branch --show-current
git rev-parse HEAD
git status --short
```

Do not mutate a dirty or unexpected checkout merely to make the commands work.

## Runtime dependencies

The current implementation requires:

### Python

- Python 3;
- `fontTools`;
- Pillow (`PIL`).

### System commands

- `fc-match` from Fontconfig;
- `inkscape`;
- `gs` from Ghostscript;
- `pdfinfo` from Poppler;
- `pdftotext` from Poppler;
- `pdftoppm` from Poppler.

### Font

The required production family is:

`Liberation Sans`

The builder resolves and uses:

- Regular;
- Bold;
- Italic;
- Bold Italic.

The builder rejects a Fontconfig nearest-match substitution whose resolved family
is not Liberation Sans.

The repository currently does **not** pin operating-system package versions,
Inkscape/Ghostscript/Poppler versions, or Python package versions for this tool.
A prepared machine must therefore preflight these dependencies before claiming
cross-machine reproduction.

Do not silently install or upgrade packages in a prepared research environment
merely because a dependency is missing.

## Suggested dependency preflight

From the repository root:

```bash
python3 --version

python3 - <<'PY'
import fontTools
import PIL
print("fontTools:", fontTools.__version__)
print("Pillow:", PIL.__version__)
PY

for cmd in fc-match inkscape gs pdfinfo pdftotext pdftoppm; do
    command -v "$cmd" || exit 1
done

fc-match "Liberation Sans:style=Regular"
fc-match "Liberation Sans:style=Bold"
fc-match "Liberation Sans:style=Italic"
fc-match "Liberation Sans:style=Bold Italic"
```

This confirms availability only. The builder remains the executable authority for
its own runtime checks.

## Public build

The public build is reproducible from the tracked repository alone.

From the repository root:

```bash
python3 resumes/applications/nreip2027/resume/build_resume.py --mode public
```

Expected tracked/public outputs:

```text
resumes/applications/nreip2027/resume/public/
  nreip2027_resume_public.svg
  nreip2027_resume_public.pdf
  page1.png
```

The public artifact uses public-safe placeholders rather than private submission
values.

A successful public build validates, among other things:

- locked source statuses;
- mirrored builder content against the locked plan;
- exact Liberation Sans family resolution;
- one-page fit;
- one-page Letter PDF structure;
- PDF size below 1,000,000 bytes;
- lack of PDF encryption;
- required extracted semantic content;
- 200-DPI Poppler rendering;
- successful Ghostscript rendering; and
- equal Poppler/Ghostscript render dimensions.

The dual-render automated check is a dimension/existence sanity check, not
pixel-equivalence or complete visual QA.

Human inspection of `page1.png` remains required.

## Private build

The private submission build is **not reproducible from GitHub alone**.

It requires the ignored local file:

```text
resumes/applications/nreip2027/private/RESUME_OVERLAY.md
```

That overlay owns the exact approved private substitutions.

Do not invent, recover, scrape, infer, or reconstruct those values from public
sources.

The private build command is:

```bash
python3 resumes/applications/nreip2027/resume/build_resume.py --mode private
```

Expected ignored outputs:

```text
resumes/applications/nreip2027/resume/private/
  nreip2027_resume.svg
  nreip2027_resume.pdf
  page1.png
```

Verify that the private output path remains ignored before submission work.

## Required build order for full local QA

For a prepared private application environment, run:

```bash
python3 resumes/applications/nreip2027/resume/build_resume.py --mode public
python3 resumes/applications/nreip2027/resume/build_resume.py --mode private
```

Running the public build first ensures that the current public artifacts exist
before the private build performs its exact-value leakage check against them.

The private build verifies that:

- required private substitutions appear in the private PDF; and
- those exact values do not appear in the public SVG or public PDF.

A public-only checkout intentionally cannot perform that exact-value comparison,
because the values needed for comparison are intentionally absent from Git.

Therefore:

- **public artifact regeneration** is cold-start reproducible from the repository;
- **full public/private privacy-parity QA** requires the ignored private overlay.

That limitation is a privacy boundary, not missing public evidence.

## Artifact contract

The current artifact contract is:

- exactly one page;
- U.S. Letter, approximately 612 × 792 pt;
- selectable/searchable PDF text;
- final private PDF strictly below 1,000,000 bytes;
- no PDF encryption;
- no clipping or overlap;
- public/private layouts structurally equivalent except for authorized private
  substitutions;
- typography no smaller than the limits established in
  `../SVG_PRODUCTION_SPEC.md`;
- public-safe tracked artifacts only.

Do not treat a successful process exit as final acceptance.

## Visual QA

Inspect:

`public/page1.png`

and, for the actual submission build:

`private/page1.png`

Check the criteria in `../SVG_PRODUCTION_SPEC.md`, including:

- clipping;
- overlap;
- wrapping;
- leading;
- indentation;
- hierarchy;
- page-edge clearance;
- glyph/font problems;
- excessive whitespace;
- unprofessional compression.

The private artifact governs submission readiness.

## Portal-specific final QA

The local artifact is not proof that the NREIP portal received the file.

After local private QA:

1. upload the private PDF through the NREIP portal;
2. use the portal's save/upload action;
3. download the server-side copy through the portal;
4. confirm that downloaded copy opens;
5. verify its page count and identity; and
6. visually inspect the downloaded copy when practical.

## Failure policy

Stop rather than silently compensating if:

- the required font family is unavailable;
- a required command/package is unavailable;
- locked source status is missing;
- builder content diverges from the locked plan;
- the résumé no longer fits one page under the production contract;
- a PDF fails page-size, page-count, extraction, encryption, or size checks;
- private values leak into public artifacts;
- visual QA reveals a material defect.

If content or page-density pressure requires different résumé wording, reopen
`../RESUME_PLAN.md`; do not rewrite content inside the builder.
