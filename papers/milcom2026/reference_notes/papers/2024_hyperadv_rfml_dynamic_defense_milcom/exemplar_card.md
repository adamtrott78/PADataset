# Exemplar Card: HyperAdv

## 1. Bibliographic Identity

Title: HyperAdv: Dynamic Defense Against Adversarial Radio Frequency Machine Learning Systems
Authors: Milin Zhang, Michael De Lucia, Ananthram Swami, Jonathan Ashdown, Kurt Turck, Francesco Restuccia
Venue: MILCOM
Year: 2024
PDF slug: 2024_hyperadv_rfml_dynamic_defense_milcom
Citation status: optional cite / section model

## 2. Library Classification

Primary decision: SECTION_MODEL
Secondary decisions: VENUE_STYLE_MODEL
Role tags: VENUE_STYLE_MODEL; METHOD_EXPOSITION_MODEL; RESULTS_NARRATIVE_MODEL; CLAIM_BOUNDARY_MODEL; FIGURE_MODEL
Paper action labels: contrast_static_vs_dynamic; analyze_tradeoff; evaluate_rfml_component

## 3. Why This Paper Is Included

This paper is included because it is a clean MILCOM RFML security paper with compact method exposition, a clear baseline-vs-proposed figure, and results organized around a tradeoff between benign and adversarial accuracy.

## 4. Relation to Our Paper

DQNGuard should similarly frame its value as an operating tradeoff: unknown detection improves while known rejection remains controlled. HyperAdv is especially useful for results narration and for keeping method claims bounded.

## 5. Scores

### Technical Relevance

| Criterion | Score | Notes |
|---|---:|---|
| RF / EMS / communications relevance | 3 | RFML setting |
| OSR / OOD / calibration relevance | 1 | Robustness, not OSR |
| ML method similarity | 2 | Decision behavior over neural outputs |
| Experimental setup similarity | 2 | RadioML and RFML evaluation |
| Operational / military / cyber relevance | 3 | Tactical RFMLS framing |
| Total | 11 |  |

### Format Relevance

| Criterion | Score | Notes |
|---|---:|---|
| IEEE two-column format | 3 | MILCOM |
| MILCOM / ComSoc / adjacent venue | 3 | Direct MILCOM |
| Six-to-eight-page length | 2 | Close target |
| Similar figure/table density | 2 | Strong compact visuals |
| Similar reviewer audience | 3 | RFML/security overlap |
| Total | 13 |  |

### Exemplar Quality

| Criterion | Score | Notes |
|---|---:|---|
| Abstract clarity | 3 | Very clear claim |
| Introduction flow | 3 | Good static-vs-dynamic contrast |
| Method explanation | 3 | Compact staged method |
| Experiment explanation | 2 | Clear RFML setup |
| Results narration | 3 | Strong tradeoff narrative |
| Figure/table design | 3 | Good first-page contrast figure |
| Discussion/limitations | 1 | Limited |
| Total | 18 |  |

## 6. Section Utility Matrix

| Our section or artifact | Utility | Notes |
|---|---|---|
| Abstract | medium | compact method/result statement |
| Introduction | high | failure of static defenses |
| Related Work | low | not core OSR lineage |
| Methodology | high | staged method explanation |
| Experimental Design | medium | RFML setup |
| Results | high | tradeoff table/figure narration |
| Discussion | medium | tactical RFMLS boundary |
| Figures | high | contrast figure model |
| Tables | high | compact result table |

## 7. Do Emulate

- Use a figure to contrast baseline and proposed behavior.
- Report both primary improvement and cost/tradeoff.
- Keep the method story simple: failure of static approach, proposed dynamic mechanism, result.
- Make the evaluation condition explicit.

## 8. Do Not Emulate

- Do not adopt adversarial ML notation unless needed.
- Do not claim DQNGuard is a defense against adversarial perturbations.
- Do not conflate robustness, OSR, and calibration.

## 9. Extracted Heuristics

- Table I should show DQNGuard improves unknown F1 and OSR macro F1 while keeping known rejection low.
- The results section should explicitly reject the trivial solution of rejecting too many known samples.
- DQNGuard is best described as a constrained decision layer.

## 10. Decision

Decision: SECTION_MODEL

Rationale: Strong MILCOM RFML method/results model, but Searchlight and Stitching are better direct structural exemplars.
