# Evidence-grounded, exemplar-guided paper composition

Read this when beginning a paper or improving its prose, structure or presentation.
The methodology below is migrated from README Section 17.6 at
`565179b5f2e78950cb59a38473169bc45ec5a35d`, which records the author's actual
DQNGuard writing process. It is not inferred from implementation code or rebuilt
from the discarded comparative-analysis framework. The author clarified the
three-view ingestion/review cycle during this migration.

[Results and analysis](../experiments/context/RESULTS.md) owns numerical evidence
and generated result assets. [MILCOM source and reusable paper tools](milcom2026/CONTEXT.md)
owns file editing, compilation, OCR, page rendering and vector-figure mechanics.
For a new project, use its own evidence files in place of the historical MILCOM
examples below. Old ground-truth notes still need their claims tied to the
correct run/source snapshot; they cannot settle a known provenance disagreement.

## Common tasks

- **Begin a paper from experiments:** establish claims and boundaries in A, then
  produce the evidence-driven draft before selecting style exemplars.
- **Understand a source or exemplar:** assign a role in B, ingest all three
  representations in C, and analyze the paper individually in D.
- **Improve one section or figure:** synthesize transferable heuristics in E,
  make a targeted change in F, and rebuild/re-ingest using the tooling context.
- **Fit the venue page limit:** use G's clarity-per-line triage and check actual
  rendered pages; do not optimize prose length independently of comprehension.
- **Review a submission candidate:** complete the whole-paper score/audit in F,
  hostile-reader pass in H, and human/mechanical verification in I.

## The paper-composition method that was actually used


The final DQNGuard manuscript was **not** produced by mechanically executing the early comparative-analysis framework in `papers/milcom2026/composition/` or by forcing every reference paper through a large scorecard. Those files record an exploratory plan from an earlier stage. They are useful historical provenance, but they are **not the workflow a future chat should copy**.

The method that survived into the final paper was simpler and more effective:

1. establish the scientific ground truth and claim boundaries first;
2. build a technically complete evidence-driven draft;
3. curate several kinds of real papers, each for a specific reason;
4. analyze useful papers individually and extract transferable heuristics;
5. synthesize those heuristics into section-level writing rules;
6. revise the manuscript in targeted passes;
7. score/audit the whole paper against the same standards used to judge the exemplars;
8. spend the remaining page budget on the prose changes with the largest clarity gain;
9. finish with a human read-through plus mechanical build/reference checks.

The key distinction is **reference relevance is not the same as exemplar value**. A paper can be essential technical lineage but a poor writing model; another paper can be technically distant but an excellent model for problem framing, page economy, a figure, a results narrative, or claim boundaries.

### A. Start from evidence, not style

Before polishing prose, read:

```text
papers/milcom2026/PAPER_GROUND_TRUTH.md
papers/milcom2026/PAPER_EVIDENCE_MAP.md
papers/milcom2026/HANDIN_MANIFEST.md
```

The first draft should be generated from the actual method, run artifacts, reduced results, figures/tables, and known system boundaries. Lock down:

- what the experiments prove,
- what they do not prove,
- the paper's main claim,
- the paper's secondary/diagnostic findings,
- the role of the proposed method inside the larger operational system,
- which claims require citations.

For DQNGuard, this prevented the prose from drifting into a claim that the work solved the full QR-CWoS response loop. The paper evaluates an RF open-set sensing/decision layer that can feed downstream reasoning; it does not claim to implement the whole downstream system.

### B. Build a role-based paper library

The successful reference search used three overlapping groups.

**1. Direct technical sources and lineage.** These are papers we actually cite or rely on for definitions, predecessors, baselines, or technical language. For DQNGuard this included the varMax lineage, DQN-IDS, prior RF open-set work, multi-domain RF/EMS work, and foundational OSR/OOD/calibration papers. These sources control technical accuracy first; they are writing exemplars only when they are also well composed.

**2. Close venue/domain exemplars.** Select short MILCOM/IEEE RF, spectrum, communications, and security papers that resemble the target audience and page budget. Use them to learn six-page pacing, first-page economy, experimental exposition, figure/table density, and results narration. The DQNGuard searches deliberately added polished RF/MILCOM-style papers after the initial citation set because the citation set alone did not cover these communication problems.

**3. Award-recognized or unusually polished exemplars.** Add a small number of exceptionally well written systems/security papers. Some may have verified awards or recognition; others may be included simply because their composition is unusually strong. Even when the technical topic is more distant, use these for problem framing, operational stakes, evidence chains, discussion structure, and claim-boundary discipline -- not for importing unrelated technical assumptions or their longer-page layout.

Representative recorded DQNGuard examples included Baye et al. varMax and Wei et al. multi-domain EMS as close MILCOM models; Scheirer, Bendale/Boult, Guo, and Liu for technical OSR/OOD/calibration precision; and polished systems/security papers such as ZMap, Foreshadow, Carlini/Wagner, DolphinAttack, and Spectre for selected rhetorical lessons. Additional RF-style searches included papers such as Searchlight, SpecForce, spectrum-sensing/security work, Stitching the Spectrum, and HyperAdv. **Do not assume every historical candidate must be reused for a new paper. Choose papers that fill the new paper's actual communication gaps.**

A useful lightweight role vocabulary is:

```text
TECHNICAL_LINEAGE
VENUE_STYLE_MODEL
PROBLEM_FRAMING_MODEL
METHOD_EXPOSITION_MODEL
EXPERIMENT_DESIGN_MODEL
RESULTS_NARRATIVE_MODEL
FIGURE_MODEL
TABLE_MODEL
CLAIM_BOUNDARY_MODEL
LAB_CONTINUITY
```

These are tags, not a mandatory scoring system.

### C. Ingest only the papers worth close reading

For each selected paper, keep the original PDF, one PNG per PDF page, and
Mathpix Markdown produced through the Mathpix OCR API. These are complementary
views of the same version: PDF/page PNGs preserve exact appearance, composition,
readability, figure/table hierarchy and page economy; Mathpix Markdown supports
semantic, section, equation and information-content analysis. A contact sheet
helps orientation but does not replace reading individual pages at legible size.
OCR text is an analysis representation, not authority for exact publication text.

Use the [paper tooling context](milcom2026/CONTEXT.md) for the existing API-backed
CLI, ingestion script, page renderer, package validation and failure recovery.
Do not count placeholder Markdown or an image-only bundle as completed ingestion.

Apply this same PDF + page PNGs + Mathpix Markdown process to each new compiled
version of our own manuscript after an edit. All three must come from that
version before the next review; stale OCR or page previews are not interchangeable
with the new PDF. Record the revision and PDF hash so reviewers can identify it.
Analyze our draft by the same content and composition standards as the exemplars.

### D. Analyze each useful paper individually

Do **not** begin with a rigid `our section vs. exemplar A vs. exemplar B vs. exemplar C` matrix. Read each useful paper on its own terms and record only what transfers.

For each paper, answer:

- Why is this paper in the library?
- Which section/artifact does it teach us about?
- What does it do unusually well?
- What concrete structural or rhetorical heuristic can be extracted?
- What should **not** transfer because the domain, claims, page length, or evaluation differs?

Examples of the kind of heuristic we actually wanted:

- turn the operational problem into a crisp failure mode quickly;
- make a narrow component important by locating it clearly inside a larger system;
- use one readable pipeline figure rather than decorative architecture clutter;
- describe evaluation conditions before asking the reader to interpret scores;
- narrate why a result happens and what tradeoff it represents, not only which number wins;
- state what the method does **not** decide so the contribution remains credible;
- use venue exemplars for density/page economy and technical papers for definitions/lineage, rather than pretending one paper can model everything.

The output is a small set of **transferable heuristics**, not a large comparative-analysis report.

### E. Synthesize heuristics before rewriting

Once several papers have been analyzed, combine repeated lessons into rules for the current paper. For a short IEEE/MILCOM paper, the DQNGuard process converged on a communication package roughly like:

- an operational first-page hook and explicit failure mode;
- one central pipeline/system figure;
- compact methodology that follows the pipeline in reader order;
- a clearly separated experimental-design section;
- one main comparison table plus one diagnostic figure/matrix;
- results prose that explains the operating-point tradeoff and mechanisms;
- a discussion that states implications, limitations, and the boundary of the component;
- a short conclusion with no new claims.

Section-specific lessons should be derived from the current exemplar set, not copied blindly from this historical list.

### F. Revise in targeted passes, then score the whole paper

Apply the synthesized heuristics to the manuscript **without changing scientific truth**. Prefer targeted section/paragraph rewrites over uncontrolled paper-wide regeneration. Preserve terminology and advisor/lab framing when they are technically correct.

After a coherent draft exists, perform the same kind of quality review used on the reference papers. The DQNGuard final passes repeatedly evaluated the paper as a reviewer would, including:

- problem framing and significance,
- novelty/contribution clarity,
- technical correctness,
- method explanation,
- experimental rigor and fairness,
- results narrative and claim/evidence alignment,
- limitations and claim boundaries,
- abstract quality,
- figure/table usefulness and readability,
- page economy,
- overall readability / reviewer effort.

The purpose of scoring is diagnostic: identify the weakest reviewer-facing dimension and fix that next. Do not optimize a synthetic total score at the expense of scientific correctness.

### G. Treat the page limit as an information budget

The final DQNGuard paper reached six pages through both compression **and later decompression**. This is important: once the draft fits, do not assume shorter prose is better.

For every substantial pass:

1. compile;
2. verify the actual page count;
3. render every page;
4. inspect section flow, columns, figures/tables, whitespace, and line wrapping.

When space is scarce, triage prose by **clarity improvement per added line**. The final process explicitly inventoried compressed passages, estimated how much each compression hurt comprehension, estimated the line cost of restoring clarity, and spent remaining space on the highest-value fixes first. Conversely, when the paper overflowed, compression targeted lower-value/redundant prose before cutting necessary explanation.

Do not fill space merely because it exists. Use available lines only when they reduce ambiguity, lower reviewer effort, strengthen claim/evidence flow, or restore an important limitation/definition. DQNGuard's final layout intentionally used most of the six-page budget and placed the conclusion cleanly in the final column, but that exact column placement is historical, not a universal rule.

### H. Run a hostile/low-effort-reader clarity pass

Before submission, read the paper as if the reviewer is skeptical, rushed, or looking for an easy misunderstanding. Every major claim should be difficult to misread.

Check especially:

- acronyms are expanded before first use;
- specialized terms are defined before they carry argumentative weight;
- the reader can state the task, method input/output, calibration/evaluation regime, and operating constraint without reverse-engineering them;
- baseline comparisons are fair and described consistently;
- figures/tables are referenced explicitly and near the relevant prose;
- the abstract tells the same story as the body;
- limitations prevent overclaiming without obscuring the contribution.

This pass is where DQNGuard's abstract, acronym setup, compressed prose, and several reviewer-risk ambiguities received late improvements.

### I. Finish with human and mechanical verification

The last pass is not another rewrite. It is a proofread and reproducibility check.

For DQNGuard the finalization loop included:

- a human line-by-line read-through;
- checking exact experimental constants against the repository/figures;
- checking acronym definitions and terminology;
- checking figure/table references and captions;
- checking citations and claim boundaries;
- rebuilding from the intended LaTeX source;
- confirming the PDF is exactly within the page limit;
- rendering the final PDF and visually reviewing every page;
- guarding against stale preview/build paths;
- committing the successful state before Overleaf/export/submission.

### Writing doctrine

The desired style is:

- technically precise,
- easy to audit,
- explicit about assumptions,
- rhetorically clear,
- concise but not compressed into ambiguity,
- grounded in experiment outputs,
- guided by excellent real papers rather than generic AI style,
- written so a skeptical reviewer can recover the paper's logic with minimal effort.

Avoid:

- hype,
- vague “AI paper” phrasing,
- unsupported generalization,
- copying exemplar wording or technical assumptions,
- claiming a full system when only one layer/component was evaluated,
- using the old comparative-analysis scorecards/CA rounds as mandatory procedure,
- rewriting an entire paper to solve one local prose issue.

### Historical composition records

The old composition frameworks, aspect registry and CA-round records document an
earlier approach, not a required writing algorithm. Useful exemplar observations
and figure-design lessons may be retained as evidence, but do not reactivate
mandatory scorecards or comparison rounds. Git and the preservation branch retain
retired documents when the later cleanup phase removes them. This migration
leaves the README and legacy files in place until the planned integration pass.

## Creating a new paper
Do not overwrite `papers/milcom2026/` for a new venue/project.

Recommended pattern:

```text
papers/<venue_or_project>/
    main.tex
    sections/
    figures/
    tables/
    references.bib
    PAPER_GROUND_TRUTH.md
    PAPER_EVIDENCE_MAP.md
    composition/
    reference_notes/
    tools/
```

Then reuse the concepts, not the historical claims:

- evidence maps,
- generated figure/table scripts,
- Mathpix/reference-paper ingestion,
- page rendering,
- role-based exemplar selection and synthesized writing heuristics,
- reviewer-style scoring/audits,
- page-budget clarity triage,
- final build verification,
- clean Overleaf export.

A new paper should get a new ground-truth file tied to its actual run manifests and result roots.

## Context maintenance

Preserve this methodology when tool implementations change. Update operational
commands in their owning context, and update evidence files when scientific
results change. Keep transient task progress in Git, run/review outputs and
task tracking rather than turning this document into a chat handoff.
