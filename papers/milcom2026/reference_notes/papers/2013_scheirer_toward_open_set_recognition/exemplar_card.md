# Exemplar Card: Toward Open Set Recognition

## 1. Bibliographic Identity

Title: Toward Open Set Recognition
Authors: Walter J. Scheirer, Anderson de Rezende Rocha, Archana Sapkota, Terrance E. Boult
Venue: IEEE TPAMI
Year: 2013
Length: journal article
DOI / URL:
PDF slug: 2013_scheirer_toward_open_set_recognition
Citation status: should cite

## 2. Library Classification

Primary decision: TECHNICAL_REFERENCE
Secondary decisions: SECTION_MODEL
Role tags: TECHNICAL_LINEAGE; PROBLEM_FRAMING_MODEL; CLAIM_BOUNDARY_MODEL
Paper action labels: define_problem; introduce_method; diagnose_failure_mode

## 3. Why This Paper Is Included

This paper is included because it is the canonical formalization of open set recognition. It defines the distinction between closed-set classification and recognition with unknown classes at test time, introduces openness, and formalizes open space risk.

## 4. Relation to Our Paper

DQNGuard operates in the open-set condition described by Scheirer et al.: known classes are available during training, but unknown classes may appear during testing. Our paper should use Scheirer for formal OSR grounding, not as a style model.

## 5. Scores

### Technical Relevance

| Criterion | Score | Notes |
|---|---:|---|
| RF / EMS / communications relevance | 0 | Not RF |
| OSR / OOD / calibration relevance | 3 | Canonical OSR paper |
| ML method similarity | 2 | Rejection/open-space logic transfers |
| Experimental setup similarity | 2 | Hold-out unknown evaluation logic transfers |
| Operational / military / cyber relevance | 3 | Recognition under incomplete world knowledge transfers |
| Total | 10 |  |

### Format Relevance

| Criterion | Score | Notes |
|---|---:|---|
| IEEE two-column format | 1 | IEEE but journal length |
| MILCOM / ComSoc / adjacent venue | 0 | Not MILCOM |
| Six-to-eight-page length | 0 | Too long |
| Similar figure/table density | 1 | Some useful conceptual figures |
| Similar reviewer audience | 2 | ML/recognition overlap |
| Total | 4 |  |

### Exemplar Quality

| Criterion | Score | Notes |
|---|---:|---|
| Abstract clarity | 2 | Strong but long |
| Introduction flow | 3 | Excellent problem distinction |
| Method explanation | 2 | Formal but too long |
| Experiment explanation | 2 | Useful evaluation logic |
| Results narration | 1 | Not primary |
| Figure/table design | 2 | Useful conceptual diagrams |
| Discussion/limitations | 2 | Strong claim boundary |
| Total | 14 |  |

## 6. Section Utility Matrix

| Our section or artifact | Utility | Notes |
|---|---|---|
| Abstract | medium | Open-set definition language |
| Introduction | high | closed set vs open set framing |
| Related Work | high | canonical citation |
| Methodology | medium | open-set formalization |
| Experimental Design | medium | held-out unknown logic |
| Results | low | not our style |
| Discussion | medium | claim boundary |
| Conclusion | low | not primary |
| Figures | medium | openness conceptual figures |
| Tables | low | not primary |

## 7. Do Emulate

- Define open-set recognition as a structural condition, not just a hard classification problem.
- Emphasize that unknown classes appear at test time.
- Explain why a classifier must support rejection.
- Use open space risk as formal background.

## 8. Do Not Emulate

- Do not import journal-length formalism.
- Do not over-explain vision examples.
- Do not make our six-page paper look like a theory paper.

## 9. Useful Pages for Visual Analysis

Page 1: closed-set vs open-set motivation.
Page 2: openness and open space risk figures.
Key method pages: formal definition.
Key figure pages: openness and margin figures.
Key table pages: openness table.
Results pages: not primary.
Discussion/conclusion pages: claim boundaries.

## 10. Extracted Heuristics

- Open-set recognition requires the unknown option to be a valid output.
- Evaluation must include classes withheld from training.
- Rejecting unknowns is not the same as low-confidence closed-set classification.

## 11. Relevance to Our Current Revision

Use this paper to strengthen Related Work and Methodology definitions. It should anchor why DQNGuard is an OSR decision layer rather than merely a classifier confidence post-processor.

## 12. Decision

Decision: TECHNICAL_REFERENCE

Rationale: Essential OSR lineage and definition source, but not a MILCOM writing model.
