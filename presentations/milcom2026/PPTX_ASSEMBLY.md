# MILCOM 2026 PowerPoint Assembly

This is the deterministic final-assembly contract for the MILCOM 2026 DQNGuard deck.

## Goal

Produce the actual conference `.pptx` from the approved slide renders while preserving:

- the official MILCOM 2026 PowerPoint template lineage;
- the exact approved 1920x1080 slide appearance;
- 16:9 geometry;
- the canonical spoken script as PowerPoint speaker notes.

The final visual slide is intentionally a full-slide PNG. The scientific/body SVGs remain the editable/reproducible source; the PowerPoint is the delivery artifact. This avoids PowerPoint reflow, font substitution, SVG-import differences, or accidental movement of scientific objects after visual QA.

## Authorities

Visual source:

`tools/build_milcom26_svg_slides.py`

Official template:

`assets/template/milcom26-ppt-template_v1_25feb26_jb.pptx`

Speaker notes:

- Slide 1: `SVG_PRODUCTION_SPEC.md` -> `Opening script`
- Slides 2-12: `SCRIPT.md` -> `Script` / `Consolidated script`

Assembler:

`tools/assemble_milcom26_pptx.py`

## Required input renders

The assembler expects exactly twelve PNGs named:

`slide01_*.png` through `slide12_*.png`

Every image must be exactly 1920x1080.

Generate them from the final template-integrated SVGs after visual QA. Do not assemble from stale pre-template previews.

## Assembly behavior

The assembler:

1. opens the committed official MILCOM 2026 `.pptx`;
2. verifies the template is 16:9;
3. reuses the official package/master/layout/theme lineage;
4. ensures the deck contains twelve slides;
5. clears template-example shapes from each delivery slide;
6. places one approved 1920x1080 render edge-to-edge on each slide;
7. embeds the canonical narration into PowerPoint speaker notes;
8. writes presentation metadata;
9. reopens the saved deck and verifies:
   - exactly twelve slides;
   - unchanged 16:9 dimensions;
   - exactly one full-slide image per slide;
   - non-empty speaker notes on Slides 1-12.

## Dependency

Python environment must provide:

- Pillow
- python-pptx

The SVG/render workflow still requires the dependencies documented in `MILCOM_TEMPLATE_INTEGRATION.md`.

## Example

From the repository root:

```sh
python presentations/milcom2026/tools/assemble_milcom26_pptx.py \
  --png-dir "$HOME/adamArchives/Adam/MILCOM2026_FINAL/slides" \
  --output "$HOME/adamArchives/Adam/MILCOM2026_FINAL/DQNGuard_MILCOM2026_official_template.pptx"
```

## Acceptance criteria

The final PowerPoint is acceptable only when:

- it opens successfully as a PowerPoint presentation;
- slide count is 12;
- slide size is 16:9;
- each visible slide exactly matches its approved PNG render;
- all 12 slides contain the expected speaker notes;
- the official template file remains unchanged in the repository;
- the final `.pptx` is written outside the Git worktree unless the user explicitly requests it be committed.
