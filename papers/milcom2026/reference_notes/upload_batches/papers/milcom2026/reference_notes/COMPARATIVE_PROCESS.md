# Comparative Analysis Pipeline

This document outlines the iterative process for designing and refining aspects of the paper via comparative analysis of reference papers.

## Workflow Overview

- **Aspects:** Each component or section of the paper (e.g., hero figure, related work, methodology, results) is treated as an "aspect" to be refined.
- **Reference Selection:** For each aspect, select two (or more) relevant reference papers from which to draw inspiration.
- **Separate Branch:** Create a new Git branch (e.g., `comp-<aspect>`) to isolate changes for that aspect.
- **Workspace Setup:** Branch off from the latest main version of the paper, which includes all current text, figures, and configuration.
- **Perform Analysis:**
  1. Prepare the sources: generate Mathpix markdown and page images for relevant sections of the reference papers.
  2. Use ChatGPT to compare the references on the target aspect, focusing on differences and best practices.
  3. Extract heuristics or design principles from each reference.
  4. Synthesize a combined set of heuristics tailored to our paper.
- **Documentation:** Save the entire analysis (including extracted heuristics) in a Markdown file under `reference_notes/<aspect>/`.
- **Implement and Commit:**
  - Apply the new heuristics to design the actual component (e.g., create or update a figure or section).
  - Commit the changes (analysis file, updated figure/section) on the current branch with a descriptive message.
- **Iterate:** Optionally iterate with additional references or adjustments.
- **Integration:** Once the design is approved, merge the branch into the main paper.

## File Organization

- `papers/milcom2026/reference_notes/COMPARATIVE_PROCESS.md` — This overview of the process (current file).
- `papers/milcom2026/reference_notes/<aspect>/comp_analysis.md` — Comparative analysis for each aspect.
- `PAPER_COMPOSITION_FRAMEWORK.md` — Updated after each analysis with new heuristics.
- Figures, tables, and LaTeX edits reside in the main paper directory.

## Branch Strategy

- Use separate branches for each comparative analysis (e.g., `comp-hero-figure`).
- Each branch begins from `main` (or the latest stable version).
- Branch contains:
  - Full paper source (inherited from main at branch creation).
  - New or updated files for the aspect.
- After analysis and implementation, commit and push the branch.

## Goals of Comparative Analysis

- **Evidence-Based Design:** Ensure each element of the paper is justified by examples from published work.
- **Modular Refinement:** Tackle one aspect at a time, enabling focused improvements.
- **Traceable Rationale:** Maintain a clear record of why design decisions were made.
- **Reproducibility:** Have a repeatable process that can be applied to future papers or sections.
