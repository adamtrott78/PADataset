# Reference Library Framework for MILCOM 2026 Paper

This document defines how exemplar and reference papers are selected, processed, scored, and used during revision of the MILCOM 2026 DQNGuard paper.

The goal is not to collect papers randomly. The goal is to build a reusable paper-composition library that helps revise the paper toward a stronger IEEE/MILCOM submission.

---

## 1. Purpose of the Library

The library should answer one question:

What does this paper teach us about how to make our paper more convincing to MILCOM/IEEE reviewers?

Every ingested paper should be treated as a structured object with four layers:

1. Identity: what the paper is.
2. Reason for inclusion: why we care.
3. Role utility: what part of our paper it can help with.
4. Transferable heuristics: what we learn from it.

This distinction matters because citation relevance and writing-exemplar value are separate properties. A paper may be necessary to cite but poor as a writing model. Another paper may be only loosely technical but excellent as a model for page economy, figure placement, or results narration.

---

## 2. Our Paper Genre

The DQNGuard paper should be treated as:

A six-page IEEE/MILCOM applied RF/EMS machine-learning paper introducing a budgeted open-set recognition decision layer for OTA RF preliminary-action detection, with controlled experimental validation and cyber-EMS system motivation.

The paper is not primarily:

* a long ML theory paper
* a survey
* a full systems paper
* a dataset release
* a pure RF hardware paper
* a pure cyber doctrine paper
* a full QR-CWoS architecture paper

It is an applied method paper that must persuade reviewers that a specific RF open-set sensing layer is useful, evaluated fairly, and scoped honestly.

---

## 3. Core Communication Burdens

The paper must satisfy four communication burdens.

| Burden                 | What reviewers need to believe                       | Exemplar type needed                                          |
| ---------------------- | ---------------------------------------------------- | ------------------------------------------------------------- |
| Operational motivation | This matters for cyber-EMS / military sensing        | MILCOM, cyber-EMS, defense communications papers              |
| Technical validity     | The OSR/calibration framing is rigorous              | OSR, OOD, calibration, uncertainty papers                     |
| RF legitimacy          | The signal representation and OTA setup are credible | RF ML, spectrum sensing, modulation, emitter-behavior papers  |
| Result credibility     | The experiments support the claims                   | papers with strong results narrative, tables, and limitations |

A paper is useful if it helps with at least one of these burdens.

---

## 4. Library Layers

The paper library has two overlapping layers.

| Layer            | Purpose                                              | Must it be cited? |  Can it guide writing? |
| ---------------- | ---------------------------------------------------- | ----------------: | ---------------------: |
| Reference corpus | Supports factual, methodological, or lineage claims  |       Usually yes | Only if it scores well |
| Exemplar corpus  | Teaches how to write, structure, visualize, or argue |   Not necessarily |                    Yes |
| Overlap set      | Technically relevant and well communicated           |               Yes |                    Yes |

Every paper should therefore receive two explanations:

1. Why are we citing or including this paper?
2. What, if anything, should we emulate from it?

---

## 5. Role Tags

Each paper can receive multiple role tags.

| Role tag                | Meaning                                                                               |
| ----------------------- | ------------------------------------------------------------------------------------- |
| VENUE_STYLE_MODEL       | Teaches MILCOM/IEEE short-paper pacing, density, captions, and contribution style     |
| TECHNICAL_LINEAGE       | Must be cited for method ancestry, terminology, or baseline justification             |
| PROBLEM_FRAMING_MODEL   | Teaches how to open the problem, state stakes, and define the failure mode            |
| METHOD_EXPOSITION_MODEL | Teaches how to explain a method, notation, stages, or pipeline                        |
| EXPERIMENT_DESIGN_MODEL | Teaches dataset, hardware, split, calibration, or metric description                  |
| RESULTS_NARRATIVE_MODEL | Teaches how to interpret results rather than merely report them                       |
| FIGURE_MODEL            | Teaches figure design, visual hierarchy, or page-level figure placement               |
| TABLE_MODEL             | Teaches compact and persuasive table design                                           |
| DISCUSSION_MODEL        | Teaches implications, limitations, and future work framing                            |
| CLAIM_BOUNDARY_MODEL    | Teaches how to state what the paper does not solve without weakening it               |
| LAB_CONTINUITY          | Preserves terminology, advisor expectations, lab framing, or prior-project continuity |
| NEGATIVE_MODEL          | Relevant but flawed; useful mainly for what not to do                                 |
| REFERENCE_ONLY          | Needed for citation lineage but not useful as a writing/design model                  |

---

## 6. Final Admission Decisions

Each paper should receive one final decision.

| Decision            | Meaning                                                             |
| ------------------- | ------------------------------------------------------------------- |
| CORE_MODEL          | Use repeatedly across multiple sections                             |
| SECTION_MODEL       | Use for one specific section or artifact                            |
| TECHNICAL_REFERENCE | Cite and use for terminology or lineage, but do not emulate broadly |
| STYLE_REFERENCE     | Use for prose/layout, maybe not cited                               |
| NEGATIVE_REFERENCE  | Relevant mainly as a warning                                        |
| REJECT_FROM_LIBRARY | Not useful enough to process deeply                                 |

The decision should be role-specific. A paper with mediocre overall score can still be essential if it teaches one narrow thing very well.

---

## 7. Three-Score System

Each paper receives three independent scores.

### 7.1 Technical Relevance

| Criterion                                | Score |
| ---------------------------------------- | ----: |
| RF / EMS / communications relevance      |   0-3 |
| OSR / OOD / calibration relevance        |   0-3 |
| ML method similarity                     |   0-3 |
| Experimental setup similarity            |   0-3 |
| Operational / military / cyber relevance |   0-3 |

Maximum: 15.

### 7.2 Format Relevance

| Criterion                        | Score |
| -------------------------------- | ----: |
| IEEE two-column format           |   0-3 |
| MILCOM / ComSoc / adjacent venue |   0-3 |
| Six-to-eight-page length         |   0-3 |
| Similar figure/table density     |   0-3 |
| Similar reviewer audience        |   0-3 |

Maximum: 15.

### 7.3 Exemplar Quality

| Criterion              | Score |
| ---------------------- | ----: |
| Abstract clarity       |   0-3 |
| Introduction flow      |   0-3 |
| Method explanation     |   0-3 |
| Experiment explanation |   0-3 |
| Results narration      |   0-3 |
| Figure/table design    |   0-3 |
| Discussion/limitations |   0-3 |

Maximum: 21.

---

## 8. Paper Action Labels

Each paper should be labeled by the action it performs.

Possible paper actions:

| Action                    | Meaning                                    |
| ------------------------- | ------------------------------------------ |
| introduce_method          | proposes a new method                      |
| evaluate_system_component | evaluates one component in a larger system |
| benchmark_methods         | compares existing methods                  |
| release_dataset           | introduces a data resource                 |
| define_problem            | formalizes a task                          |
| diagnose_failure_mode     | studies why something fails                |
| survey_field              | synthesizes literature                     |
| position_architecture     | proposes a system architecture             |

Our paper's action is:

introduce_method + evaluate_system_component + diagnose_calibration_failure_mode

This is important because the paper does not merely introduce DQNGuard. It also shows that surrogate-open calibration is target-dependent. Strong exemplars should ideally teach both method introduction and diagnostic result framing.

---

## 9. What to Prioritize During Search

Search should be gap-driven. We should not search randomly.

| If the library lacks... | Search for...                                                                  |
| ----------------------- | ------------------------------------------------------------------------------ |
| VENUE_STYLE_MODEL       | recent MILCOM or IEEE ComSoc short papers with strong first pages              |
| PROBLEM_FRAMING_MODEL   | papers that clearly explain deployment risk and technical gap                  |
| METHOD_EXPOSITION_MODEL | papers that explain staged methods cleanly under space constraints             |
| EXPERIMENT_DESIGN_MODEL | RF/communications papers with compact dataset and hardware descriptions        |
| RESULTS_NARRATIVE_MODEL | papers with strong ablations, matrix plots, and concise interpretation         |
| FIGURE_MODEL            | papers with excellent pipeline or system diagrams                              |
| TABLE_MODEL             | IEEE papers with dense but readable comparison tables                          |
| CLAIM_BOUNDARY_MODEL    | papers with strong limitations sections that do not undermine the contribution |

---

## 10. Existing Reference Audit Comes First

Before searching for new papers, audit the existing reference set.

Initial audit set:

1. Baye et al., varMax MILCOM.
2. Broggi et al., varMax uncertainty and novelty paper.
3. Tiwari et al., DQN-IDS.
4. Energy-Based Open-World Uncertainty Modeling for Confidence Calibration.
5. Wei et al., Exploiting Multi-Domain Features for Detection of Unclassified Electromagnetic Signals.
6. Trott et al., prior RF modulation VarMax paper.
7. Bendale and Boult, Towards Open Set Deep Networks, if used.
8. Scheirer et al., Toward Open Set Recognition, if used.

The purpose is to classify what these papers are useful for before adding more.

Expected preliminary roles:

| Paper                         | Expected role before inspection                                                 |
| ----------------------------- | ------------------------------------------------------------------------------- |
| Baye varMax MILCOM            | TECHNICAL_LINEAGE, possible VENUE_STYLE_MODEL, possible RESULTS_NARRATIVE_MODEL |
| Broggi varMax uncertainty     | TECHNICAL_LINEAGE, possible METHOD_EXPOSITION_MODEL                             |
| DQN-IDS                       | TECHNICAL_LINEAGE, possible RELATED_WORK_MODEL                                  |
| Energy-based open-world paper | TECHNICAL_LINEAGE, possible METHOD_EXPOSITION_MODEL                             |
| Wei multi-domain RF           | METHOD_EXPOSITION_MODEL, FIGURE_MODEL, possible EXPERIMENT_DESIGN_MODEL         |
| Prior Trott RF VarMax         | LAB_CONTINUITY, TECHNICAL_LINEAGE, possible PROBLEM_FRAMING_MODEL               |
| OpenMax                       | TECHNICAL_LINEAGE, OSR definition model                                         |
| Toward Open Set Recognition   | TECHNICAL_LINEAGE, likely REFERENCE_ONLY for prose                              |

These labels should be revised after page-level inspection.

---

## 11. Reference Paper Processing Pipeline

Drop PDFs into:

papers/milcom2026/reference_notes/staging/

Run from repo root:

MATHPIX_CMD='mpx convert "{pdf}" "{out}"' bash papers/milcom2026/tools/process_reference_papers.sh

Each processed paper folder should contain:

* renamed PDF
* Mathpix Markdown .mmd file
* images/contact_sheet.png
* images/pages/<slug>-001.png, <slug>-002.png, etc.
* manifest.json
* process.log
* eventually exemplar_card.md

Downloadable bundles are written to:

papers/milcom2026/reference_notes/reference_paper_exports/

---

## 12. Master Registry

After several papers are processed, create and maintain:

papers/milcom2026/reference_notes/reference_registry.md

The registry should summarize all processed papers.

Suggested columns:

| Slug | Cited? | Decision | Primary roles | Best use | Technical score | Format score | Quality score |
| ---- | ------ | -------- | ------------- | -------- | --------------: | -----------: | ------------: |

The registry is the command center. It prevents the library from becoming an unstructured pile of PDFs.

---

## 13. Operating Principle

Never copy a paper globally.

Always ask:

Use this paper for what?
Do not use it for what?
Which part of our paper does it help revise?
What mistake does it teach us to avoid?

This is the difference between a citation folder and a reusable paper-composition system.
