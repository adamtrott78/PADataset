# MILCOM 2026 SVG sources

Twelve standalone 1920×1080 slides implement `../SVG_PRODUCTION_SPEC.md`.
The planning documents and canonical scientific assets are unchanged.

| Slide | SVG | Status |
|---|---|---|
| 1 | `slide01_title.svg` | Complete |
| 2 | `slide02_closed_set_gap.svg` | Complete |
| 3 | `slide03_pa_taxonomy.svg` | Five approved OTA placeholders |
| 4 | `slide04_ota_dataset.svg` | Fifteen approved protocol/behavior image slots |
| 5 | `slide05_operating_requirement.svg` | Complete |
| 6 | `slide06_dqnguard_architecture.svg` | Canonical s23 vector artwork embedded |
| 7 | `slide07_surrogate_calibration.svg` | Complete |
| 8 | `slide08_main_results.svg` | Complete |
| 9 | `slide09_target_surrogate_matrix.svg` | Canonical matrix PNG embedded unchanged |
| 10 | `slide10_surrogate_diagnostics.svg` | Complete |
| 11 | `slide11_multi_surrogate_future.svg` | Complete; proposals explicitly marked future work |
| 12 | `slide12_takeaways.svg` | Complete; canonical matrix thumbnail embedded |

## Rebuild

From the repository root:

```sh
python presentations/milcom2026/tools/build_svg_slides.py
```

Dependencies: Python 3 with Pillow, fontconfig (`fc-match`), and Poppler
(`pdftocairo`). The builder uses the local Arial fallback for text measurement;
slide text declares `Arial, Helvetica, sans-serif` and has no external font or CSS
dependency. It builds slides in numerical order, checks XML, unique IDs, text
sizes and estimated text bounds, and writes only the twelve slide SVGs.

Slide 6 is converted directly from
`../assets/figures/hero_dqnguard_pipeline_s23_tikz.pdf`; its full vector artwork,
including PDF glyph outlines, is embedded without scientific redrawing.
Slides 9 and 12 embed the original bytes of
`../assets/figures/target_surrogate_unknown_f1_matrix.png`.

## Production choices and remaining work

- Slides 3–4 await real OTA images. Their stable `*_ota_slot` groups identify the
  reserved frames. No RF examples were fabricated. Supply images and update the
  builder when those assets become available.
- Slide 2 uses repeated, identically labeled known/novel input boxes. The plan
  allows thumbnails when appropriate assets exist; none are supplied for these
  conceptual cases.
- Long titles use the specified 52 px, two-line treatment where necessary.
  Line breaks within labels preserve wording. Optional supporting text is
  omitted on Slides 7–8 to retain the specified content geometry.
- Slide 8's suggested y-domain is expanded to 0.48–1.03 so all specified SD bars
  are visible without clipping. The axis extension shows statistical spread;
  it does not imply that F1 observations can exceed 1. Means and SDs are unchanged.
- The canonical scientific assets retain their original fonts, colors, and
  aspect ratios, as required by the asset-preservation rules. Surrounding slide
  elements use the locked deck palette and font stack.
- Slide 11's goal is placed in the bottom text zone, with its future cards kept
  at the specified positions. This resolves the spec's request for a goal line
  across a row whose cards already extend to y=980.

Validation: all twelve SVGs parse, text sizes and safe-area bounds were checked,
and Inkscape's vector object queries were used to check actual slide-text bounds
and pairwise text overlaps. Embedded matrix bytes were compared to the canonical
PNG. Full-slide PNG preview generation was omitted following the user's request;
the deck has not been visually reviewed in PowerPoint. No unresolved generation
blockers remain; real OTA asset insertion and PowerPoint assembly are pending.
