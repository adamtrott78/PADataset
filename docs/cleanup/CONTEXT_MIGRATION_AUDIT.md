# Context migration audit

This is a finite migration record, not a context entry point or run-status handoff.
It covers every one of the 74 Markdown/text candidates in the original tracked
census at `077c8d9466e1a4e70bb8163560e4b52e108cef92`. The preservation branch
`context-pre-modularization` still points there. Decisions were checked against
the context hierarchy at `a08bd19ff3d6040c0767abb614e14f069cedd073` and the
maintenance context added with this audit. No legacy deletion is executed by
this checkpoint. Paths below identify original files, including future removals.

## Batch 3 completion record

The removal pass is based on commit
`6a2f157f1ca1be51448207b7b01f4d86d6b45f95`. All 18 entries originally classified
RETIRE or MIGRATE-RETIRE in the ledger below are now removed from the working
branch. No files were moved. Their preservation destinations were completed in
Batch 2; the original files remain recoverable from the preservation branch.
The original ledger is retained as an audit trail, not a pending work list.

Gate E: checked all surviving first-party Markdown links to retired paths and
162 local links across README plus the 12 scoped contexts against the prospective
post-removal tree. No active link repair was necessary. Searched 409 inspected
text sources for removed-path references. Remaining references are this audit,
the explicitly historical concatenated DQN review bundle, and the historical
spring-clean script's placeholder-writing code. The maintenance context explains
why that script must not be replayed; its code is unchanged.

Validation is static documentation/interface verification, not execution of
hardware, training, OSR, OCR or final-paper reproduction. Independent Phase 9
cold-start validation remains required. The final 8192-result lineage is still
unresolved and was not changed by cleanup. See FINAL_REPORT.md for the complete
implementation record and PHASE9_VALIDATION.md for the operator prompt package.

## Disposition meanings

- **REPLACE:** rewrite the entry point after its destinations are complete.
- **RETIRE:** useful operational content has a named owner; remove after final
  coverage and incoming-link checks, not merely because the filename looks old.
- **MIGRATE-RETIRE:** a specific content-preservation gate remains before removal.
- **RETAIN-HISTORY/EVIDENCE/SOURCE:** preserve research provenance or source
  material; do not promote its historical commands/statuses to current policy.
- **RETAIN-OPTIONAL:** useful aid, explicitly nonmandatory.
- **RETAIN:** useful component boundary.

## Batch 2 integration record

Baseline for this integration: `26cd3ae39f4d8597653fcd3f003b2ce78c0151fd`.
Content-preservation gates A–D are complete for documentation integration:

| Gate | Concrete result |
|---|---|
| A | README replaced with scientific model, environment/artifact boundaries and direct task routes. Section coverage ledger follows. |
| B | HANDIN_MANIFEST, PAPER_GROUND_TRUTH and PAPER_EVIDENCE_MAP have explicit historical/provenance boundaries. Clean source-export recipe migrated to paper tools; final run lineage remains unresolved rather than relabeled. |
| C | Existing legacy_digital_reconstruction now retains the complete family correspondence table without rerun mandates, the original confidence-labeled parameter table and scoped historical findings. Retained incident/recovery/iteration records explicitly mark old instructions historical. |
| D | Retained hero heuristics preserve source-specific Baye/Wei/Broggi/Tiwari/Trott observations and winning-config evidence labels; registry preserves the incomplete downstream source lead; exemplar template is optional. |

All six MIGRATE-RETIRE entries in the original ledger now have their preservation
destination populated. Ledger dispositions below are the original audit decisions,
not deletion records. Gate E's final removal/dependency check and Phase 9 independent
cold-start validation remain for the subsequent batch. No legacy files were deleted.

Validation: new shell/Python blocks parsed; new relative links resolved; the
Overleaf export recipe passed an isolated fixture check; paper methodology
stages A–I and writing doctrine remain byte-identical to the previous context.
No actual paper compilation, model evaluation, OCR request or hardware run was
performed. Independent cold-start behavior is not established by these checks.

### Original README section coverage

| Original section(s) | Owner / treatment |
|---|---|
| 0–2 branch, orientation, bootstrap | README; maintenance context. Replace broad mandatory handoff reading with task-scoped routes. |
| 3 environment | README overview; exact setup remains with generation, experiment and paper contexts. |
| 4–5 repository map, PA taxonomy | README router and PA table; experiment/preprocess contexts own universes and labels. |
| 6 generation | protocol/CONTEXT.md |
| 7–8 capture and resplice | txrx/CONTEXT.md |
| 9–10 bank and cache | scripts/preprocess/CONTEXT.md |
| 11–12 training and reduction | experiments/CONTEXT.md; BACKBONE.md; RESULTS.md |
| 13 OSR and diagnostics | Method contexts and RESULTS.md; diagnostic source owners retained. |
| 14 new run groups | experiments/CONTEXT.md; historical mandatory reruns replaced with question-driven design. |
| 15 result persistence | RESULTS.md research-record guidance and maintenance context. |
| 16 legacy recovery | Existing legacy_digital_reconstruction with preserved confidence labels; maintenance context. |
| 17 paper | papers/CONTEXT.md preserves section 17.6 methodology; papers/milcom2026/CONTEXT.md owns files, build, three-view OCR review and export. |
| 18 new paper | papers/CONTEXT.md separate project workflow |
| 19–20 Git/artifact hygiene | docs/cleanup/CONTEXT.md; root history boundary |
| 21 recovery | Owner contexts; GPU-lock and diagnostic gaps filled in experiment/results contexts. |
| 22 reproducibility | RESULTS.md provenance requirements plus upstream validation in generation/capture/preprocess contexts. |
| 23 repeated cookbook | Remove duplicates; use source-checked owner commands. |

## Original gates and their rationale

**A — README coverage and routing.** Check every existing README section against
the owning context before replacing it. Preserve scientific scope (PA precursor
behavior, known/unknown separation, downstream QR-CWoS boundary), environment
prerequisites and task discovery at root. Commands remain with their owners.
Methodology in README section 17.6 has already migrated to papers/CONTEXT.md;
do not reconstruct it from the old comparative framework. Remove migration-stage
wording from active contexts when integration is complete.

**B — Paper snapshot boundaries.** Check HANDIN_MANIFEST, ground-truth and evidence
records for stale status, lengths, filenames and export instructions. Preserve
submission evidence with explicit snapshot scope. Author-confirmed paper pooling
is 8192; recovered supplied CSVs link to exploratory 16384 run artifacts. The
final 8192 result lineage still needs tracing, not another broad data collection
or silent relabeling. The comparator adapts the peer's CICIDS/UNSW DQN-IDS model
to RF; current implementation details are in DQN_IDS.md. These provenance issues
do not block routing/cleanup, but do block declaring final historical reproduction
verified. Local-only analysis scripts and later figure sources are documented
dependencies, not automatically present on GitHub.

**C — Historical experiment knowledge.** Current commands, split/calibration
semantics, family overrides and partial-run behavior are covered by experiment
contexts. Before retiring final_rerun_plan and prior-chat knowledge, extract any
unique legacy family correspondence and evidence-backed findings into the
existing historical reconstruction record with their confidence labels. Do not
copy old recommendations as final settings. Retained incident/inventory/recovery
reports need an explicit historical boundary where their future-task wording
could mislead. Keep diagnostic tensor-versus-spectrogram interpretation.

**D — Exemplar and figure observations.** Retain individual cards, source text,
hero analysis rounds and heuristics. Before deleting framework/winning/nested
upload docs, compare their unique source-specific observations with the retained
heuristics and add only missing durable lessons. Label the long exemplar template
optional. Preserve iteration notes as historical evidence, without active
next-step instructions. The actual figure owner and build process are already
in papers/milcom2026/CONTEXT.md; a winning-config note is not authoritative.

**E — Dependency check.** After A–D, scan links and literal path references to each
removal candidate, including generator scripts. The historical spring-clean
script recreates obsolete READMEs: maintenance context explicitly excludes it
from routine use. Do not run or silently modernize that migration script during
documentation cleanup. Repair active incoming links; historical quoted paths
may remain identifiable as historical. Validate the final README cold-start
routes before declaring Phases 7–8 complete.

## Context ownership

| Owner | Migrated responsibility |
|---|---|
| protocol/CONTEXT.md | PA generation, configuration and deterministic plans |
| txrx/CONTEXT.md | Tape/spec pairing, capture, resplice and recovery |
| scripts/preprocess/CONTEXT.md | Banking, PA labels, transforms, pooling and cache validation |
| experiments/CONTEXT.md | Configurations, catalogs, manifests, launchers and run lifecycle |
| experiments/context/BACKBONE.md | Architecture, losses, features and checkpoints |
| experiments/context/DQNGUARD.md | Class calibration, guard evidence, budgeted threshold and evaluation |
| experiments/context/VARMAX.md | VarMax acceptance, sweep and calibration behavior |
| experiments/context/DQN_IDS.md | DQN head and adapted peer-model comparator distinctions |
| experiments/context/RESULTS.md | Result provenance, reduction, table and Target–Surrogate Matrix inputs |
| papers/CONTEXT.md | Successful evidence-grounded, exemplar-guided writing methodology |
| papers/milcom2026/CONTEXT.md | Manuscript editing, figures, build and three-view API-backed ingestion |
| docs/cleanup/CONTEXT.md | Checkout inspection, source preservation and maintenance boundaries |

## Complete baseline disposition ledger

Counts: MIGRATE-RETIRE 6; REPLACE 1; RETAIN 1; RETAIN-EVIDENCE 24; RETAIN-HISTORY 24; RETAIN-OPTIONAL 1; RETAIN-SOURCE 5; RETIRE 12.

| Original path | Planned disposition | Destination / preservation condition |
|---|---|---|
| `AI_HANDOFF_README.md` | RETIRE | papers/CONTEXT.md and papers/milcom2026/CONTEXT.md own methodology, build, assets and claim boundaries. Drop branch/chat-status instructions; verify export/hand-in details under Gate B. |
| `README.md` | REPLACE | Scoped contexts listed below; retain only project model, prerequisites overview and task router. Gate A. |
| `docs/cleanup/spring_clean.md` | RETAIN-HISTORY | Historical layout migration; docs/cleanup/CONTEXT.md owns current maintenance. |
| `docs/experiments/dqn_review/dqn_archive_concat_for_review.md` | RETAIN-HISTORY | Run/incident/reconstruction or notebook-recovery evidence. Current operations belong to experiments contexts; old next-task instructions are not active. Gate C. |
| `docs/experiments/final_rerun_plan.md` | MIGRATE-RETIRE | experiments/CONTEXT.md and method contexts own current launch/configuration behavior. Gate C: preserve unique legacy-to-modern family mapping as historical evidence, discard mandatory future rerun language. |
| `docs/experiments/legacy_digital_reconstruction.md` | RETAIN-HISTORY | Run/incident/reconstruction or notebook-recovery evidence. Current operations belong to experiments contexts; old next-task instructions are not active. Gate C. |
| `docs/experiments/legacy_inventory_summary.md` | RETAIN-HISTORY | Run/incident/reconstruction or notebook-recovery evidence. Current operations belong to experiments contexts; old next-task instructions are not active. Gate C. |
| `docs/experiments/legacy_notebook_inventory.md` | RETAIN-HISTORY | Run/incident/reconstruction or notebook-recovery evidence. Current operations belong to experiments contexts; old next-task instructions are not active. Gate C. |
| `docs/experiments/legacy_prior_chat_experiment_knowledge.md` | MIGRATE-RETIRE | Current configuration semantics belong to experiments contexts. Gate C: retain only evidence-backed historical findings with confidence labels in an existing reconstruction record before retiring chat instructions. |
| `docs/experiments/run_diagnostics/highconf_pa2_as_pa8_stale/README.md` | RETAIN-HISTORY | Run/incident/reconstruction or notebook-recovery evidence. Current operations belong to experiments contexts; old next-task instructions are not active. Gate C. |
| `docs/experiments/run_incidents/catalog_tiny_smoke_20260513_115657.md` | RETAIN-HISTORY | Run/incident/reconstruction or notebook-recovery evidence. Current operations belong to experiments contexts; old next-task instructions are not active. Gate C. |
| `docs/experiments/run_incidents/primary_tiny_real_family_error_20260513_134057.md` | RETAIN-HISTORY | Run/incident/reconstruction or notebook-recovery evidence. Current operations belong to experiments contexts; old next-task instructions are not active. Gate C. |
| `docs/experiments/run_incidents/primary_tiny_real_family_error_20260513_134719.md` | RETAIN-HISTORY | Run/incident/reconstruction or notebook-recovery evidence. Current operations belong to experiments contexts; old next-task instructions are not active. Gate C. |
| `docs/experiments/run_incidents/primary_tiny_real_family_error_20260513_134935.md` | RETAIN-HISTORY | Run/incident/reconstruction or notebook-recovery evidence. Current operations belong to experiments contexts; old next-task instructions are not active. Gate C. |
| `docs/experiments/run_results/catalog_tiny_smoke_validation.md` | RETAIN-HISTORY | Run/incident/reconstruction or notebook-recovery evidence. Current operations belong to experiments contexts; old next-task instructions are not active. Gate C. |
| `docs/experiments/shreyash_dqn_backbone_recovery.md` | RETAIN-HISTORY | Run/incident/reconstruction or notebook-recovery evidence. Current operations belong to experiments contexts; old next-task instructions are not active. Gate C. |
| `experiments/README.md` | RETIRE | experiments/CONTEXT.md replaces obsolete future-system placeholder. |
| `legacy/README.md` | RETAIN | Archive boundary, not an executable workflow. Link current context if needed. |
| `legacy/preprocessing/buh_pipeline/buh.txt` | RETAIN-HISTORY | Archived buh pipeline commands stay with archived code; current preprocessing context is authoritative. |
| `manifests/bluetooth/bluetooth_pa1_run01/stage_manifest.txt` | RETAIN-EVIDENCE | Dataset staging provenance; not a current command recipe. |
| `manifests/wifi/wifi_pa1_run01/stage_manifest.txt` | RETAIN-EVIDENCE | Dataset staging provenance; not a current command recipe. |
| `manifests/zigbee/zigbee_pa1_run01/stage_manifest.txt` | RETAIN-EVIDENCE | Dataset staging provenance; not a current command recipe. |
| `papers/milcom2026/HANDIN_MANIFEST.md` | RETAIN-HISTORY | Submission snapshot and provenance; paper context owns current build. Gate B: make dated/snapshot authority explicit. |
| `papers/milcom2026/PAPER_EVIDENCE_MAP.md` | RETAIN-EVIDENCE | Claim/source navigation; Gate B: separate historical recommendations from verified final evidence. |
| `papers/milcom2026/PAPER_GROUND_TRUTH.md` | RETAIN-EVIDENCE | Claim record used by papers/CONTEXT.md; Gate B: label historical constants and unresolved provenance rather than overwriting evidence. |
| `papers/milcom2026/README_SETUP.md` | RETIRE | papers/milcom2026/CONTEXT.md owns Makefile, preview and source editing; maintenance context owns targeted source preservation. |
| `papers/milcom2026/TODO_REPORT.md` | RETIRE | Stale line-number/TODO snapshot; paper context documents mechanical checks on the current manuscript. Do not carry old tasks forward. |
| `papers/milcom2026/composition/ASPECT_REGISTRY.md` | RETIRE | Paper context asset-owner map replaces stale aspect statuses; papers/CONTEXT.md replaces governing composition process. |
| `papers/milcom2026/composition/aspects/hero_figure/CURRENT_WINNING_CONFIG.md` | MIGRATE-RETIRE | Paper context owns current main.tex figure selection and durable figure lessons. Gate D: compare remaining scientific labels and visual requirements before retiring stale winning/next-step claims. |
| `papers/milcom2026/composition/aspects/hero_figure/ca_rounds/002_tiwari_vs_trott_model_diagrams.md` | RETAIN-HISTORY | Figure iteration/heuristic evidence; main.tex determines active asset. Gate D: mark old candidate next steps historical, preserve unique lessons. |
| `papers/milcom2026/composition/aspects/hero_figure/ca_rounds/003_gemini_g1_vs_scripted_s1_hero_figure.md` | RETAIN-HISTORY | Figure iteration/heuristic evidence; main.tex determines active asset. Gate D: mark old candidate next steps historical, preserve unique lessons. |
| `papers/milcom2026/composition/aspects/hero_figure/heuristics/hero_figure_heuristics_v002.md` | RETAIN-HISTORY | Figure iteration/heuristic evidence; main.tex determines active asset. Gate D: mark old candidate next steps historical, preserve unique lessons. |
| `papers/milcom2026/composition/aspects/hero_figure/implementation/hero_figure_visual_spec_v001.md` | RETAIN-HISTORY | Figure iteration/heuristic evidence; main.tex determines active asset. Gate D: mark old candidate next steps historical, preserve unique lessons. |
| `papers/milcom2026/composition/aspects/hero_figure/implementation/scripted_s1_candidate_notes.md` | RETAIN-HISTORY | Figure iteration/heuristic evidence; main.tex determines active asset. Gate D: mark old candidate next steps historical, preserve unique lessons. |
| `papers/milcom2026/composition/aspects/hero_figure/implementation/scripted_s2_candidate_notes.md` | RETAIN-HISTORY | Figure iteration/heuristic evidence; main.tex determines active asset. Gate D: mark old candidate next steps historical, preserve unique lessons. |
| `papers/milcom2026/composition/aspects/hero_figure/implementation/scripted_s3_candidate_notes.md` | RETAIN-HISTORY | Figure iteration/heuristic evidence; main.tex determines active asset. Gate D: mark old candidate next steps historical, preserve unique lessons. |
| `papers/milcom2026/composition/aspects/hero_figure/implementation/scripted_s4_candidate_notes.md` | RETAIN-HISTORY | Figure iteration/heuristic evidence; main.tex determines active asset. Gate D: mark old candidate next steps historical, preserve unique lessons. |
| `papers/milcom2026/composition/aspects/hero_figure/implementation/scripted_s5_candidate_notes.md` | RETAIN-HISTORY | Figure iteration/heuristic evidence; main.tex determines active asset. Gate D: mark old candidate next steps historical, preserve unique lessons. |
| `papers/milcom2026/composition/comparative_revision_plan.md` | RETIRE | papers/CONTEXT.md preserves evidence-first, role-based, heuristic-guided revision; obsolete comparative workflow is not required. |
| `papers/milcom2026/reference_notes/2024_baye_varmax_milcom_mathpix.md` | RETAIN-SOURCE | Converted reference text; preserve alongside original PDF and page views. Not governing documentation. |
| `papers/milcom2026/reference_notes/2024_wei_multidomain_milcom_mathpix.md` | RETAIN-SOURCE | Converted reference text; preserve alongside original PDF and page views. Not governing documentation. |
| `papers/milcom2026/reference_notes/2025_broggi_varmax_uncertainty_novelty_mathpix.md` | RETAIN-SOURCE | Converted reference text; preserve alongside original PDF and page views. Not governing documentation. |
| `papers/milcom2026/reference_notes/2026_tiwari_dqn_ids_mathpix.md` | RETAIN-SOURCE | Converted reference text; preserve alongside original PDF and page views. Not governing documentation. |
| `papers/milcom2026/reference_notes/2026_trott_rf_varmax_mathpix.md` | RETAIN-SOURCE | Converted reference text; preserve alongside original PDF and page views. Not governing documentation. |
| `papers/milcom2026/reference_notes/PAPER_COMPOSITION_FRAMEWORK.md` | MIGRATE-RETIRE | papers/CONTEXT.md owns successful methodology, paper context owns figure lessons. Gate D: retain useful source-specific observations; discard fixed word counts and superseded figure/table package. |
| `papers/milcom2026/reference_notes/README_PROCESSING.md` | RETIRE | papers/milcom2026/CONTEXT.md owns API-backed Mathpix hook, PDF/page-PNG/MMD validation, paths and package limitations. |
| `papers/milcom2026/reference_notes/REFERENCE_LIBRARY_FRAMEWORK.md` | RETIRE | papers/CONTEXT.md preserves technical-reference versus exemplar distinction, source roles, selection and analysis. Existing cards retain individual evidence; mandatory scoring framework is superseded. |
| `papers/milcom2026/reference_notes/RELATED_WORK_SYNTHESIS.md` | MIGRATE-RETIRE | Gate D: preserve any unique source-role mapping in reference_registry.md; remove unfilled synthesis/status instructions. |
| `papers/milcom2026/reference_notes/candidate_search_log.md` | RETAIN-HISTORY | Search/admission provenance; old next-search tasks are not current instructions. papers/CONTEXT.md owns selection. |
| `papers/milcom2026/reference_notes/exemplar_card_template.md` | RETAIN-OPTIONAL | Gate D: explicitly label long scorecard optional/historical; papers/CONTEXT.md permits focused individual analysis. |
| `papers/milcom2026/reference_notes/papers/2013_scheirer_toward_open_set_recognition/exemplar_card.md` | RETAIN-EVIDENCE | Individual source analysis and transferable lessons; historical scores do not impose a mandatory workflow. |
| `papers/milcom2026/reference_notes/papers/2016_bendale_open_set_deep_networks/exemplar_card.md` | RETAIN-EVIDENCE | Individual source analysis and transferable lessons; historical scores do not impose a mandatory workflow. |
| `papers/milcom2026/reference_notes/papers/2017_guo_calibration_modern_neural_networks/exemplar_card.md` | RETAIN-EVIDENCE | Individual source analysis and transferable lessons; historical scores do not impose a mandatory workflow. |
| `papers/milcom2026/reference_notes/papers/2019_shi_dyspan_unknown_dynamic_rf/exemplar_card.md` | RETAIN-EVIDENCE | Individual source analysis and transferable lessons; historical scores do not impose a mandatory workflow. |
| `papers/milcom2026/reference_notes/papers/2020_liu_energy_ood_detection/exemplar_card.md` | RETAIN-EVIDENCE | Individual source analysis and transferable lessons; historical scores do not impose a mandatory workflow. |
| `papers/milcom2026/reference_notes/papers/2021_fadul_adversarial_spread_spectrum_milcom/exemplar_card.md` | RETAIN-EVIDENCE | Individual source analysis and transferable lessons; historical scores do not impose a mandatory workflow. |
| `papers/milcom2026/reference_notes/papers/2022_sensing_throughput_tradeoffs_gan_nextg_spectrum/exemplar_card.md` | RETAIN-EVIDENCE | Individual source analysis and transferable lessons; historical scores do not impose a mandatory workflow. |
| `papers/milcom2026/reference_notes/papers/2022_specforce_battlefield_spectrum_sensors/exemplar_card.md` | RETAIN-EVIDENCE | Individual source analysis and transferable lessons; historical scores do not impose a mandatory workflow. |
| `papers/milcom2026/reference_notes/papers/2023_searchlight_rf_energy_detection_milcom/exemplar_card.md` | RETAIN-EVIDENCE | Individual source analysis and transferable lessons; historical scores do not impose a mandatory workflow. |
| `papers/milcom2026/reference_notes/papers/2023_stealth_spectrum_sensing_data_falsification_milcom/exemplar_card.md` | RETAIN-EVIDENCE | Individual source analysis and transferable lessons; historical scores do not impose a mandatory workflow. |
| `papers/milcom2026/reference_notes/papers/2024_baye_varmax_milcom/exemplar_card.md` | RETAIN-EVIDENCE | Individual source analysis and transferable lessons; historical scores do not impose a mandatory workflow. |
| `papers/milcom2026/reference_notes/papers/2024_hyperadv_rfml_dynamic_defense_milcom/exemplar_card.md` | RETAIN-EVIDENCE | Individual source analysis and transferable lessons; historical scores do not impose a mandatory workflow. |
| `papers/milcom2026/reference_notes/papers/2024_stitching_spectrum_signal_stitching/exemplar_card.md` | RETAIN-EVIDENCE | Individual source analysis and transferable lessons; historical scores do not impose a mandatory workflow. |
| `papers/milcom2026/reference_notes/papers/2024_wei_multidomain_milcom/exemplar_card.md` | RETAIN-EVIDENCE | Individual source analysis and transferable lessons; historical scores do not impose a mandatory workflow. |
| `papers/milcom2026/reference_notes/papers/2025_broggi_varmax_uncertainty_novelty/exemplar_card.md` | RETAIN-EVIDENCE | Individual source analysis and transferable lessons; historical scores do not impose a mandatory workflow. |
| `papers/milcom2026/reference_notes/papers/2026_tiwari_dqn_ids/exemplar_card.md` | RETAIN-EVIDENCE | Individual source analysis and transferable lessons; historical scores do not impose a mandatory workflow. |
| `papers/milcom2026/reference_notes/papers/2026_trott_rf_modulation_varmax/exemplar_card.md` | RETAIN-EVIDENCE | Individual source analysis and transferable lessons; historical scores do not impose a mandatory workflow. |
| `papers/milcom2026/reference_notes/papers/energy_based_open_world_uncertainty_modeling_for_confidence_calibration/exemplar_card.md` | RETAIN-EVIDENCE | Individual source analysis and transferable lessons; historical scores do not impose a mandatory workflow. |
| `papers/milcom2026/reference_notes/reference_registry.md` | RETAIN-EVIDENCE | Source navigation; provisional scores and citation/admission statuses are historical, not rules. Verify actual citations in manuscript/bibliography. |
| `papers/milcom2026/reference_notes/upload_batches/papers/milcom2026/reference_notes/COMPARATIVE_PROCESS.md` | RETIRE | papers/CONTEXT.md owns actual methodology; paper operations context owns source preparation and helper branch behavior. |
| `papers/milcom2026/reference_notes/upload_batches/papers/milcom2026/reference_notes/hero_figure/comp_analysis.md` | MIGRATE-RETIRE | Gate D: move unique Baye/Wei observations into retained hero heuristics before deleting nested upload-batch copy. |
| `scripts/osr/README.md` | RETIRE | experiments/CONTEXT.md and method contexts route to actual scripts/eval launchers. |
| `scripts/preprocess/README.md` | RETIRE | scripts/preprocess/CONTEXT.md replaces minimal orchestration note. |
| `scripts/train/README.md` | RETIRE | experiments/CONTEXT.md owns the implemented training launchers. |

## Additional reference conversions

The 18 separately inventoried Mathpix `.mmd` artifacts are retained as source
material. They are outside the 74-file Markdown/text ledger; existence alone
does not establish successful OCR. Paper context documents validation.

- `papers/milcom2026/reference_notes/papers/2013_scheirer_toward_open_set_recognition/2013_scheirer_toward_open_set_recognition.mmd`
- `papers/milcom2026/reference_notes/papers/2016_bendale_open_set_deep_networks/2016_bendale_open_set_deep_networks.mmd`
- `papers/milcom2026/reference_notes/papers/2017_guo_calibration_modern_neural_networks/2017_guo_calibration_modern_neural_networks.mmd`
- `papers/milcom2026/reference_notes/papers/2019_shi_dyspan_unknown_dynamic_rf/2019_shi_dyspan_unknown_dynamic_rf.mmd`
- `papers/milcom2026/reference_notes/papers/2020_liu_energy_ood_detection/2020_liu_energy_ood_detection.mmd`
- `papers/milcom2026/reference_notes/papers/2021_fadul_adversarial_spread_spectrum_milcom/2021_fadul_adversarial_spread_spectrum_milcom.mmd`
- `papers/milcom2026/reference_notes/papers/2022_sensing_throughput_tradeoffs_gan_nextg_spectrum/2022_sensing_throughput_tradeoffs_gan_nextg_spectrum.mmd`
- `papers/milcom2026/reference_notes/papers/2022_specforce_battlefield_spectrum_sensors/2022_specforce_battlefield_spectrum_sensors.mmd`
- `papers/milcom2026/reference_notes/papers/2023_searchlight_rf_energy_detection_milcom/2023_searchlight_rf_energy_detection_milcom.mmd`
- `papers/milcom2026/reference_notes/papers/2023_stealth_spectrum_sensing_data_falsification_milcom/2023_stealth_spectrum_sensing_data_falsification_milcom.mmd`
- `papers/milcom2026/reference_notes/papers/2024_baye_varmax_milcom/2024_baye_varmax_milcom.mmd`
- `papers/milcom2026/reference_notes/papers/2024_hyperadv_rfml_dynamic_defense_milcom/2024_hyperadv_rfml_dynamic_defense_milcom.mmd`
- `papers/milcom2026/reference_notes/papers/2024_stitching_spectrum_signal_stitching/2024_stitching_spectrum_signal_stitching.mmd`
- `papers/milcom2026/reference_notes/papers/2024_wei_multidomain_milcom/2024_wei_multidomain_milcom.mmd`
- `papers/milcom2026/reference_notes/papers/2025_broggi_varmax_uncertainty_novelty/2025_broggi_varmax_uncertainty_novelty.mmd`
- `papers/milcom2026/reference_notes/papers/2026_tiwari_dqn_ids/2026_tiwari_dqn_ids.mmd`
- `papers/milcom2026/reference_notes/papers/2026_trott_rf_modulation_varmax/2026_trott_rf_modulation_varmax.mmd`
- `papers/milcom2026/reference_notes/papers/energy_based_open_world_uncertainty_modeling_for_confidence_calibration/energy_based_open_world_uncertainty_modeling_for_confidence_calibration.mmd`
