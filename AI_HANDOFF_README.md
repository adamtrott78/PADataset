# AI Handoff README for PADataset / MILCOM 2026 Paper

This document is the operational map for future AI chats working on this repository. The current priority is the MILCOM 2026 paper under `papers/milcom2026/`.

The project has two simultaneous goals:

1. Finish a technically correct MILCOM 2026 paper.
2. Develop a reusable paper-composition workflow based on comparative analysis of strong papers, generated figures/tables, and iterative LaTeX revisions.

---

## 1. Current Paper Location

Main paper directory:

```text
papers/milcom2026/
```

Primary LaTeX file:

```text
papers/milcom2026/main.tex
```

Section files:

```text
papers/milcom2026/sections/
  0-abstract.tex
  1-intro.tex
  2-related.tex
  3-methodology.tex
  4-experiments.tex
  5-results.tex
  6-discussion.tex
  7-conclusion.tex
```

Bibliography:

```text
papers/milcom2026/references.bib
```

Main generated figures:

```text
papers/milcom2026/figures/hero_figure/
papers/milcom2026/figures/target_surrogate_matrix/
```

Main generated tables:

```text
papers/milcom2026/tables/main_results/
```

---

## 2. Current Branch

Most recent paper work has been done on:

```text
comp-hero-figure
```

Check branch:

```bash
git branch --show-current
```

Switch branch:

```bash
git checkout comp-hero-figure
```

---

## 3. Build the Paper Locally

Compile:

```bash
cd ~/adamArchives/Adam/varMax/PADataset/papers/milcom2026

latexmk -pdf -interaction=nonstopmode -file-line-error -synctex=1 -outdir=build main.tex
```

Watch mode for continuous editing:

```bash
cd ~/adamArchives/Adam/varMax/PADataset/papers/milcom2026

make watch
```

The user has also been serving the compiled paper in a browser through a local HTTP server / Jupyter workflow.

---

## 4. Render Paper Pages for Visual Inspection

After compiling:

```bash
cd ~/adamArchives/Adam/varMax/PADataset/papers/milcom2026

rm -rf build/page_previews
mkdir -p build/page_previews

pdftoppm -png -r 220 build/main.pdf build/page_previews/page

ls -lh build/page_previews
```

The user can upload relevant rendered page PNGs to the chat for visual critique.

Do not commit `build/` or page preview PNGs unless explicitly requested.

---

## 5. Overleaf Export

Create a clean Overleaf ZIP:

```bash
cd ~/adamArchives/Adam/varMax/PADataset

cd papers/milcom2026
latexmk -pdf -interaction=nonstopmode -file-line-error -synctex=1 -outdir=build main.tex

cd ~/adamArchives/Adam/varMax/PADataset

EXPORT_ROOT="$HOME/adamArchives/overleaf_exports"
STAMP="$(date +%Y%m%d_%H%M%S)"
EXPORT_DIR="$EXPORT_ROOT/milcom2026_overleaf_$STAMP"
ZIP_PATH="$EXPORT_ROOT/milcom2026_overleaf_$STAMP.zip"

mkdir -p "$EXPORT_DIR"

rsync -av \
  --exclude='build/' \
  --exclude='page_previews/' \
  --exclude='reference_notes/' \
  --exclude='*.aux' \
  --exclude='*.bbl' \
  --exclude='*.blg' \
  --exclude='*.log' \
  --exclude='*.out' \
  --exclude='*.synctex.gz' \
  --exclude='*.fls' \
  --exclude='*.fdb_latexmk' \
  papers/milcom2026/ "$EXPORT_DIR/"

cp papers/milcom2026/build/main.pdf "$EXPORT_ROOT/milcom2026_current_compiled_$STAMP.pdf"

cd "$EXPORT_DIR"
zip -r "$ZIP_PATH" .

echo "Created:"
ls -lh "$ZIP_PATH"
ls -lh "$EXPORT_ROOT/milcom2026_current_compiled_$STAMP.pdf"
```

Important Overleaf rule:

The ZIP must have `main.tex` at the ZIP root, not nested inside another folder.

Check:

```bash
unzip -l ~/adamArchives/overleaf_exports/milcom2026_overleaf_*.zip | grep ' main.tex$'
```

---

## 6. Current Paper State

The current paper is technically complete enough to compile and show to the professor, but the prose is not final.

The current paper was generated primarily from ground-truth project documentation and experimental outputs. It succeeds at communicating the project contents but has not yet been optimized for rhetorical quality, audience fit, or MILCOM-style clarity.

The user intends to do a human line-by-line revision later. AI should support that by:

1. Auditing structure.
2. Comparing the paper to excellent exemplars.
3. Extracting section-level writing heuristics.
4. Suggesting targeted rewrites.
5. Avoiding broad uncontrolled rewrites unless explicitly requested.

---

## 7. Major Current Figures and Tables

### Figure 1: DQNGuard Pipeline

Final current candidate:

```text
papers/milcom2026/figures/hero_figure/hero_dqnguard_pipeline_s22_tikz.pdf
papers/milcom2026/figures/hero_figure/hero_dqnguard_pipeline_s22_tikz.tex
```

Purpose:

Shows RF input → multi-domain PA encoder → DQNGuard → OSR outputs.

This is inserted in Methodology as Figure 1.

### Figure 2: Target--Surrogate Matrix

Generator:

```text
papers/milcom2026/figures/target_surrogate_matrix/make_target_surrogate_matrix.py
```

Output:

```text
papers/milcom2026/figures/target_surrogate_matrix/target_surrogate_unknown_f1_matrix.pdf
papers/milcom2026/figures/target_surrogate_matrix/target_surrogate_unknown_f1_matrix.csv
```

Purpose:

Shows unknown F1 for target unknown class versus surrogate-open calibration class.

This is inserted in Results as Figure 2.

### Table I: Main OSR Results

Generator:

```text
papers/milcom2026/tables/main_results/make_main_results_table.py
```

Generated table:

```text
papers/milcom2026/tables/main_results/main_osr_results_table.tex
papers/milcom2026/tables/main_results/main_osr_results_table_summary.csv
```

Purpose:

Compares DQNGuard, Shreyash CNN head, and VarMax surrogate-all under fixed PA1-surrogate known-budget calibration.

This is inserted in Results.

---

## 8. Important Result Sources

Main Table I source:

```text
results/og_method_comparison/og_dqnguard_vs_varmax_vs_shreyash_full.csv
```

Target--Surrogate Matrix source candidates used by generator:

```text
results/target_surrogate_selection/ts_matrix_surrogate_selection_rules_full.csv
results/target_surrogate_selection/ruleD_confusion_route_alignment_full.csv
results/l2o_surrogate_selection/l2o_surrogate_selection_diagnostics.csv
```

Known weak result:

Rule E pseudo-target surrogate selection performed poorly and should not be overstated.

Known important result:

Target--Surrogate Matrix shows surrogate utility is highly target-dependent.

---

## 9. Reference Notes and Comparative Analysis Infrastructure

Reference PDFs, Mathpix markdown, and layout screenshots live under:

```text
papers/milcom2026/reference_notes/
```

Expected structure:

```text
reference_notes/
  pdfs/
  markdown/
  layout_screenshots/
```

The user has been converting reference papers into:

1. Original PDF.
2. Mathpix Markdown.
3. Page images / contact sheets.

The purpose is to let AI compare both content and visual composition.

---

## 10. Comparative Analysis Workflow

The intended revision workflow is:

1. Choose a paper component to improve.
   Examples:

   * Introduction
   * Related Work
   * Methodology
   * Experimental Design
   * Results
   * Discussion
   * Figure 1
   * Table I

2. Select strong exemplar papers or sections.
   Sources may come from:

   * MILCOM papers
   * accepted labmate papers
   * ScholarGPT recommendations
   * advisor-provided exemplars
   * highly polished IEEE papers

3. Convert exemplars into analyzable forms:

   * PDF
   * Mathpix Markdown
   * page images

4. Perform comparative analysis:

   * What does exemplar A do well?
   * What does exemplar B do well?
   * What does our paper currently do poorly?
   * What should be copied structurally, visually, or rhetorically?
   * What should not be copied?

5. Produce heuristics:

   * section-specific writing rules
   * figure/table design rules
   * paragraph-level structure rules
   * caption rules
   * audience-specific framing rules

6. Apply the heuristics to the current paper.

7. Compile and inspect rendered pages.

8. Commit each successful iteration.

---

## 11. Suggested Git Discipline

Before major rewrites:

```bash
git status --short
git checkout comp-hero-figure
git pull
```

Create a branch for a major comparative analysis pass:

```bash
git checkout -b comp-methodology-rewrite-v1
```

After edits:

```bash
git add <files>
git status --short
git commit -m "<clear message>"
git push origin <branch>
```

For small paper edits on the current branch:

```bash
git add papers/milcom2026
git status --short
git commit -m "<clear message>"
git push origin comp-hero-figure
```

---

## 12. Current High-Level Revision Priorities

Priority 1: Paper-wide structure audit.

Questions:

* Does each section earn its place?
* Are claims introduced before evidence?
* Are figures/tables placed near the prose that uses them?
* Does the introduction promise exactly what the results deliver?
* Are limitations clear without sounding weak?
* Is the QR-CWoS / ATT&CK-EW connection clear but not overclaimed?

Priority 2: Find excellent exemplar papers.

Need papers with strong:

* MILCOM-style introduction
* RF/communications experimental methodology
* OSR / novelty detection framing
* figure/table economy
* results narrative
* discussion/limitations writing

Priority 3: Comparative revision.

Start with:

1. Introduction
2. Methodology
3. Results
4. Discussion

Priority 4: Human line edit.

The user intends to personally revise wording line-by-line after AI-assisted structure and comparative analysis.

---

## 13. Important Style Preferences From User

The user wants:

* strong technical precision
* no overclaiming
* clear paper logic
* preservation of advisor/professor voice where possible
* prose that is rhetorically strong, not merely information-complete
* section rewrites guided by exemplars, not generic AI style
* explicit documentation of the comparative-analysis process

The user does not want:

* vague “AI paper” prose
* uncontrolled broad rewrites
* empty hype
* unsupported claims
* final paper wording that sounds detached from the lab’s real research purpose

---

## 14. Current Conceptual Framing

Core claim:

DQNGuard is a budgeted open-set recognition decision layer for RF preliminary-action detection. It uses multi-domain OTA RF evidence and known-only thresholding to reject unknown RF behaviors while preserving known-class recognition.

Broader purpose:

This RF OSR layer supports a QR-CWoS-style pipeline by producing:

* known preliminary-action evidence for ATT&CK/EW precursor hypotheses
* unknown behavior pools for LLM-assisted label-making and continual learning

Important boundary:

The paper does not solve full response planning or autonomous EW decision-making. It demonstrates the sensing/OSR mechanism needed to feed such systems.

---

## 15. Commands New Chat Should Know

Compile:

```bash
cd ~/adamArchives/Adam/varMax/PADataset/papers/milcom2026
latexmk -pdf -interaction=nonstopmode -file-line-error -synctex=1 -outdir=build main.tex
```

Render pages:

```bash
rm -rf build/page_previews
mkdir -p build/page_previews
pdftoppm -png -r 220 build/main.pdf build/page_previews/page
```

Generate Figure 2:

```bash
cd ~/adamArchives/Adam/varMax/PADataset
python papers/milcom2026/figures/target_surrogate_matrix/make_target_surrogate_matrix.py
```

Generate Table I:

```bash
cd ~/adamArchives/Adam/varMax/PADataset
python papers/milcom2026/tables/main_results/make_main_results_table.py
```

Create Overleaf ZIP:

```bash
cd ~/adamArchives/Adam/varMax/PADataset
# use the Overleaf export command block in Section 5
```

Check Git:

```bash
git status --short
git log --oneline -5
```

---

## 16. Immediate Next Step for New Chat

If a new chat is taking over, it should first:

1. Read this file.
2. Inspect `papers/milcom2026/main.tex`.
3. Inspect all section files.
4. Compile the paper.
5. Render page previews.
6. Ask the user which priority to pursue:

   * exemplar sourcing and comparative analysis
   * paper-wide audit
   * section rewrite
   * figure/table polish
   * Overleaf packaging
