# NREIP 2027 resume package

Status: **EXPERIMENTAL — first live resume-tool case**

This directory owns the first implemented use of the resume-generation workflow:
a tailored resume for the 2027 Naval Research Enterprise Internship Program
(NREIP).

## Start here

For NREIP resume work:

1. read `../../CONTEXT.md`;
2. read `../../context/EVIDENCE.md` when candidate claims need verification;
3. read `JOB_SPEC.md` for authoritative NREIP/application requirements and
   selection signals;
4. read `RESUME_PLAN.md` for the selected resume content and structure.

Read `../../context/TAILORING.md` when changing why content is selected or how the
target is analyzed.

Do not begin rendering until the resume plan has been reviewed and marked
content-locked.

## Current state

- resume workflow skeleton: established;
- candidate evidence ledger: initial public-safe baseline populated;
  target-specific verification ongoing;
- NREIP 2027 public-source opportunity research: captured;
- authenticated portal résumé guidance: captured;
- PDF and `< 1 MB` resume artifact constraints: established;
- portal-upload requiredness: not explicitly established by supplied guideline;
- target laboratory choices: selected in portal and captured in application context;
- resume content architecture and exact résumé copy: content-locked;
- SVG production specification: production-locked; builder is next;
- builder: not yet created;
- SVG/PDF/PNG artifacts: not yet created;
- cold-start validation: not yet performed.

## Intended implementation sequence

```text
official NREIP / laboratory evidence
        ↓
JOB_SPEC.md
        +
candidate EVIDENCE.md
        ↓
RESUME_PLAN.md
        ↓
user content review
        ↓
production specification
        ↓
first SVG
        ↓
PDF + rendered preview
        ↓
semantic / visual QA
        ↓
bounded revision
```

This package should teach the general resume workflow through implementation.
Reusable lessons belong in the parent resume context; NREIP-specific facts stay
here.
