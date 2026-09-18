# NREIP 2027 SVG résumé production specification

Status: **PRODUCTION LOCKED**

This file owns the rendering contract for the content-locked NREIP 2027 résumé.

It governs:

- page geometry;
- typography;
- visual hierarchy;
- deterministic pagination;
- public-review versus private-submission rendering;
- SVG construction;
- PDF conversion;
- semantic/text QA;
- visual QA; and
- final NREIP artifact validation.

It does **not** own résumé wording.

Content authority remains:

`RESUME_PLAN.md`

Private substitution authority remains the ignored application-specific private
overlay.

If production reveals a genuine content problem, do not silently rewrite,
remove, enlarge, shorten, or add résumé text here or in the builder. Reopen
`RESUME_PLAN.md`, revise the owning content decision, obtain review, relock it,
and then rebuild.

## Artifact objective

Produce a professional two-page research/technical résumé optimized for review
by Department of Navy laboratory research staff.

The visual design should communicate:

- technical depth;
- academic/research maturity;
- clarity;
- precision;
- restrained professionalism; and
- high information density without appearing cramped.

The résumé should not look like:

- a federal qualification résumé;
- a graphic-design portfolio;
- a two-column infographic;
- a résumé template dominated by decorative elements; or
- a document whose layout impairs machine text extraction.

## Page contract

### Physical page

Use U.S. Letter:

- width: 8.5 inches;
- height: 11 inches;
- PDF page size: 612 × 792 points.

Each SVG page should use:

```xml
width="8.5in"
height="11in"
viewBox="0 0 612 792"
```

This makes one SVG user unit correspond conceptually to one PDF point within the
page coordinate system.

### Page count

Exactly **two pages**.

The portal does not impose this limit; it is the content-locked NREIP résumé
design decision.

Do not create:

- a third page;
- an artificially compressed one-page version; or
- blank/filler space merely to reach two pages.

### Margins

Target content margins:

- left: 38 pt;
- right: 38 pt;
- top: 32 pt on page 1;
- top: 34 pt on page 2;
- bottom: minimum 30 pt.

No visible text or rules may enter the margin safety area.

## Deterministic page ownership

Pagination is semantic, not automatic.

### Page 1

In this order:

1. Header
2. Education
3. Research Experience
   - Research Assistant / operational-AI research
   - DQNGuard
   - HICSS-59 RF open-set-recognition research

### Page 2

In this order:

1. Selected Publications
2. Technical Skills
3. Selected Technical and Teaching Experience
   - NUWC-client Senior Design capstone
   - Cyber Defense and Operations TA
   - Digital Forensics TA

Do not split an individual bullet across pages.

Do not move an entire locked section to a different page solely because a
builder finds automatic pagination easier.

If either page cannot accommodate its assigned content under the minimum
typographic constraints in this specification, report a fit failure rather than
altering content.

## Layout model

Use a single-column résumé.

Do not use:

- sidebars;
- multi-column skill blocks;
- floating boxes;
- icons as semantic labels;
- charts;
- portraits;
- rating bars;
- timelines; or
- decorative backgrounds.

Dates and concise metadata may be visually aligned toward the right edge where
appropriate, but DOM/source order and PDF extraction order must remain logical.

The rendered document should still read correctly if all formatting is stripped.

## Typography

### Font family

Use a professional sans-serif font with reliable PDF embedding and text
extraction.

Preferred family:

`Liberation Sans`

Accepted fallback only if font preflight establishes availability and stable
metrics:

`Arial`

Do not use a custom downloaded font or commit font files to the repository.

The builder must verify that the selected production font is available before
rendering.

Do not silently substitute a materially different font.

### Minimum sizes

Target sizes may be adjusted slightly during visual QA, but never below these
minimums without reopening this production specification:

- candidate name: 18.5 pt minimum;
- professional contact line: 9.0 pt minimum;
- section heading: 10.2 pt minimum;
- principal entry/project heading: 9.8 pt minimum;
- metadata line: 8.8 pt minimum;
- body/bullet text: 9.0 pt minimum;
- publication text: 8.9 pt minimum.

Preferred initial body size:

**9.3–9.5 pt**

Preferred initial line height:

**approximately 1.17–1.22 × font size**

Do not solve fit problems by progressively shrinking text.

### Font weights

Use restrained hierarchy:

- name: bold;
- section headings: bold;
- institution/project/role identifiers: bold;
- normal metadata and body copy: regular;
- limited italics only where already semantically useful.

Avoid excessive bolding within bullets.

## Section styling

Section headings should be uppercase as locked in the content:

- EDUCATION
- RESEARCH EXPERIENCE
- SELECTED PUBLICATIONS
- TECHNICAL SKILLS
- SELECTED TECHNICAL AND TEACHING EXPERIENCE

Use:

- bold section label;
- modest letter spacing if visually useful;
- a thin horizontal rule beneath or aligned with the heading.

Rule weight should remain subtle:

approximately 0.6–0.9 pt.

Do not use colored banners or filled heading boxes.

## Color

Primary production target:

- black or near-black text;
- white page background.

A restrained dark neutral may be used for secondary metadata only if it remains
high-contrast in print and grayscale.

Do not rely on color to convey semantic meaning.

The résumé must remain visually coherent when printed in grayscale.

## Header

### Public tracked review artifact

Show:

**ADAM TROTT**

and a public-safe layout surrogate for the private contact line.

Use a neutral placeholder such as:

`[private phone] | [university email]`

The purpose is to preserve approximately the same vertical structure as the
private artifact.

Do not insert the actual private values into any tracked SVG, PDF, PNG, Markdown,
test fixture, screenshot, or generated preview.

### Private submission artifact

Substitute the exact approved professional contact values from the ignored
private overlay.

Do not include:

- street address;
- ZIP code; or
- personal email.

The private contact line must remain one line.

## Private government-application credential

### Public review artifact

Use a neutral visual surrogate at the locked location immediately after the
Ph.D. education entry.

Use a neutral public-safe surrogate whose measured visual width is deliberately
close to the private replacement.

Initial surrogate:

`[private government application credential - withheld] | Jan. 2026-Present`

This text exists only to preserve visual hierarchy and density.

It is not résumé submission content.

The builder should measure both public and private variants. Ideally both remain
on one line. If their widths differ enough to alter wrapping or vertical flow,
adjust only the public surrogate or presentation geometry and inspect both
artifacts. Do not alter the locked private credential wording merely to make the
public placeholder fit.

### Private submission artifact

Replace the surrogate with the exact locked wording from the ignored private
overlay.

Never expose the exact private credential in:

- tracked source;
- tracked SVG;
- tracked PDF;
- tracked PNG;
- Git diff;
- GitHub preview; or
- repository test snapshots.

## Education layout

The Ph.D. entry should receive strongest visual emphasis.

Recommended hierarchy:

1. institution;
2. degree/program;
3. expected graduation + GPA;
4. private credential/public surrogate;
5. selected coursework.

The B.S. entry follows with modest separation.

The coursework line may wrap, but should remain visually subordinate to the
degree information.

Do not convert coursework into bullets.

## Research layout

Research is the dominant content on page 1.

### Research Assistant

Present as a conventional role heading with dates and one bullet.

### DQNGuard

Give this the strongest project emphasis on the document.

The title should be visually easy to locate.

Keep:

- first-author / venue/status metadata directly associated with the title;
- all three locked bullets together;
- numeric results visually readable without special callout graphics.

Do not turn the `0.865`, `0.745`, `0.701`, or `5%` values into badges,
infographics, or oversized typography.

### HICSS-59 project

Keep the title and publication/presentation metadata together.

Keep both locked bullets together.

Avoid orphaning the project title at the bottom of a page.

## Publications layout

Use hanging-indent or compact scholarly citation formatting.

Do not repeat the full research bullets.

Candidate name may be bolded within each citation if the implementation can do
so without damaging text extraction order.

Do not introduce DOI/URL fields unless the content plan is explicitly reopened
and updated.

## Technical skills layout

Keep the three locked skill categories:

- AI / Machine Learning
- RF / Signal Processing
- Cybersecurity / Systems / Software

Use one compact paragraph per category.

Do not use proficiency bars, star ratings, or columns.

The category label should be bold; skill text should remain regular.

## Technical and teaching experience layout

Maintain this order:

1. NUWC-client Senior Design capstone
2. Cyber Defense and Operations TA
3. Digital Forensics TA

The capstone should clearly retain:

`Client: NUWC Newport`

without visually presenting NUWC as the employer.

The university relationship must remain clear.

## Bullets

Use a simple round or small square bullet.

Preferred bullet-indent geometry:

- bullet x: approximately 45–48 pt;
- text x: approximately 55–59 pt;
- continuation lines align to the text x position.

Keep bullet spacing compact but visibly distinct.

Do not use Unicode glyphs that render unreliably across SVG/PDF engines if a
simple SVG circle or standard bullet character is safer.

## Spacing system

The builder should use named spacing constants rather than arbitrary per-entry
coordinates.

Recommended initial rhythm:

- after section rule: 5–7 pt;
- between entries: 6–9 pt;
- heading to metadata: 1.5–3 pt;
- metadata to first bullet: 3–4.5 pt;
- between bullets: 2.5–4 pt;
- paragraph/skill-category separation: 3–5 pt.

The implementation may tune these values during visual QA while keeping them
systematic.

Avoid large blank gaps inserted solely to balance page bottoms.

## SVG implementation requirements

### Text must remain text

Résumé text must be emitted as SVG text elements.

Do not convert résumé text to vector paths.

Do not rasterize text.

### Wrapping

The builder must perform deterministic line wrapping using actual or
prevalidated font metrics.

Do not rely on browser-specific automatic SVG text wrapping.

Long blocks should be represented with explicit line positions/tspans.

### Reading order

Source order must follow visible reading order.

This is important for:

- PDF text extraction;
- ATS-like processing;
- accessibility; and
- semantic QA.

### Decorative elements

Keep decorative SVG elements minimal:

- horizontal rules;
- optional tiny bullet circles.

No filters, shadows, gradients, masks, clipping effects, or raster backgrounds.

## Builder architecture

The initial implementation should remain small.

Expected builder:

`resumes/applications/nreip2027/resume/build_resume.py`

Expected tracked public-review outputs:

```text
resumes/applications/nreip2027/resume/public/
  nreip2027_resume_public_page1.svg
  nreip2027_resume_public_page2.svg
  nreip2027_resume_public.pdf
  page1.png
  page2.png
  contact_sheet.png
```

Expected ignored private outputs:

```text
resumes/applications/nreip2027/resume/private/
  nreip2027_resume_page1.svg
  nreip2027_resume_page2.svg
  nreip2027_resume.pdf
  page1.png
  page2.png
  contact_sheet.png
```

The existing repository ignore rule for:

`applications/*/resume/private/`

must protect the private output directory.

Before the first private build, verify that rule with `git check-ignore`.

## Content implementation rule

The builder is a renderer, not a writer.

Every résumé-facing string must correspond to:

- the content-locked exact résumé copy in `RESUME_PLAN.md`; or
- an authorized public placeholder/private substitution defined by this
  specification and the ignored private overlay.

No production code may:

- summarize;
- paraphrase;
- rewrite;
- improve;
- shorten;
- expand; or
- invent

résumé content.

If implementation requires a machine-readable content representation, it may
mirror the locked plan, but the plan remains authoritative and the mirror must be
validated against it during build/QA.

## PDF production

Preferred conversion path:

1. generate page 1 SVG;
2. generate page 2 SVG;
3. convert each SVG to PDF with a renderer that preserves selectable text;
4. combine the two pages into one PDF;
5. verify final page size and page count;
6. verify text extraction;
7. render PDF pages to PNG for visual QA.

Do not accept an SVG-to-PDF route merely because it looks correct.

The resulting PDF must retain extractable text.

### Final PDF contract

Private submission PDF must be:

- exactly 2 pages;
- U.S. Letter on both pages;
- less than **1 MB**;
- free of passwords/encryption;
- visually intact;
- text searchable/selectable;
- free of clipped or overlapping text.

Because the résumé is primarily vector text, the normal expected PDF size should
be comfortably below the 1 MB limit.

Do not reduce legibility or rasterize the document merely to satisfy the size
limit.

## Semantic QA

The build/QA workflow must verify at minimum:

### Page structure

- exactly two PDF pages;
- page dimensions approximately 612 × 792 pt each.

### Text extraction

Run an independent text extraction step against the produced PDF.

Verify that extracted text includes, at minimum:

- ADAM TROTT;
- University of Massachusetts Dartmouth;
- DQNGuard;
- open-world RF preliminary-action detection;
- 0.865;
- RadioML 2018.01A;
- NUWC Newport;
- Cyber Defense and Operations;
- Digital Forensics.

Private build QA must additionally verify the presence of the authorized private
contact and credential values without printing those values to a tracked log.

Public build QA must verify that exact private values are absent.

### Content integrity

Compare the rendered/extracted résumé against the locked content.

Any missing bullet, duplicated block, changed number, changed publication title,
or altered status is a build failure.

### Font/text behavior

Verify that:

- text is selectable;
- extracted characters are sensible;
- no important text has been converted into unidentified vector shapes;
- no replacement glyph boxes appear.

## Visual QA

Render the final PDF at a minimum of approximately 150–200 DPI.

Create:

- page 1 PNG;
- page 2 PNG; and
- a two-page contact sheet.

Inspect for:

- clipping;
- overlap;
- awkward wrapping;
- overly tight leading;
- inconsistent indentation;
- excessive whitespace;
- weak hierarchy;
- stranded headings;
- bullets split incorrectly;
- inconsistent date alignment;
- text too close to page edges;
- page imbalance severe enough to harm readability;
- broken punctuation/glyphs.

A successful script exit is not evidence of visual correctness.

For the final private PDF, perform a secondary-renderer sanity check when a
second independent PDF renderer is available. The objective is to catch
renderer-specific clipping, glyph substitution, font behavior, or layout
differences before submission.

A renderer disagreement that materially changes text or layout is a QA failure
until understood.

## Public/private parity QA

The public and private layouts should be structurally equivalent.

Differences should be limited to authorized substitutions:

- contact placeholder ↔ private professional contact line;
- government-credential surrogate ↔ exact private credential.

If a private substitution changes wrapping or vertical flow, inspect both builds.

The final private artifact, not the public preview, governs submission readiness.

## Artifact-size QA

Before submission, check the final private PDF byte size.

Acceptance condition:

`size < 1,000,000 bytes`

Use the portal's strict language rather than assuming a binary-megabyte
interpretation.

If the PDF unexpectedly exceeds the threshold:

1. identify the cause;
2. remove unnecessary embedded/raster data;
3. rebuild;
4. re-run text and visual QA.

Do not solve size problems by degrading text into low-resolution images.

## Portal submission QA

After the private artifact passes local QA:

1. upload the private PDF through the NREIP portal;
2. use **Upload and Save**;
3. download the server-side copy using the portal-provided link;
4. verify that the downloaded file opens;
5. verify page count and file identity;
6. visually inspect the downloaded copy when practical.

The local build alone does not establish successful portal receipt.

## Production failure policy

Stop and report rather than silently compensating if any of the following occur:

- locked content does not fit the assigned two-page structure;
- body text would need to fall below the minimum size;
- a page overflows;
- PDF text extraction is materially broken;
- selected font is unavailable and fallback metrics differ materially;
- a private field would leak into tracked output;
- PDF exceeds the portal size limit for an unexplained reason;
- visual QA reveals clipping, overlap, or hierarchy defects.

A fit failure is evidence that either the production specification or the
content plan needs an explicit revision. It is not permission for the builder to
rewrite the résumé.

## First-build success criteria

The first implementation is successful when:

- public two-page SVG source exists;
- public PDF exists;
- public page renders/contact sheet exist;
- private two-page SVG source exists locally and remains ignored;
- private PDF exists locally and remains ignored;
- private contact and credential substitutions are correct;
- page assignment matches this specification;
- PDF text remains extractable;
- no locked content has changed;
- visual review finds no clipping or overlap;
- final private PDF is less than 1 MB; and
- Git status demonstrates that no private artifact is tracked.

Only after those conditions are demonstrated should the NREIP résumé production
workflow be described as operational.
