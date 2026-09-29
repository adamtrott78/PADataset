# Presentation Assets

This directory contains presentation-specific visual assets for the MILCOM 2026 deck.

The rendering contract is:

`../SVG_PRODUCTION_SPEC.md`

The scientific/design provenance is:

`../PRESENTATION_PLAN.md`

## Current tree

```text
assets/
├── figures/
│   ├── hero_dqnguard_pipeline_s23_tikz.pdf
│   └── target_surrogate_unknown_f1_matrix.png
├── ota/
│   ├── wifi/
│   ├── bluetooth/
│   └── zigbee/
├── template/
│   ├── milcom26-ppt-template_v1_25feb26_jb.pdf
│   ├── milcom26-ppt-template_v1_25feb26_jb.pptx
│   └── template.md
└── README.md
```

## Figure assets

### DQNGuard hero

Use:

`figures/hero_dqnguard_pipeline_s23_tikz.pdf`

This is the camera-ready presentation asset for Slide 6. Convert it to SVG/vector for slide construction while preserving the original artwork. Do not substitute an older hero revision.

### Target–Surrogate Matrix

Use:

`figures/target_surrogate_unknown_f1_matrix.png`

This is the reviewed presentation asset for Slide 9. Do not manually reconstruct its scientific values from memory. If a vector version is later required, regenerate it from the reviewed paper/result provenance rather than retyping cells.

## Official MILCOM 2026 template

Use the committed conference files under `template/`.

- the PDF is the deterministic visual source for SVG background/header/footer integration;
- the PPTX is the conference template source for final PowerPoint assembly;
- PDF page 1 is the blank title background;
- PDF page 2 is the blank content background;
- PDF pages 3–4 are populated examples and are not used as production backgrounds.

Do not modify the official template files in place. The integration contract is `../MILCOM_TEMPLATE_INTEGRATION.md`.

## OTA imagery

The `ota/` protocol folders are reserved for real examples generated from the OTA tapes.

Expected use:

- Slide 3: representative behavior examples for Scan, Burst, Sustain, Hop, Replay;
- Slide 4: the 3×5 protocol/behavior matrix.

Do not fabricate scientific spectrograms or substitute generic stock RF imagery. The fixed slide geometry is already specified, so the image slots may remain neutral placeholders until the real OTA assets are generated.

## Naming / provenance rule

For any new presentation asset:

- use a descriptive filename tied to the scientific role;
- record the source/generation path when the asset contains scientific data;
- prefer reviewed vector sources where practical;
- do not silently replace a reviewed figure with an older revision because it is easier to render.