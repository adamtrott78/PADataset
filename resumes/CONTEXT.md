# Resume-generation workflow

Status: **COLD-START READY**

This is the scoped entry context for creating and tailoring resumes in PADataset.

The first live implementation case is **NREIP 2027**. The workflow should be
allowed to evolve from that real implementation rather than having a complete
resume architecture invented in advance.

## Purpose and artifact contract

The workflow turns:

- a target job, internship, fellowship, or research opportunity;
- authoritative information about its requirements and selection mechanism; and
- verified candidate evidence

into a tailored resume whose content and visual form can be inspected,
regenerated, and revised through the repository's normal ChatGPT ↔ terminal ↔
GitHub loop.

The intended mature production path is:

```text
candidate evidence
        +
target application evidence
        ↓
job/application analysis
        ↓
locked resume content plan
        ↓
production specification
        ↓
reproducible source artifact
        ↓
PDF + rendered visual review artifacts
        ↓
semantic and visual QA
        ↓
bounded revision
```

SVG is the intended initial source format because the existing presentation
workflow demonstrates that it is inspectable, reproducible, and visually
reviewable. This does not yet establish the final resume rendering architecture.
That must be learned from the first implementation.

A successful build is not established merely because a generator exits
successfully. The final resume must satisfy both its factual/content contract and
its rendered visual contract.

## Cold-start route

For ordinary resume work, read only what the task requires:

| Need | Read |
|---|---|
| Understand the resume workflow and authority model | this file |
| Understand the candidate's public-safe professional history | `context/PROFILE.md` |
| Verify whether a candidate claim is supported | `context/EVIDENCE.md` |
| Decide how to analyze and tailor for a target | `context/TAILORING.md` |
| Work on NREIP 2027 | `applications/nreip2027/CONTEXT.md` |
| Understand the NREIP opportunity and selection signals | `applications/nreip2027/JOB_SPEC.md` |
| Decide what the NREIP resume should contain | `applications/nreip2027/RESUME_PLAN.md` |
| Regenerate or inspect the current NREIP artifact | `applications/nreip2027/resume/README.md` |

Do not recursively ingest the repository.

Research-project facts should be traced to their owning PADataset context,
paper, source, or committed implementation only when the resume evidence ledger
or application plan requires that detail.

## Source-of-truth precedence

Conflicts are resolved semantically:

```text
candidate factual evidence          target opportunity evidence
    context/EVIDENCE.md             applications/<target>/JOB_SPEC.md
             \                              /
              \                            /
               content-selection authority
          applications/<target>/RESUME_PLAN.md
                         ↓
          production / rendering specification
                         ↓
          builder / executable implementation
                         ↓
                 generated artifact
```

`PROFILE.md` is a public-safe working summary. It does not override the evidence
ledger.

The central rule is:

**layout or implementation pressure must never silently rewrite candidate facts
or locked resume content.**

If content does not fit, report the conflict and revise the owning plan
deliberately.

## Privacy boundary

This repository is public.

Tracked resume contexts and review artifacts must therefore remain public-safe.
Do not commit private or restricted candidate information merely to make a
cold-start workflow self-contained.

Examples of information that should remain outside tracked public context unless
the user explicitly decides otherwise include:

- street address;
- private phone/contact details;
- student or government identifiers;
- transcripts containing private identifiers;
- medical, disability, legal, drug/alcohol, or clearance information;
- application-only demographic information;
- any scholarship, program, employer, or other status the user has been told
  not to publicize.

Local private inputs belong under ignored `resumes/private/` or an
application-specific ignored `private/` directory.

The NREIP implementation now demonstrates the public/private artifact pattern:

- tracked **public review** artifacts contain only public-safe placeholders; and
- local **private submission** artifacts resolve approved private values from
  ignored application-specific inputs and remain ignored by Git.

Future application builders may reuse this pattern only when their own production
contract establishes the same privacy boundary.

If a cold-start reader needs a private field that is not available in tracked
context, ask the user for it rather than inventing or recovering it indirectly.

## Current operating phases

For a new target:

1. capture authoritative target/application evidence;
2. update or verify only the candidate evidence needed for that target;
3. map selection signals and requirements to verified candidate evidence;
4. draft the application-specific resume plan;
5. review and lock content before typesetting;
6. define only the production rules needed for the artifact;
7. build a representative source/render;
8. inspect factual, structural, and visual correctness;
9. iterate through bounded Git-synchronized changes;
10. update this workflow when the implementation demonstrates a genuinely
   reusable rule.

The NREIP 2027 application has now exercised the full repository-production
cycle: authoritative application research, candidate-evidence reconciliation,
target mapping, content planning, content lock, production lock, source
generation, PDF/PNG rendering, semantic and visual QA, bounded revision, Git
synchronization, operator documentation, and independent cold-start validation.

The NREIP SVG/PDF artifact has been built, rendered, visually inspected, revised,
and independently audited from a fresh-reader perspective.

That implementation produced one reusable workflow lesson:

**page count is a production hypothesis until the first real render is visually
inspected.**

The original NREIP two-page target was reasonable during content planning but
proved substantially under-filled when rendered. The page budget and production
specification were explicitly revised to one page while the locked résumé claims
and bullets remained unchanged.

Therefore, when future résumé visual QA shows that pagination or page density is
wrong, revise the owning page-budget/production decision explicitly. Do not
silently rewrite résumé content merely to satisfy the original page-count
assumption.

Further production rules should still be generalized only from demonstrated
implementation evidence rather than speculation.

## Maturity boundary

This workflow is **COLD-START READY**.

Two independent fresh-reader audits successfully reconstructed the public NREIP
workflow from repository context. The first audit exposed real documentation and
production-contract defects; those defects were corrected. The second audit found
no issue that materially prevents safe public regeneration.

Known nonblocking limitations remain:

- system/Python-package renderer versions are not hermetically pinned;
- final visual correctness still requires human review;
- final portal receipt requires portal-side upload/download verification; and
- the private submission artifact intentionally requires ignored local inputs and
  cannot be reproduced from the public repository alone.

Those are explicit operating boundaries rather than cold-start blockers.

Promote this workflow to **STABLE** only after it has been reused successfully for
additional materially different resume targets and the reusable abstractions have
survived that reuse without target-specific leakage.
