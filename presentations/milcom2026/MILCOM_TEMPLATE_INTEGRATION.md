# MILCOM 2026 Official Template Integration

This file is the presentation-branding and slide-frame authority for the MILCOM 2026 deck.

It overrides the older custom background/title treatment in SVG_PRODUCTION_SPEC.md while preserving that file's scientific/body-layout authority.

## Official source assets

The conference-provided files are committed unchanged under:

- presentations/milcom2026/assets/template/milcom26-ppt-template_v1_25feb26_jb.pdf
- presentations/milcom2026/assets/template/milcom26-ppt-template_v1_25feb26_jb.pptx

The PDF is the deterministic rendering source for SVG production.
The PPTX remains the source to use when the final PowerPoint package is assembled.

Do not redraw, recolor, crop, or substitute the MILCOM or IEEE ComSoc branding.

## Template page roles

The official PDF has four 16:9 pages:

1. blank title-slide background with MILCOM and IEEE ComSoc branding;
2. blank content-slide background with branded header and conference footer;
3. populated welcome/title example;
4. populated content-slide example.

Production uses page 1 for Slide 1 and page 2 for Slides 2–12.
Pages 3–4 are visual examples only.

## Geometry

The canonical slide coordinate system remains:

- width: 1920
- height: 1080
- viewBox: 0 0 1920 1080

This matches the existing SVG deck and the official conference template.

For content slides:

- the official header occupies approximately y = 0–160;
- the existing white body starts below the header;
- the official conference footer remains visible near the bottom edge;
- scientific/body objects retain their existing coordinates unless a later visual QA pass identifies a real collision.

## Content-slide title treatment

The official content-slide header owns the title.

Title rules:

- x = 56
- maximum title width before the conference logos = 1100 px
- font family = Calibri, Arial, sans-serif
- color = #002856
- one-line title: approximately 48 px
- long title: automatically reduced/wrapped to at most two lines
- one-line baseline = y 88
- two-line baselines = y 59 and y 110

Do not move the MILCOM or IEEE ComSoc logos to create extra title width.
Do not shorten a scientific conclusion title solely for the template.

The existing optional supporting sentence remains in the white body below the official header.

## Title slide

Slide 1 uses official template page 1 as the complete background.

The old custom "MILCOM 2026" conference tag is removed because the official MILCOM logo already provides that identity.

The existing title, subtitle, author block, and DQNGuard hero diagram remain the content authority unless the user explicitly requests a redesign.

## Scientific/body content

The following remain governed by SVG_PRODUCTION_SPEC.md and the presentation plan:

- slide narrative and conclusion titles;
- scientific numbers;
- panel/diagram geometry;
- semantic colors;
- arrows and claim-sensitive relationships;
- OTA imagery;
- DQNGuard camera-ready hero;
- Target–Surrogate Matrix;
- future-work labeling.

Template integration must not change scientific content.

## Deterministic build

Canonical rebuild command from the repository root:

    python presentations/milcom2026/tools/build_milcom26_svg_slides.py

The wrapper performs:

1. build_svg_slides.py — rebuild locked scientific/body SVGs;
2. apply_milcom26_template.py — apply the official title/content backgrounds and header-title treatment.

The template applicator is idempotent and may be rerun.

## Dependencies

In addition to the existing SVG builder dependencies:

- pdftocairo must be available to render the committed official template PDF;
- fontconfig must resolve Calibri or a metrics-compatible fallback such as Carlito;
- Pillow is used for title measurement and template-render validation.

## Static acceptance checks

After the wrapper runs, every slide must satisfy:

- 1920x1080 viewBox;
- exactly one official MILCOM template background;
- Slide 1 uses official page 1;
- Slides 2–12 use official page 2;
- no redundant custom conference tag on Slide 1;
- content-slide titles stay left of the official logos;
- content-slide titles use at most two lines;
- the conference footer remains visible;
- no scientific/body object is clipped or hidden by the template;
- all prior scientific-claim and asset-preservation checks still pass.

A source change is not proof that the deck rendered correctly.
Render the rebuilt SVGs to PNG and visually inspect the complete twelve-slide contact sheet before treating the migration as complete.
