# Resume/application document-workflow integration

Status: **INTEGRATED — CURRENT DOMAIN REMAINS IN PADataset**

This document records the explicit integration between the PADataset
resume/application domain and the pinned workspace-control document-artifact
workflow. It also records the repository-separation decision made from the
current repository evidence.

## Exact shared binding

Repository-root `workspace-control.lock.json` pins:

- workspace-control checkpoint:
  `0bb8705e7a416bb064f3cd6c877e9d3fe559c8b9`;
- workflow: `workflows/document-artifact-build.v1.json`;
- workflow id: `document-artifact-build-v1`;
- workflow content blob:
  `0d66b919acdd2e51c08d2e8496c41dc22aed47c4`.

Do not silently substitute a later workflow or shared contract.

## Authority boundary

workspace-control owns only reusable artifact mechanics.

PADataset resume/application owners retain:

- candidate evidence and factual claims;
- target/application requirements and selection signals;
- application-specific tailoring rationale;
- locked resume content;
- production/rendering specifications;
- private/public data boundaries;
- deterministic builder commands and dependencies;
- application-specific semantic and visual acceptance criteria; and
- upload/submission semantics.

Layout or implementation pressure must never rewrite candidate evidence or locked
content.

## Lifecycle mapping

The demonstrated NREIP 2027 implementation maps to the shared workflow without
moving domain truth:

| Shared stage | PADataset owner/evidence |
|---|---|
| Load domain contract | `resumes/CONTEXT.md`, candidate `context/EVIDENCE.md`, target `JOB_SPEC.md`, content `RESUME_PLAN.md`, production `SVG_PRODUCTION_SPEC.md` |
| Prepare source | application-owned builder/source under `resumes/applications/<target>/` |
| Build | deterministic application command; NREIP uses `build_resume.py --mode public|private` |
| Structural/static validation | locked-source checks, page/size/encryption checks, extracted-text semantic checks, font checks, privacy checks |
| Render | final PDF plus review render; NREIP uses Poppler and Ghostscript |
| Visual QA | inspect the rendered final page against application-owned clipping/overlap/legibility/density criteria |
| Bounded revision | revise the owning layer only: content plan, production spec, or builder; then rebuild and revalidate |
| Delivery gate | portal upload/save/download verification is separate from local artifact completion |

A capable executor may perform visual QA when it has adequate image-inspection
capability. A human gate is required only when the owning application or delivery
decision explicitly requires substantive judgment or approval.

## Existing NREIP production mechanics

The existing SVG/PDF builder already implements the important shared mechanics:

- deterministic source generation from locked content;
- explicit font-family resolution;
- one-page fit enforcement;
- PDF page-count, dimensions, encryption, and strict size validation;
- extracted-text semantic validation against every renderer-owned content string;
- public/private artifact separation;
- private-value leakage checks when the ignored private overlay is available;
- Poppler and Ghostscript rendering;
- secondary-render dimension sanity checks; and
- a documented bounded-revision rule that forbids content rewriting for fit.

PDF byte identity is not the reproducibility criterion because renderer creation
metadata may vary. Reproducibility is established by source identity plus the
project-owned structural, semantic, privacy, and rendered-output contracts.

## Repository-separation decision

The current resume/application implementation remains in PADataset for this
integration. No repository is created and no files are moved by this decision.

Repository evidence nevertheless justifies a **future dedicated private
career/application repository** as a separately authorized migration:

1. PADataset's primary authority is RF/DQNGuard research, while candidate and
   application evidence form an independent long-lived domain.
2. The current repository is public, while real application work naturally has
   private overlays and may accumulate additional non-public target evidence.
3. The resume domain already has a clean internal authority boundary and can be
   separated without changing PADataset scientific truth.
4. The current public-safe cold-start route is operational, so there is no need
   to take migration risk merely to complete this workflow integration.

This is a design decision, not migration authorization.

## Requirements for any future migration

A separately authorized migration must:

- create/use a private destination intentionally rather than by implication;
- preserve source provenance and the relevant Git identities;
- move only career/application authority, not PADataset scientific authority;
- leave a durable redirect from PADataset's existing resume route;
- preserve the candidate-evidence -> target-evidence -> content-plan ->
  production-spec -> source -> PDF -> rendered-QA lifecycle;
- preserve ignored/private boundaries without exposing private values in public
  history;
- define the public-artifact retention policy explicitly;
- pin the shared workflow version used by the destination; and
- validate cold-start recovery before the old route is retired.

## Regression contract

A workflow-integration regression should demonstrate, using public-safe inputs
unless a prepared private environment is explicitly available:

1. fresh start from PADataset `README.md` routes to this resume domain without
   loading unrelated scientific contexts;
2. exact shared-workflow identity is recoverable from
   `workspace-control.lock.json`;
3. the public builder runs from tracked state and its semantic/structural checks
   pass;
4. the PDF renders successfully and the final rendered page is visually
   inspected;
5. a deliberately induced production-only fit/validation defect fails without
   rewriting locked content, and restoring the correct production layer returns
   the build to PASS;
6. tracked paths remain public-safe and private outputs remain ignored; and
7. external upload/submission is not conflated with local artifact completion.

A public-only regression is not expected to reproduce private overlay values.
That is an intentional privacy boundary.
