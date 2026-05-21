# Exemplar Card: Sensing-Throughput Tradeoffs with GANs for NextG Spectrum Sharing

## 1. Bibliographic Identity

Title: Sensing-Throughput Tradeoffs with Generative Adversarial Networks for NextG Spectrum Sharing
Authors: Yi Shi, Yalin E. Sagduyu
Venue: IEEE-style conference/workshop paper
Year: 2022
PDF slug: 2022_sensing_throughput_tradeoffs_gan_nextg_spectrum
Citation status: optional / section model

## 2. Library Classification

Primary decision: SECTION_MODEL
Secondary decisions: RESULTS_NARRATIVE_MODEL
Role tags: RESULTS_NARRATIVE_MODEL; TABLE_MODEL; CLAIM_BOUNDARY_MODEL; EXPERIMENT_DESIGN_MODEL
Paper action labels: analyze_operating_tradeoff; evaluate_system_component

## 3. Why This Paper Is Included

This paper is included because it frames results around an operational tradeoff: more sensing improves detection but reduces transmission time. That structure is directly useful for explaining DQNGuard as an operating-point method under a known-rejection budget.

## 4. Relation to Our Paper

DQNGuard also manages a tradeoff. Rejecting more samples can improve unknown detection, but excessive known rejection damages the utility of known PA evidence. The known-budget threshold should be narrated as an operating constraint, not just another hyperparameter.

## 5. Scores

### Technical Relevance

| Criterion | Score | Notes |
|---|---:|---|
| RF / EMS / communications relevance | 3 | Spectrum sharing |
| OSR / OOD / calibration relevance | 0 | Not OSR |
| ML method similarity | 1 | ML detector, but GAN objective differs |
| Experimental setup similarity | 2 | Sensing metrics and operating regimes |
| Operational / military / cyber relevance | 2 | Spectrum access decision setting |
| Total | 8 |  |

### Format Relevance

| Criterion | Score | Notes |
|---|---:|---|
| IEEE two-column format | 2 | IEEE-style |
| MILCOM / ComSoc / adjacent venue | 2 | Communications adjacent |
| Six-to-eight-page length | 2 | Compact |
| Similar figure/table density | 2 | Several compact tables |
| Similar reviewer audience | 2 | RF/comms ML audience |
| Total | 10 |  |

### Exemplar Quality

| Criterion | Score | Notes |
|---|---:|---|
| Abstract clarity | 2 | Clear tradeoff |
| Introduction flow | 2 | Good but not exceptional |
| Method explanation | 2 | Compact equations |
| Experiment explanation | 2 | Clear enough |
| Results narration | 3 | Strong operating tradeoff story |
| Figure/table design | 2 | Tables useful for comparison |
| Discussion/limitations | 1 | Limited |
| Total | 14 |  |

## 6. Section Utility Matrix

| Our section or artifact | Utility | Notes |
|---|---|---|
| Abstract | low | Not central |
| Introduction | medium | tradeoff motivation |
| Related Work | low | Not core citation |
| Methodology | medium | objective/constraint formulation |
| Experimental Design | medium | operating regimes |
| Results | high | tradeoff narration |
| Discussion | medium | constrained deployment framing |
| Figures | low | Not primary |
| Tables | high | compact tradeoff tables |

## 7. Do Emulate

- Present the operating constraint before the results.
- Explain why a metric improvement is only useful under the constraint.
- Compare baselines and proposed method at the same operating condition.

## 8. Do Not Emulate

- Do not import the GAN/spectrum-sharing mechanics.
- Do not let the math become the main story.
- Do not make our DQNGuard beta threshold sound like an arbitrary tuning knob.

## 9. Extracted Heuristics

- A result is more persuasive when tied to an operating regime.
- DQNGuard should be evaluated as fixed-budget OSR, not unconstrained novelty detection.
- Table I should be narrated as evidence that DQNGuard improves unknown detection without escaping the known-rejection constraint.

## 10. Decision

Decision: SECTION_MODEL

Rationale: Useful tradeoff/results model, but not a core style exemplar.
