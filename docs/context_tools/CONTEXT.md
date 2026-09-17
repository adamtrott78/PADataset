# Context-backed workflow/tool authoring

This is the repository-level owner for designing or adding a new
**context-backed workflow/tool**.

Status: **provisional v0.1**.

This document captures patterns already demonstrated by the repository's
validated context/operator framework, its evidence-grounded paper-production
method, and the MILCOM SVG presentation workflow. It is deliberately not a
final universal framework. Revise it after additional tools have actually been
implemented and evaluated.

A future workflow should not copy one existing tool mechanically. Reuse the
architectural principles that survive across tools, then adapt the physical
files, implementation language, artifacts, and validation to the job.

## Evidence basis and current limits

The repository-level context system established these operating principles:

- `README.md` is a task router, not a giant handoff;
- a reader loads the owning context and only the specifically required sources;
- context separates contract/invariant knowledge, historical provenance, and
  recommended future operation;
- a proposed command is not evidence that it ran;
- process exit is not evidence that the artifact satisfies its contract;
- GitHub is the synchronization point for tracked source;
- bounded changes are reviewed, committed, pushed, and reread before the next
  source mutation;
- cold-start usability can be tested independently without exposing the
  evaluator rubric to the reader.

Phase 10 validated that repository operating model at the documentation level.
It did **not** establish hardware, model, or scientific reproduction.

The paper methodology in
[`papers/CONTEXT.md`](../../papers/CONTEXT.md) demonstrates a different but
compatible concern split: establish factual evidence and claim boundaries first,
then plan communication, produce artifacts, compile/render them, and inspect the
actual rendered result rather than trusting source edits alone.

The `milcom-presentation` branch provides a newer reference implementation.
Its relevant package is `presentations/milcom2026/`, where the workflow separates
a package entry context, scientific/design plan, SVG production specification,
narration, executable SVG builder, generated SVGs, rendered previews, and QA.

That presentation architecture is evidence for this methodology, not a required
template for every future tool. SVG, slides, narration files, and visual-preview
steps are presentation-specific.

The forthcoming resume-generation workflow is **not yet evidence for this
document**. Do not invent requirements from it or treat an anticipated design as
an established repository standard. Revisit this context after that workflow has
been implemented and evaluated.

## 1. Define the job and artifact contract first

Before implementation, establish the tool's contract.

Answer explicitly:

- What problem does this workflow solve?
- What is its primary output artifact?
- Who or what consumes that artifact?
- Which inputs are authoritative?
- What constitutes successful completion?
- What evidence establishes correctness?
- Which failures must be detectable?
- What must a cold-start reader know to operate or modify it?
- What information is historical/supporting evidence and should stay outside the
  normal startup path?

The artifact contract should be concrete enough that validation can distinguish
"the command finished" from "the intended artifact is correct."

Examples of artifact contracts differ by tool:

- a paper workflow may produce a compiled manuscript and review package;
- a presentation workflow may produce standalone SVG slides and rendered
  previews;
- a research workflow may produce validated data, manifests, checkpoints, or
  result tables.

Do not force unrelated tools into one output format.

## 2. Establish scoped ownership

Every important concern needs an explicit owner, but not necessarily its own
physical file.

Typical concerns are:

| Concern | What it owns |
|---|---|
| Evidence / factual contract | Facts, measurements, claim boundaries, required inputs |
| Historical provenance | Why prior choices, artifacts, or interfaces exist |
| Current operational context | How a fresh reader discovers and operates the workflow |
| Application/task plan | What this particular artifact should communicate or accomplish |
| Production specification | Rendering, file-format, geometry, transformation, or build rules |
| Executable implementation | Code that performs the transformation/build |
| Generated artifacts | Outputs produced by the implementation |
| Validation / QA | Checks proving semantic, structural, visual, or provenance correctness |

Merge concerns when one owner is genuinely clearer. Split them when different
forms of authority would otherwise become ambiguous.

Avoid both extremes:

- one giant context file that owns everything;
- one file per abstract concern when the split adds navigation without clarifying
  authority.

## 3. State source-of-truth precedence

A mature workflow must say how conflicts are resolved.

The precedence should follow the semantics of the tool rather than file age or
implementation convenience.

A useful general pattern is:

```text
evidence / factual authority
        ↓
task or application plan
        ↓
production specification
        ↓
executable implementation
        ↓
generated artifact
```

This is not a claim that every tool requires all five layers.

The central rule is:

**downstream production code must not silently redefine upstream factual or
semantic authority.**

For example, the MILCOM presentation separates scientific/design claims from
layout/rendering rules and narration. Its builder implements the production
contract; it is not allowed to invent new scientific values merely because they
fit a slide better.

When two authorities legitimately disagree, preserve and report the conflict.
Do not silently rewrite one side to make the repository appear internally
consistent.

## 4. Define a cold-start route

A context-backed tool must be discoverable without prior conversation history.

Its scoped entry context should tell a new reader:

- what this tool is for;
- which file to read first;
- which files to read only for particular sub-tasks;
- what owns factual/semantic authority;
- what owns implementation behavior;
- where outputs and validation evidence live;
- what environment or external dependencies are required;
- what should **not** be recursively ingested.

The root `README.md` should route the task to that owner with a short task row.
Do not move the tool's full methodology into the root README.

For a package large enough to need its own README, that package README may serve
as the local cold-start entry point, provided the repository router points to it
or to a context that routes into it.

## 5. Use the established iterative operating loop

Operate new tools with the repository's existing collaboration model:

```text
read scoped context
        ↓
establish checkout / runtime state
        ↓
make one bounded change or run one bounded operation
        ↓
produce artifact / result
        ↓
validate the artifact contract
        ↓
inspect the targeted Git diff
        ↓
stage reviewed paths
        ↓
commit and push
        ↓
ChatGPT rereads the pushed GitHub state
        ↓
next bounded correction
```

For reusable, concurrent, stateful, recoverable, or repeated operations, prefer
tracked implementation artifacts over long collections of ephemeral terminal
commands.

Do not confuse:

- inspecting a command with executing it;
- a successful process exit with a valid output;
- a dashboard/status marker with authoritative completion evidence;
- an already-open GUI/Jupyter view with the checkout currently being modified.

Use the repository-maintenance context for worktree, dirty-checkout, staging,
SSH, and copy/paste safety.

## 6. Make artifacts inspectable and reproducible

Prefer outputs and intermediate representations that can be inspected,
diffed, regenerated, or independently checked.

Where practical:

- keep the builder/generator in tracked source;
- keep meaningful configuration or production specifications in text;
- separate generated outputs from their source;
- record enough provenance to identify the inputs and producer;
- avoid manual edits to opaque final binaries when a reproducible source format
  can own the artifact instead.

This does **not** mean every final artifact must be text. PDFs, PNGs, datasets,
models, and other binaries can be legitimate outputs. The requirement is that
their production and validation path be explicit.

The MILCOM workflow's SVG-first design is one successful instance of this
principle, not a universal mandate.

## 7. Require artifact-level QA

Define validation from the artifact contract before calling the workflow done.

Relevant QA may include:

- factual / semantic checks;
- scientific claim and provenance checks;
- structural or static validation;
- schema / shape / metadata validation;
- visual inspection of rendered outputs;
- output-format and compatibility checks;
- reproducibility checks;
- comparison against locked source assets;
- negative checks for prohibited substitutions or unsupported claims.

A generator saying "success" is not enough.

For visual artifacts, inspect the rendered output rather than only the source
markup. For data/model artifacts, inspect the actual saved data, metadata,
configuration, or completion contract rather than only a progress display.

Validation should be narrow enough to identify what failed and whether the
failure belongs to documentation, implementation, runtime inputs, or the artifact
itself.

## 8. Keep status prose synchronized with real production state

Package documentation can drift after implementation evolves.

Treat a stale status sentence as a documentation defect, not as authority over
newer committed implementation/artifacts. At the same time, do not normalize
status drift as acceptable permanent behavior.

When a production milestone changes:

1. validate the new artifact/implementation;
2. update the owning package status/context;
3. review both in the same bounded change when practical.

The MILCOM presentation is a useful warning: its architecture is strong, but some
earlier status prose can lag newer committed slide/artifact state. Future tools
should minimize that divergence.

## 9. Use maturity states only as operational shorthand

The following maturity vocabulary is useful provisionally:

### `EXPERIMENTAL`

The concept or implementation is still being explored. Ownership or artifact
contracts may be incomplete. Prior chat context may still be required.

### `OPERABLE`

The workflow has explicit owners, implementation, inputs/outputs, and practical
artifact validation. A knowledgeable operator can use it, but independent
cold-start discovery has not yet been demonstrated.

### `COLD-START READY`

A fresh reader can enter through the repository/package route, identify the
correct authorities and implementation, and produce a grounded operational plan
without relying on hidden conversation history.

This state should be demonstrated by an independent test, not declared from
documentation alone.

### `STABLE`

The cold-start route has been demonstrated, the implementation/artifact contract
has survived actual use, significant status/provenance conflicts are resolved or
explicitly bounded, and the workflow is suitable as a canonical reference for
future work.

These names and thresholds are **provisional**. Revise them after more
context-backed tools have been built and tested.

## 10. Cold-start validation before maturity claims

For a sufficiently important workflow, validate the context architecture with a
fresh reader.

A useful test pattern is:

1. pin an exact repository commit;
2. give the reader only the root README or scoped entry route;
3. forbid prior chat/memory and recursive repository ingestion;
4. ask for one or more realistic operating cases;
5. require a read trace and explicit authority/validation reasoning;
6. keep the evaluator rubric outside the tested startup path;
7. distinguish reader error from a real documentation defect;
8. retest only the affected case after a justified correction;
9. record what the validation establishes and what it does not.

Documentation/operator validation does not imply runtime or scientific
reproduction.

## 11. Recommended authoring sequence

For a new context-backed workflow/tool:

1. define the job and artifact contract;
2. identify upstream factual/evidence authority;
3. assign concern ownership and source-of-truth precedence;
4. create the scoped cold-start entry route;
5. design the smallest production specification needed by the job;
6. implement a reproducible builder/operator path;
7. generate a small representative artifact first;
8. validate the actual artifact;
9. iterate with bounded changes through Git;
10. update status/context as implementation changes;
11. exercise recovery or failure paths when they matter;
12. independently cold-start test before calling the tool mature.

Do not create the entire architecture speculatively before the first artifact
exists. Allow implementation evidence to refine the methodology.

## Reference implementations

### Repository context/operator framework

Demonstrates:

- README-first scoped routing;
- explicit context ownership;
- bounded terminal/Git operation;
- artifact/result authority;
- independent cold-start validation.

See `README.md`, `docs/cleanup/CONTEXT.md`, and the finite Phase-10 records.

### Evidence-grounded paper workflow

Demonstrates:

- evidence and claim boundaries before prose/style;
- explicit source roles;
- tracked source plus compiled artifact;
- PDF + page PNG + Mathpix Markdown review;
- iterative targeted revision and rendered-page inspection.

See [`papers/CONTEXT.md`](../../papers/CONTEXT.md).

### MILCOM SVG presentation workflow

Reference branch: `milcom-presentation`.

Relevant package paths on that branch:

```text
presentations/milcom2026/README.md
presentations/milcom2026/PRESENTATION_PLAN.md
presentations/milcom2026/SVG_PRODUCTION_SPEC.md
presentations/milcom2026/SCRIPT.md
presentations/milcom2026/slides/README.md
presentations/milcom2026/tools/build_svg_slides.py
```

Demonstrates:

```text
context
→ scientific/design plan
→ production specification
→ executable builder
→ SVG artifact
→ rendered preview
→ visual/scientific QA
→ bounded revision
```

Do not universalize its SVG, slide, narration, or visual-layout choices.

## Provisional boundary and next revision trigger

This v0.1 should remain compact and evidence-backed.

Do not add detailed requirements for a tool that has not been built merely
because its likely architecture resembles an existing workflow.

The next planned revision should occur after another materially different
context-backed tool has been implemented. Compare its actual ownership model,
source-of-truth hierarchy, production path, QA failures, recovery behavior, and
cold-start results against the principles above.

Keep what generalizes. Remove what turns out to have been presentation- or
paper-specific. Add new rules only when implementation evidence justifies them.
