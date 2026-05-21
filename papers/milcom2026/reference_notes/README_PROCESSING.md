# Reference Paper Processing

Drop PDFs into:

papers/milcom2026/reference_notes/staging/

Then run from repo root:

bash papers/milcom2026/tools/process_reference_papers.sh

For each PDF, the pipeline creates a structured paper folder under:

papers/milcom2026/reference_notes/papers/

Each processed paper contains:

- renamed PDF
- Mathpix markdown file or a placeholder if Mathpix is not configured
- rendered PNG for every page
- contact sheet PNG
- manifest JSON
- processing log

Downloadable analysis bundles are written to:

~/adamArchives/reference_paper_exports/

Mathpix integration is controlled with MATHPIX_CMD. The command must use:

- {pdf} for input PDF
- {out} for output Markdown

Example:

MATHPIX_CMD='mathpix convert "{pdf}" --format md --output "{out}"' bash papers/milcom2026/tools/process_reference_papers.sh

If the local Mathpix CLI uses a different syntax, change only MATHPIX_CMD, not the pipeline script.
