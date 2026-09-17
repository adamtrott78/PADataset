# Resume candidate evidence ledger

Status: **EXPERIMENTAL — structure established; claims not yet populated**

This file is the factual authority for candidate claims used by the resume
workflow.

A prior resume is evidence, not automatic truth. Older resumes can preserve useful
history while also containing stale degree status, shorthand relationships,
outdated dates, or wording that should not be propagated.

## Claim record

Use a compact record when a fact is important enough to be reused:

```text
CLAIM
<the factual proposition>

STATUS
VERIFIED_CURRENT | VERIFIED_HISTORICAL | CONFLICT | UNSUPPORTED

VALUE
<dates, title, result, relationship, metric, or other factual value>

EVIDENCE
<specific source paths, publications, transcripts, reviewed resumes, or
repository owners>

PERMITTED WORDING
<optional safe formulations>

FORBIDDEN / MISLEADING WORDING
<optional formulations that materially change the relationship or claim>

NOTES
<scope, uncertainty, provenance, or update conditions>
```

Not every trivial fact requires a large record. The ledger should be detailed
where ambiguity, quantitative claims, role relationships, or stale historical
wording create real risk.

## Evidence rules

1. Prefer current primary or authoritative evidence over old resume wording.
2. Preserve useful historical experience even if it is omitted from a current
   tailored resume.
3. Distinguish employment, university projects, scholarships, research
   collaboration, client relationships, and federal service accurately.
4. Quantitative research claims should trace to the relevant paper/result
   provenance when practical.
5. Do not upgrade an intended, planned, or submitted activity into a completed
   one.
6. Do not infer skills or responsibilities solely because they are plausible for
   a title.
7. Preserve unresolved conflicts explicitly.
8. Private evidence may support a local submission artifact without being copied
   into this public repository.

## Initial evidence sources

The first population pass should reconcile:

- the current DCSA-tailored resume;
- the supplied historical resumes and CV;
- authoritative academic evidence where needed;
- the HICSS-59 and MILCOM/DQNGuard repository evidence;
- relevant PADataset context and implementation ownership.

Do not populate this ledger from conversation memory alone when repository or
document evidence is available.
