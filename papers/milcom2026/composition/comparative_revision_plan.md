# Comparative Revision Plan for MILCOM 2026 Paper

This document defines the paper-quality improvement process.

The current paper is technically complete but rhetorically immature. The next phase is not to add more ground-truth content blindly. The next phase is to learn how strong papers communicate similar work and then revise this paper using those lessons.

---

## 1. Goal

Use comparative analysis of excellent papers to improve:

* section structure
* paragraph design
* figure/table placement
* claim-to-evidence flow
* audience fit
* rhetorical strength
* technical credibility

The final paper should preserve the technical truth of the project while reading like a mature IEEE/MILCOM submission.

---

## 2. Core Process

For each target component:

1. Select the component.
2. Select 2--4 exemplar papers or sections.
3. Convert exemplars to:

   * PDF
   * Mathpix Markdown
   * page images
4. Compare exemplars against our current paper.
5. Extract heuristics.
6. Apply heuristics to our paper.
7. Compile and inspect the rendered PDF.
8. Commit the successful iteration.

---

## 3. Components to Analyze

Suggested order:

1. Introduction
2. Related Work
3. Methodology
4. Experimental Design
5. Results
6. Discussion
7. Conclusion
8. Figure captions
9. Table captions
10. Full-paper page flow

---

## 4. Comparative Analysis Questions

For each exemplar:

* What is the section trying to accomplish?
* How quickly does it define the problem?
* How does it establish stakes?
* How does it introduce the gap?
* How does it state contributions?
* How does it sequence technical detail?
* Where are figures/tables introduced?
* How much does the text explain versus defer to figures?
* How long are paragraphs?
* How does it avoid overclaiming?
* What sentence patterns make it sound credible?
* What does it leave out?

For our paper:

* Where do we overexplain?
* Where do we underexplain?
* Where do we introduce claims before context?
* Where do we bury the important contribution?
* Where does the prose sound generic?
* Where does the section fail the likely reviewer expectation?

---

## 5. Output of Each Comparative Analysis

Each comparative analysis should produce:

1. Summary of exemplar strengths.
2. Diagnosis of our current section.
3. Transferable heuristics.
4. Specific rewrite plan.
5. Optional rewritten section.
6. Compile/render instructions.
7. Git commit instructions.

---

## 6. Example Heuristic Format

```text
Heuristic:
A MILCOM methodology section should lead with task definition and evaluation protocol before algorithmic detail.

Why:
Reviewers need to understand what is being measured before they evaluate whether the method is appropriate.

Apply to our paper:
Move experimental regimes out of Methodology if they interrupt the DQNGuard definition; keep Methodology focused on the pipeline and decision rule.
```

---

## 7. Sourcing Exemplar Papers

Good exemplars should be chosen deliberately.

Potential categories:

* MILCOM 2024/2025 RF, communications, or ML-security papers
* accepted labmate papers
* open-set recognition papers with strong methods/results sections
* signal-processing papers with excellent figures
* IEEE papers with concise contribution framing

ScholarGPT may be used to find candidates. Once candidates are chosen, add them to `papers/milcom2026/reference_notes/`.

---

## 8. Warning

Do not rewrite the paper into generic AI prose.

The goal is not merely grammatical improvement. The goal is to make the paper more convincing to the actual audience while preserving the project’s real logic and the advisor/lab framing.
