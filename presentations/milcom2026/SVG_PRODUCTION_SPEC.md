# MILCOM 2026 SVG Production Specification

This file is the rendering contract for the MILCOM 2026 presentation.

It is intentionally narrower than `PRESENTATION_PLAN.md`:

- `PRESENTATION_PLAN.md` remains the scientific/design provenance and explains *why* each slide exists.
- `SCRIPT.md` remains the narration source for Slides 2–12.
- **This file governs how the locked concepts are rendered as 16:9 SVG slides.**

If a rendering choice here conflicts with a scientific claim or number in `PRESENTATION_PLAN.md`, the scientific plan wins. If an older `PRESENTATION_PLAN.md` status still calls Slide 1 `TBD`, treat that marker as stale: **Slide 1 is now concept locked by this specification.**

The camera-ready submitted paper is the authority for the title-page author/affiliation block. Nathaniel D. Bastian is listed with Johns Hopkins University; Adam Trott, Cameron Popillo, Roulin Zhou, and Gokhan Kul are listed with the University of Massachusetts Dartmouth.

---

# 1. Output contract

## File format

Create one standalone SVG per main slide.

Recommended filenames:

```text
slide01_title.svg
slide02_closed_set_gap.svg
slide03_pa_taxonomy.svg
slide04_ota_dataset.svg
slide05_operating_requirement.svg
slide06_dqnguard_architecture.svg
slide07_surrogate_calibration.svg
slide08_main_results.svg
slide09_target_surrogate_matrix.svg
slide10_surrogate_diagnostics.svg
slide11_multi_surrogate_future.svg
slide12_takeaways.svg
```

## Canvas

- width: `1920`
- height: `1080`
- aspect ratio: `16:9`
- SVG root: `viewBox="0 0 1920 1080"`

## Safe area

- left: `96 px`
- right: `96 px`
- top: `64 px`
- bottom: `60 px`
- usable width: `1728 px`

Standard vertical zones:

```text
y = 64–140      slide title
y = 145–195     optional supporting sentence
y = 220–985     primary content
y = 1000–1035   optional tiny footer / provenance only
y > 1035        do not place important content
```

Use a conceptual 12-column alignment grid with `24 px` gutters. Do not draw the grid.

---

# 2. SVG implementation rules

Use SVG 1.1-compatible primitives that survive browser rendering and PowerPoint import.

Preferred:

- `<rect>`
- `<line>`
- `<polyline>` / `<path>`
- `<circle>`
- `<text>` and `<tspan>`
- `<image>` only for reviewed raster assets
- `<g>` for all logical object groups
- one simple arrowhead marker in `<defs>` if useful

Avoid:

- `<foreignObject>`
- external CSS
- external fonts
- complex filter effects
- masks/clipping unless absolutely necessary
- converting all text to outlines
- embedded stock icons
- heavy drop shadows
- gradients without a scientific reason

Prefer explicit attributes over CSS classes so a downstream editor can understand the SVG without another stylesheet.

Every major object group should have a useful `id` matching the group hierarchy in this file.

---

# 3. Deck-wide visual system

## Background and ink

| Semantic role | Color |
|---|---|
| Background | `#F7F9FC` |
| Primary ink | `#102235` |
| Secondary text | `#5D6C7B` |
| Light border | `#D8E1EA` |
| Neutral panel | `#EEF3F7` |
| DQNGuard / proposed method | `#1F6FEB` |
| Known / retained evidence | `#2E8B57` |
| Unknown / target unknown | `#C63D4F` |
| Surrogate-open | `#E39A27` |
| Future work | `#6C5CE7` |
| Disabled / comparison gray | `#8A98A8` |

Color semantics are global:

- green = known / retained evidence
- red = true unknown / rejected target behavior
- amber = surrogate-open evidence
- blue = DQNGuard / proposed method
- purple = future architecture

Color must never be the only differentiator. Pair it with labels, borders, glyphs, or line patterns.

## Typography

Font stack:

```text
Arial, Helvetica, sans-serif
```

Do not depend on custom fonts.

| Role | Size | Weight |
|---|---:|---:|
| Slide title | 58–62 px | 700 |
| Very long title | 50–56 px | 700 |
| Supporting sentence | 29–31 px | 400 |
| Major panel heading | 29–32 px | 700 |
| Normal body / labels | 24–27 px | 400 |
| Strong body label | 24–27 px | 700 |
| Small annotation | 20–22 px | 400 |
| Pill / category tag | 19–21 px | 700 |
| Hero metric | 72–92 px | 700 |

Minimum meaningful presentation text: `20 px`.

Do not place paragraphs on-slide. Use real SVG text wherever practical.

## Shape grammar

Cards/panels:

- fill: white
- border: `2 px #D8E1EA`
- corner radius: `18 px`
- no heavy shadow

Small pills:

- corner radius: `12 px`
- light semantic tint
- semantic-color border/text

Arrows/connectors:

- `4 px`
- rounded joins/caps
- filled arrowhead
- primary ink unless a semantic color is important

Dividers:

- `2 px #D8E1EA`

## Visual hierarchy rule

Each slide must have exactly one obvious first-read object.

A viewer at the back of the room should recover the slide from:

**title → dominant visual → one annotation**

Do not turn the deck into a generic corporate card template. Cards are a containment device, not the dominant visual language.

## Results terminology

Audience-facing labels are fixed:

- `Unknown F1`
- `OSR macro F1`
- `known rejection`
- `AUROC`

Use behavior names:

`Scan / Burst / Sustain / Hop / Replay`

Do not show PA1/PA2/etc. on normal audience-facing slides.

Use:

`USRP N210`

not `Ettus N210`.

Use:

`DQN-IDS-style head`

not the internal Shreyash label.

---

# 4. Asset policy

## Slide 6 hero figure

Presentation-ready asset:

`presentations/milcom2026/assets/figures/hero_dqnguard_pipeline_s23_tikz.pdf`

This is the preferred slide asset. Convert the PDF to SVG/vector while preserving text and linework. Do not substitute older s1–s22 artwork.

## Slide 9 Target–Surrogate Matrix

Presentation asset:

`presentations/milcom2026/assets/figures/target_surrogate_unknown_f1_matrix.png`

Use this reviewed asset directly unless a vector regeneration is intentionally performed from the canonical paper generator/provenance. Do not manually retype/reconstruct the scientific values from memory.

## OTA imagery for Slides 3–4

Reserved asset tree:

```text
presentations/milcom2026/assets/ota/
  wifi/
  bluetooth/
  zigbee/
```

The final OTA thumbnails are not required to lock the layout. **Do not invent synthetic scientific examples as substitutes.** During production, either:

1. populate the fixed image slots from the real OTA assets when they are generated, or
2. leave clearly labeled neutral placeholder frames until the real assets are supplied.

Slide 1 is the only place where a stylized non-scientific RF trace is allowed; it is decorative context and must not be presented as measured data.

---

# 5. Shared title treatment for Slides 2–12

Unless a slide below overrides it:

- title bounding box: `x=96, y=64, w=1728, h=76`
- title baseline near `y=116`
- title fill: primary ink
- supporting sentence: `x=96, y=150, w=1728, h=52`
- supporting baseline near `y=186`
- supporting fill: secondary text

For a title that must wrap to two lines, reduce to `50–54 px` and keep the full title block within `y=64–160`; then move supporting text to `y=168–218` and primary content down to approximately `y=238`.

No slide numbers in the main deck.

---

# 6. Slide 1 — Title

## Status

**CONCEPT LOCKED**

## Exact title

**DQNGuard: Towards Open-World RF Preliminary-Action Detection**

Use the accepted/camera-ready paper title exactly.

## Composition

Use a `58 / 42` left/right split.

### Left title region

- region: `x=96, y=64, w=1010, h=900`
- conference tag: `x=100, y=78`, 22 px bold
- tag text: `MILCOM 2026`
- title starts around `x=96, y=165`
- preferred title lines:

```text
DQNGuard: Towards
Open-World RF
Preliminary-Action Detection
```

- title: `70–74 px`, weight 700, line-height approximately `1.04`
- color only the word `DQNGuard` blue; remainder primary ink

Subtitle:

**Open-set recognition for over-the-air RF behavioral evidence**

- approximately `x=96, y=455`
- `30 px`, regular, secondary text

Author group:

- presenter baseline around `y=825`
- `Adam Trott` — `30 px`, weight 700
- coauthors baseline around `y=870`
- `Cameron Popillo • Nathaniel D. Bastian • Roulin Zhou • Gokhan Kul` — `22–24 px`
- affiliation baseline around `y=910`
- `University of Massachusetts Dartmouth • Johns Hopkins University` — `21–22 px`, secondary text

Do not add university logos in the first production pass.

### Right hero region

Hero bounding region:

- `x=1180, y=205, w=644, h=680`

This is a minimal conceptual preview, not Slide 6 compressed.

Stage 1 — RF observation:

- card: `x=1260, y=235, w=480, h=150`
- label: `RF observation`
- stylized waveform/spectral trace inside; decorative only

Stage 2 — classifier:

- arrow down
- node: `x=1330, y=445, w=340, h=100`
- text: `PA classifier`
- neutral blue-gray treatment

Stage 3 — DQNGuard:

- arrow down
- node: `x=1300, y=615, w=400, h=120`
- blue fill/tint
- text: `DQNGuard`
- this is the visual center

Stage 4 — split:

- one branch left, one right
- known node: `x=1205, y=825, w=270, h=105`
- green outline
- text: `KNOWN PA` with small checkmark
- unknown node: `x=1525, y=825, w=270, h=105`
- red outline
- text: `UNKNOWN` with question-mark/unfamiliar-signal glyph

## Object hierarchy

```text
slide01
├── background
├── conference_tag
├── title_group
│   ├── title_dqnguard
│   ├── title_remaining_lines
│   └── subtitle
├── author_group
│   ├── presenter
│   ├── coauthors
│   └── affiliations
└── hero_group
    ├── rf_observation_card
    │   ├── label
    │   └── decorative_trace
    ├── arrow_rf_to_classifier
    ├── classifier_node
    ├── arrow_classifier_to_guard
    ├── dqnguard_node
    ├── branch_connector
    ├── known_node
    └── unknown_node
```

## Forbidden additions

Do not show on Slide 1:

- DQN internals
- confidence features
- variance/energy bands
- surrogate calibration
- five PA classes
- protocol matrix
- performance metrics

Conceptual promise only:

**RF comes in → classifier + DQNGuard → retain known behavior or isolate unknown behavior.**

## Opening script

Target: approximately 20–25 seconds.

> Good morning. I'm Adam Trott from the University of Massachusetts Dartmouth. This work asks a simple question: when an RF behavior falls outside what a classifier was trained to recognize, can we detect that novelty without throwing away the known evidence that we still trust? We address that problem with DQNGuard, an open-set decision layer for RF Preliminary-Action recognition.
>
> The problem starts with a limitation of conventional closed-set classifiers.

---

# 7. Slide 2 — Closed-set RF classifiers cannot say “I don't know”

## Dominant visual

Two-panel closed-set/open-world contrast.

## Geometry

Primary content begins at `y=235`.

- left panel: `x=96, y=235, w=840, h=710`
- right panel: `x=984, y=235, w=840, h=710`
- panel gap: `48 px`

Panel heading region:

- heading baseline around `y=285`
- allowed-output row around `y=345`

Case 1 card:

- `y=395, h=205`

Case 2 card:

- `y=635, h=220`

Bottom callout:

- `y=880–925`

## Left panel

Heading:

**CLOSED-SET CLASSIFIER**

Allowed outputs:

`Scan | Burst | Hop`

Known case:

`Known Burst behavior → RF classifier → Burst ✓`

Novel case:

`Novel RF behavior → RF classifier → forced known prediction: Hop ✕`

Bottom callout:

**“Unknown” is not an available output.**

The wrong class label is visually secondary; the absence of UNKNOWN is the point.

## Right panel

Heading:

**OPEN-WORLD REQUIREMENT**

Allowed outputs:

`Scan | Burst | Hop | UNKNOWN`

Known case:

`Known Burst behavior → open-world decision → Burst ✓`

Novel case:

`Novel RF behavior → open-world decision → UNKNOWN ✓`

Bottom callout:

**Preserve known evidence. Isolate unfamiliar behavior.**

## Visual rules

- repeat the *same* known and novel input thumbnails in both panels
- align cases horizontally across panels
- known-case output uses green
- novel closed-set wrong output is muted red/gray
- UNKNOWN on the right uses strong red outline/text
- do not introduce all five final classes

## Object hierarchy

```text
slide02
├── title_group
├── supporting_sentence
├── closed_set_panel
│   ├── heading
│   ├── allowed_outputs
│   ├── known_case
│   ├── novel_case
│   └── closed_set_callout
└── open_world_panel
    ├── heading
    ├── allowed_outputs
    ├── known_case
    ├── novel_case
    └── open_world_callout
```

---

# 8. Slide 3 — Preliminary Actions capture RF behavior, not final attack labels

## Dominant visual

Five equal behavior cards.

## Geometry

Card row:

- top: `y=255`
- card height: `545`
- gap: `24`
- card width: approximately `326`

Card x positions:

```text
Scan     x=96
Burst    x=446
Sustain  x=796
Hop      x=1146
Replay   x=1496
```

Each card:

- title area: `y=278–325`
- image slot: approximately `x+18, y=340, w=290, h=300`
- description: `y=675–745`

Bottom contrast band:

- `y=835, h=115`
- left half: `x=96, w=840`
- right half: `x=984, w=840`

Optional tiny footer near `y=990` only if needed.

## Exact card text

**Scan**  
Discovery-like activity

**Burst**  
Short transmissions + quiet gaps

**Sustain**  
Persistent channel occupancy

**Hop**  
Frequency dwell + revisits

**Replay**  
Repeated waveform / template

Bottom labels:

**WHAT IT TELLS US**  
Observable RF behavior

**WHAT IT DOES NOT CLAIM**  
Final attack-technique attribution

Optional footer:

**Same behavioral taxonomy evaluated across WiFi, Bluetooth, and Zigbee.**

## Asset rule

Real OTA/dataset examples are preferred. Until they exist, keep the image slots neutral and labeled `OTA RF example pending`. Do not invent scientific spectrograms.

## Object hierarchy

```text
slide03
├── title_group
├── supporting_sentence
├── behavior_cards
│   ├── scan_card
│   ├── burst_card
│   ├── sustain_card
│   ├── hop_card
│   └── replay_card
├── tells_us_box
├── does_not_claim_box
└── optional_protocol_footer
```

---

# 9. Slide 4 — We evaluate the same five behaviors over-the-air across three protocol families

## Dominant visual

3×5 protocol/behavior matrix, with a compact OTA capture pipeline on the right.

## Geometry

Left matrix region:

- `x=96, y=245, w=1135, h=670`

Right capture region:

- `x=1275, y=245, w=549, h=670`

Left matrix label:

**5 BEHAVIORS × 3 PROTOCOLS**

- centered over left region near `y=275`

Matrix row labels:

- label column approximately `x=96–210`
- `WiFi`
- `Bluetooth`
- `Zigbee`

Matrix behavior columns:

- `Scan`
- `Burst`
- `Sustain`
- `Hop`
- `Replay`

Use five equal columns from approximately `x=225` to `x=1215` with `16–18 px` gaps.

Use three equal thumbnail rows between approximately `y=350` and `y=870`.

Right pipeline heading:

**OTA CAPTURE**

Pipeline nodes centered around `x=1549`:

```text
USRP N210 TX
     ↓
over the air
     ↓
USRP N210 RX
     ↓
32 ms RF window
     ↓
classifier input
```

Key-fact block at bottom of right region:

```text
12.5 MS/s
400,000 complex IQ samples / window
2.437 GHz
2× USRP N210 SDRs
```

## Asset rule

Do not block deck production on the 15 OTA images. Geometry is final now. Populate the cells later from `assets/ota/`.

Until then, use neutral image slots carrying only protocol/behavior labels. Never synthesize fake measured RF data.

## Object hierarchy

```text
slide04
├── title_group
├── supporting_sentence
├── dataset_matrix
│   ├── matrix_heading
│   ├── column_labels
│   ├── row_labels
│   └── fifteen_image_slots
└── ota_capture_panel
    ├── heading
    ├── tx_node
    ├── over_air_connector
    ├── rx_node
    ├── window_node
    ├── classifier_input_node
    └── capture_facts
```

---

# 10. Slide 5 — Unknown detection is only useful if known behavior stays usable

## Dominant visual

Three-column conceptual story. The third panel is visually strongest.

## Geometry

Panels:

- left: `x=96, y=250, w=560, h=675`
- middle: `x=680, y=250, w=560, h=675`
- right: `x=1264, y=250, w=560, h=675`
- gap: `24 px`

Use a stronger `4 px` blue top rule or blue outline on the right panel.

## Left — VarMax

Heading:

**VARMAX — SCORE-BASED REJECTION**

Flow centered vertically:

```text
classifier evidence
       ↓
unknownness score
       ↓
threshold
       ↓
known / unknown
```

Bottom tags:

**✓ useful unknownness evidence**

**✕ threshold choice can sacrifice known samples**

## Middle — DQN-style confidence head

Heading:

**DQN-STYLE CONFIDENCE HEAD**

Use one state block, one learned-decision block, one output:

```text
P1
P1 − P2
H(p)
  ↓
learned decision
  ↓
known / unknown
```

Bottom tags:

**✓ learned decision boundary**

**✕ no explicit guarantee on known rejection**

No arrow may cross from this panel into the right panel.

## Right — operational requirement

Heading:

**WHAT DEPLOYMENT ACTUALLY NEEDS**

Center:

```text
Detect unknowns
      +
Preserve known classifications
      ↓
EXPLICIT KNOWN-REJECTION BUDGET
```

Callout:

**Reject unfamiliar behavior — but only within a controlled known-sample cost.**

## Object hierarchy

```text
slide05
├── title_group
├── supporting_sentence
├── varmax_panel
├── dqn_style_panel
└── operating_requirement_panel
```

---

# 11. Slide 6 — DQNGuard adds a budgeted open-world decision layer to the PA classifier

## Dominant visual

The camera-ready DQNGuard hero figure.

## Geometry

- imported figure frame: `x=110, y=245, w=1700, h=690`
- preserve original aspect ratio
- center vertically inside the frame
- do not crop labels

Supporting sentence:

**DQNGuard decides whether the classifier's prediction conforms to learned known behavior.**

## Asset

Use:

`presentations/milcom2026/assets/figures/hero_dqnguard_pipeline_s23_tikz.pdf`

Convert to SVG/vector for the slide while preserving the original artwork.

Do not redraw the architecture from scratch.

The following content must remain legible:

- RF Input
- IQ / FFT / DCT / Polar
- PA CNN
- prediction / logits / softmax / feature outputs
- predicted-class calibration
- guard evidence
- known-budget threshold
- `β = 0.05`
- Known PA / Unknown behavior
- downstream CWoS consumer path

## Object hierarchy

```text
slide06
├── title_group
├── supporting_sentence
└── hero_figure_s23
```

If progressive reveal is later desired, animate only an overlay/highlight in PowerPoint. The static SVG must show the complete figure.

---

# 12. Slide 7 — A surrogate unknown shapes the DQN; the true unknown remains unseen until test

## Dominant visual

One vertical leave-two-out calibration flow with explicit color-coded roles.

## Geometry

Role strip near top of content:

- `y=238–300`
- surrogate pill: amber, text `Surrogate: Scan`
- target pill: red, text `Target: Sustain`
- known pill: green, text `Known: Burst / Hop / Replay`

Backbone training node:

- `x=730, y=320, w=460, h=110`
- text: `3-class PA backbone`
- second line: `Burst | Hop | Replay`

Calibration split:

Known calibration card:

- `x=350, y=485, w=470, h=120`
- green accent
- text: `KNOWN CALIBRATION` / `Burst • Hop • Replay`

Surrogate calibration card:

- `x=1100, y=485, w=470, h=120`
- amber accent
- text: `SCAN SURROGATE` / `withheld from backbone training`

Both feed:

- `FIT DQN CONFIDENCE HEAD`
- `x=730, y=645, w=460, h=105`
- sublabel: `known + surrogate states`

Known-only fitting row:

- left: `x=385, y=790, w=500, h=95`
- text: `FIT GUARD BANDS ON KNOWN ONLY`
- right: `x=1035, y=790, w=500, h=95`
- text: `SET 5% THRESHOLD ON KNOWN ONLY`

Final evaluation block:

- `x=570, y=910, w=780, h=90`
- text: `FINAL EVALUATION: known test + Sustain target unknown`
- small red/gray note: `Scan surrogate is not included in final test metrics.`

## Arrow rules

- backbone feeds both calibration cards
- both calibration cards feed DQN fitting
- known calibration additionally feeds both known-only fitting boxes
- the surrogate must **not** have an arrow directly into the known-only threshold box
- target Sustain appears only at the final evaluation stage

## Scientific text that must remain explicit

```text
DQN fitting: known + surrogate-open calibration
Guard bands: known calibration only
5% final threshold: known calibration only
Final test: known test classes + target unknown
```

## Object hierarchy

```text
slide07
├── title_group
├── supporting_sentence
├── role_strip
├── backbone_node
├── known_calibration_node
├── surrogate_calibration_node
├── dqn_fit_node
├── known_guard_fit_node
├── known_threshold_node
├── final_evaluation_node
└── role_connectors
```

---

# 13. Slide 8 — DQNGuard gives the strongest usable operating point at low known rejection

## Dominant visual

Known-rejection vs Unknown-F1 operating-point plot.

## Geometry

Experiment strip:

- `x=96, y=225, w=1728, h=92`
- neutral panel
- text: `Fixed-surrogate comparison • Scan surrogate • targets: Burst / Sustain / Hop / Replay • mean ± SD across four held-out target folds`

Plot:

- `x=120, y=345, w=1120, h=560`

Right interpretation rail:

- `x=1300, y=345, w=524, h=560`

## Plot axes

x-axis:

**Known rejection → lower is better**

Suggested display domain: `0.00–0.18`.

Y-axis:

**Unknown F1 → higher is better**

Suggested display domain: `0.55–1.00`.

Lightly tint the upper-left region as desirable. Do not use a gradient.

## Points

DQNGuard:

- x = `0.050`
- y = `0.865`
- highlight blue

DQN-IDS-style head:

- x = `0.063`
- y = `0.701`
- neutral gray

VarMax surrogate-all:

- x = `0.128`
- y = `0.745`
- amber/neutral accent; do not use surrogate amber so strongly that it reads as a surrogate class

Direct-label all three points.

## Error bars

Include subtle error bars because the across-fold spread matters to the story:

- DQNGuard: x ± `0.004`, y ± `0.142`
- DQN-IDS-style: x ± `0.017`, y ± `0.197`
- VarMax surrogate-all: x ± `0.043`, y ± `0.146`

Use `2 px` neutral lines with small caps. Add a tiny annotation:

**Error bars = SD across held-out target folds, not rerun variance.**

## Right rail

Top card:

**AUROC / RANKING**

```text
VarMax           0.951
DQNGuard         0.891
DQN-IDS-style    0.829
```

Center callout:

**Ranking quality ≠ usable thresholded decision**

Bottom DQNGuard result:

**OSR macro F1: 0.881 ± 0.109**

Small interpretation:

**DQNGuard combines the highest mean Unknown F1 with the lowest mean known rejection in the main comparison.**

Do not write “wins every metric.”

## Object hierarchy

```text
slide08
├── title_group
├── guiding_question
├── experiment_strip
├── operating_plot
│   ├── axes
│   ├── desirable_region
│   ├── dqnguard_point
│   ├── dqn_ids_point
│   ├── varmax_point
│   └── error_bars
└── interpretation_rail
    ├── auroc_card
    ├── ranking_callout
    └── osr_f1_card
```

---

# 14. Slide 9 — Surrogate usefulness depends strongly on the unseen target

## Dominant visual

Accepted-paper Target–Surrogate Matrix.

## Geometry

Matrix asset frame:

- `x=250, y=235, w=1420, h=610`
- preserve aspect ratio
- center artwork
- do not crop axis labels or colorbar

Interpretation strip:

- `x=96, y=865, w=1728, h=120`
- three equal columns with `24 px` gaps

Column 1:

**TARGET VARIATION**

`Slide 8: 0.865 ± 0.142`

`Across target PAs — not repeated runs`

Column 2:

**BEST SURROGATE CHANGES**

`Scan → Hop`

`Burst → Replay`

`Sustain / Hop / Replay → Scan`

`No universal surrogate`

Column 3:

**SOME PAIRS NEARLY FAIL**

`Unknown F1 ≈ 0 in several cells`

`Mismatched calibration evidence may not transfer`

## Asset

Use:

`presentations/milcom2026/assets/figures/target_surrogate_unknown_f1_matrix.png`

Do not manually recreate or alter values.

## Scientific framing

Do not claim the Scan column in Figure 2 is numerically identical to the fixed-Scan comparison values on Slide 8. They are distinct reviewed result chains.

The takeaway is broader:

**surrogate choice materially changes performance, and target/surrogate roles are directional.**

## Object hierarchy

```text
slide09
├── title_group
├── supporting_sentence
├── target_surrogate_matrix_asset
└── interpretation_strip
    ├── target_variation
    ├── best_surrogate_changes
    └── pair_failure
```

---

# 15. Slide 10 — No simple target-blind rule reliably predicts the best surrogate

## Dominant visual

Three diagnostic columns converging on one conclusion bar.

## Geometry

Diagnostic cards:

- left: `x=96, y=275, w=560, h=560`
- middle: `x=680, y=275, w=560, h=560`
- right: `x=1264, y=275, w=560, h=560`

Shared conclusion:

- `x=300, y=875, w=1320, h=105`
- visually stronger than any one diagnostic card

## Left — calibration performance

Heading:

**SURROGATE CALIBRATION PERFORMANCE**

Question:

**“If I reject the surrogate well, will I reject the true unknown well?”**

Hero statistic:

**ρ ≈ −0.075**

Secondary:

`Pearson r ≈ −0.047`

`Best surrogate selected: 2 / 5 targets`

Interpretation:

**Rejecting the surrogate well does not imply transfer.**

## Middle — confidence geometry

Heading:

**CONFIDENCE GEOMETRY**

Small feature row:

`P1 • P1−P2 • entropy`

Hero statistic:

**ρ ≈ −0.552**

Interpretation:

**The intuitive confidence-space rule pointed in the wrong direction overall.**

## Right — feature geometry

Heading:

**FEATURE GEOMETRY**

Hero statistic:

**best simple +ρ ≈ +0.406**

Secondary:

`Best surrogate selected: 1 / 5 targets`

Interpretation:

**Some positive signal exists, but proximity alone is not reliable.**

## Shared conclusion

Large text:

**NO RELIABLE SINGLE-SURROGATE SELECTION RULE**

Small line:

**Good surrogate performance does not imply good target transfer.**

## Object hierarchy

```text
slide10
├── title_group
├── guiding_question
├── calibration_performance_card
├── confidence_geometry_card
├── feature_geometry_card
└── shared_conclusion
```

---

# 16. Slide 11 — VarMax can search across surrogates; DQNGuard must learn how to combine them

## Dominant visual

Top-half architecture contrast; bottom-half future-work options.

This slide is intentionally denser than the rest, but the reading order must be unambiguous.

## Title sizing

This is a long title. Use approximately `50–52 px` and a maximum of two lines.

Supporting sentence:

**In VarMax, surrogates change calibration parameters; in DQNGuard, the surrogate changes the learned open-set decision function itself.**

## Geometry

Top comparison region:

- `y=245–730`

Left VarMax region:

- `x=96, y=245, w=820, h=485`

Right DQNGuard mismatch region:

- `x=950, y=245, w=874, h=485`

Vertical divider at approximately `x=933`.

Bottom future-work region:

- `x=96, y=770, w=1728, h=215`

Three future-work cards:

- left: `x=96, w=552`
- middle: `x=684, w=552`
- right: `x=1272, w=552`
- each `y=805, h=175`

## Left — VarMax surrogate-all

Tag:

**ORIGINAL CONTRIBUTION — VARMAX SURROGATE-ALL**

Core visual:

```text
ONE FROZEN BACKBONE
        │
  ┌─────┼─────┐
  ▼     ▼     ▼
Scan  Burst   Hop ...
pseudo pseudo pseudo
open   open   open
  │     │     │
threshold / band candidates
        ↓
ALL CANDIDATES COMPETE
        ↓
SELECT ONE RULE
```

Key annotation:

**Surrogate-all is a calibration search, not a deployed ensemble.**

## Right — why it does not port directly

Use amber surrogate labels feeding distinct blue DQN nodes:

```text
Scan surrogate   → DQN A
Burst surrogate  → DQN B
Hop surrogate    → DQN C
                     ↓
          DIFFERENT LEARNED SCORE SPACES
```

Strong annotation:

**Thresholds are not directly interchangeable across separately fitted DQNs.**

Secondary note:

**Current DQNGuard also withholds its external surrogate from the backbone taxonomy.**

## Bottom — future architectures

Purple tag above the row:

**FUTURE WORK — NOT YET EVALUATED**

Card A:

**POOLED MULTI-SURROGATE DQN**

`A + B + C surrogate states → ONE DQN → one score space`

Card B:

**SURROGATE-SPECIFIC DQN ENSEMBLE**

`DQN A + DQN B + DQN C → normalize / aggregate`

Card C:

**HYBRID VARMAX / DQNGUARD**

`multi-surrogate deterministic guard evidence + one DQN signal`

Bottom goal line across all three cards:

**Goal: reduce dependence on a favorable single surrogate while preserving DQNGuard's strong thresholded operating point and explicit 5% known-rejection budget.**

## Color rules

- VarMax top-left: neutral ink with amber pseudo-open accents
- DQN nodes: blue
- future-work row: purple labels/borders
- never imply any future option has been validated

## Object hierarchy

```text
slide11
├── title_group
├── supporting_sentence
├── varmax_surrogate_all_group
├── dqnguard_mismatch_group
├── future_work_tag
└── future_architectures
    ├── pooled_dqn_card
    ├── dqn_ensemble_card
    └── hybrid_guard_card
```

## Progressive reveal

If animation is later added, reveal in this order:

1. VarMax surrogate-all
2. DQNGuard score-space mismatch
3. three future architectures

The static SVG must still contain the complete slide.

---

# 17. Slide 12 — DQNGuard improves the operating point—but surrogate transfer remains the next challenge

## Dominant visual

Three equal takeaway columns, deliberately calm and spacious.

## Title sizing

Use `50–54 px` if necessary to keep the title to at most two lines.

## Geometry

Takeaway cards:

- left: `x=96, y=250, w=560, h=610`
- middle: `x=680, y=250, w=560, h=610`
- right: `x=1264, y=250, w=560, h=610`

Scope footer:

- `x=96, y=895, w=1728, h=72`

Questions label:

- centered near `y=1015`

## Column 1 — usable OSR

Heading:

**1. USABLE OPEN-WORLD OPERATING POINT**

Hero metrics, stacked:

```text
0.865   UNKNOWN F1
0.881   OSR MACRO F1
0.050   KNOWN REJECTION
```

Use blue hero numerals with labels in primary ink.

Small label:

**Best thresholded operating point in the main comparison**

Interpretation:

**Preserve known PA evidence while exposing unfamiliar RF behavior.**

## Column 2 — surrogate dependence

Heading:

**2. SURROGATE TRANSFER IS TARGET-DEPENDENT**

Use a small thumbnail derived from the reviewed Target–Surrogate Matrix asset.

Hero line:

**20 ordered target–surrogate pairs**

Supporting lines:

- `Best surrogate changes with the target`
- `Several mismatched pairs approach F1 ≈ 0`
- `No simple target-blind selector was reliable`

Interpretation:

**Calibration transfer is directional and behavior dependent.**

## Column 3 — next research problem

Heading:

**3. MULTI-SURROGATE DQNGUARD**

Compact conceptual stack:

```text
VarMax surrogate-all philosophy
            +
DQNGuard budgeted decision layer
            ↓
MULTI-SURROGATE DQNGUARD?
```

Use purple for the future node.

Small tag:

**FUTURE WORK — ARCHITECTURAL REDESIGN REQUIRED**

Interpretation:

**Goal: retain DQNGuard's Unknown F1, OSR macro F1, and explicit known-rejection budget while reducing single-surrogate dependence.**

## Scope footer

Exact text:

**Preliminary Actions are RF precursor evidence. DQNGuard routes evidence; it does not make the final attack attribution or response decision.**

Questions:

**Questions?**

## Object hierarchy

```text
slide12
├── title_group
├── takeaway_1_group
│   ├── heading
│   ├── metric_unknown_f1
│   ├── metric_osr_f1
│   ├── metric_known_reject
│   └── interpretation
├── takeaway_2_group
│   ├── heading
│   ├── matrix_thumbnail
│   ├── pair_count
│   └── interpretation
├── takeaway_3_group
│   ├── heading
│   ├── varmax_node
│   ├── dqnguard_node
│   ├── merge_arrow
│   ├── future_node
│   └── interpretation
├── scope_footer
└── questions_label
```

---

# 18. Production sequence

Recommended build order:

1. Slide 1 — validates title treatment and global styling.
2. Slide 2 — validates two-panel card grammar.
3. Slide 5 — validates three-panel conceptual grammar.
4. Slide 6 — validates imported vector-figure treatment.
5. Slide 8 — validates chart and metric typography.
6. Slide 9 — validates imported scientific-result artwork.
7. Slides 7, 10, 11, 12.
8. Slides 3 and 4 after real OTA imagery is available, or build their fixed frames now and populate images later.

After each SVG is built:

- render to PNG at 1920×1080 for visual QA;
- verify no clipping/overflow;
- verify every text element is readable at presentation scale;
- compare against this specification and `PRESENTATION_PLAN.md`;
- do not change scientific values during visual cleanup.

---

# 19. Global forbidden substitutions

Do not silently:

- replace the camera-ready DQNGuard hero figure with an older revision;
- reconstruct the Target–Surrogate Matrix from memory;
- invent OTA scientific images;
- rename PA behaviors;
- expose PA1/PA2/etc. on the main audience-facing deck;
- call the comparison head `Shreyash`;
- call the hardware `Ettus N210`;
- interpret the main table standard deviations as rerun/seed variance;
- claim DQNGuard is best on AUROC;
- claim Figure 2's Scan column is the exact source of Slide 8's fixed-Scan means;
- claim multi-surrogate DQNGuard has already been implemented or validated;
- imply that DQNGuard performs final ATT&CK/EW attribution or response selection.

---

# 20. Static-slide acceptance checklist

Every SVG must pass all of these checks before assembly into PowerPoint:

- correct `1920×1080` viewBox;
- no important content outside the safe area;
- no text below 20 px unless it is optional provenance;
- title is conclusion-style and matches the locked plan;
- exactly one clear first-read visual;
- semantic colors are consistent with the deck-wide palette;
- imported scientific assets are from reviewed paths;
- all audience-facing terminology matches this file;
- arrows have unambiguous direction;
- no accidental implication of a scientific relationship created by decorative connectors;
- no clipped text, image, axis, colorbar, or arrowhead;
- no unsupported external font/CSS dependency;
- the static SVG is understandable without animation;
- scientific numbers exactly match the locked presentation plan / camera-ready result provenance.
