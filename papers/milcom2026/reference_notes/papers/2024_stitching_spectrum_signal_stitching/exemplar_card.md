# Exemplar Card: Stitching the Spectrum

## 1. Bibliographic Identity

Title: Stitching the Spectrum: Semantic Spectrum Segmentation with Wideband Signal Stitching
Authors: Daniel Uvaydov, Milin Zhang, Clifton Paul Robinson, Salvatore D'Oro, Tommaso Melodia, Francesco Restuccia
Venue: IEEE/ACM-style RF sensing paper
Year: 2024
PDF slug: 2024_stitching_spectrum_signal_stitching
Citation status: candidate cite / core exemplar

## 2. Library Classification

Primary decision: CORE_MODEL
Secondary decisions: SECTION_MODEL
Role tags: FIGURE_MODEL; METHOD_EXPOSITION_MODEL; EXPERIMENT_DESIGN_MODEL; RESULTS_NARRATIVE_MODEL; PROBLEM_FRAMING_MODEL
Paper action labels: motivate_real_ota_data; introduce_pipeline; evaluate_generalization

## 3. Why This Paper Is Included

This is the strongest visual and methodology exemplar in the style batch. It uses early figures to make the RF problem concrete, explains why real OTA data is hard to label, and presents a pipeline that addresses a practical data/representation bottleneck.

## 4. Relation to Our Paper

Our paper also depends on making OTA RF windows and preliminary-action evidence concrete. The hero figure should structure the methodology the same way Stitching uses figures to connect RF reality, representation, dataset construction, model behavior, and evaluation.

## 5. Scores

### Technical Relevance

| Criterion | Score | Notes |
|---|---:|---|
| RF / EMS / communications relevance | 3 | Direct wideband RF sensing |
| OSR / OOD / calibration relevance | 1 | Generalization/unknown RF conditions |
| ML method similarity | 2 | Deep RF representation/pipeline |
| Experimental setup similarity | 3 | OTA data and multiple protocols |
| Operational / military / cyber relevance | 2 | Spectrum sensing supports operational use |
| Total | 11 |  |

### Format Relevance

| Criterion | Score | Notes |
|---|---:|---|
| IEEE two-column format | 3 | IEEE-style |
| MILCOM / ComSoc / adjacent venue | 2 | RF/comms adjacent |
| Six-to-eight-page length | 1 | Longer than target |
| Similar figure/table density | 3 | Excellent figures |
| Similar reviewer audience | 2 | RFML/spectrum reviewers |
| Total | 11 |  |

### Exemplar Quality

| Criterion | Score | Notes |
|---|---:|---|
| Abstract clarity | 3 | Strong problem-method-result density |
| Introduction flow | 3 | Excellent figure-supported motivation |
| Method explanation | 3 | Clear pipeline staging |
| Experiment explanation | 3 | Strong OTA setup |
| Results narration | 3 | Generalization and latency claims |
| Figure/table design | 3 | Best visual model |
| Discussion/limitations | 2 | Useful boundaries |
| Total | 20 |  |

## 6. Section Utility Matrix

| Our section or artifact | Utility | Notes |
|---|---|---|
| Abstract | high | dense RF sensing summary |
| Introduction | high | figure-supported RF problem framing |
| Related Work | medium | OTA RF dataset realism |
| Methodology | high | pipeline staging |
| Experimental Design | high | OTA data and generalization |
| Results | high | result claims tied to RF realism |
| Discussion | medium | real-time/deployment framing |
| Figures | high | best figure model |
| Tables | medium | not primary |

## 7. Do Emulate

- Use early visuals to make the RF problem real.
- Explain why easy synthetic/closed-world assumptions fail.
- Present the pipeline as the answer to a specific practical bottleneck.
- Separate dataset/representation, model, and evaluation claims cleanly.

## 8. Do Not Emulate

- Do not let our paper become mainly a dataset-generation paper.
- Do not overload page 1 with too many visual claims.
- Do not claim general RF spectrum segmentation; our output is PA evidence and unknown routing.

## 9. Extracted Heuristics

- Figure 1 should carry the structure of the methodology.
- Methodology should follow the hero figure sequence: RF input, multi-domain PA encoder, DQNGuard decision layer, OSR outputs.
- The paper should repeatedly connect OTA realism to why open-set routing matters.
- Claims should be tied to what the evaluated pipeline actually emits.

## 10. Decision

Decision: CORE_MODEL

Rationale: Best visual/methodology exemplar and one of the strongest models for RF dataset and representation framing.
