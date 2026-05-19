# Hero Figure Comparative Analysis

We compare two reference papers for guidance on designing the "hero" pipeline figure:

- Baye et al., *“varmax: Towards Confidence-Based Zero-Day Attack Recognition”* (MILCOM 2024).
- Wei et al., *“Exploiting Multi-Domain Features for Detection of Unclassified Electromagnetic Signals”* (MILCOM 2024).

These papers were selected because they are recent MILCOM publications with relevant pipeline or system diagrams.

## Analysis of Baye et al.

- Baye et al. emphasize clear conceptual diagrams. They introduce **Figure 1: an OSR (Open-Set Recognition) concept flow**, and **Figure 3: the varMax pipeline** early in the paper.
- They use multiple figures to build intuition (conceptual timeline, pipeline), then present heavy results figures later.
- **Lessons:** Use a high-level flow diagram to explain our method components in context.

### Heuristics from Baye et al.
- **Conceptual clarity:** Include a high-level flow diagram of the system (e.g., how unknown signals flow through DQNGuard). Avoid purely textual explanations.
- **Early placement:** Place the pipeline diagram near the description of the algorithm.
- **Separate results:** Delay metric-heavy figures to later pages, keeping method pages focused on concepts.

## Analysis of Wei et al.

- Wei et al. present one dominant system diagram (**Figure 1:** DUNES framework) that encapsulates the whole method (multi-domain feature extraction, autoencoders, GAN).
- They also include compact tables for network architecture and training parameters.
- Their results page has one central figure (feature-space visualization, ROC plots) and one table.
- **Lessons:** A polished, self-contained system diagram is effective. Limit the number of distinct figures on the method pages.

### Heuristics from Wei et al.
- **Single diagram focus:** Use one comprehensive system diagram rather than many small plots or equations.
- **Clean layout:** Group elements in logical blocks with consistent styling for clarity.
- **Support with tables:** Use tables for detailed parameters, freeing up space for the main figure.

## Combined Heuristics for Hero Figure

Based on the above, we derive the following guidelines for our hero figure:

- **H1:** Do not place any figure on the title/abstract page. Reserve page 1 for motivation and contributions.
- **H2:** Introduce the main system/pipeline figure at the beginning of the Methods section (e.g., top of page 2).
- **H3:** Design a single "hero" figure that layers our system context with DQNGuard details:
  - Show the RF evidence pipeline for QR-CWoS, including known/unknown decision.
  - Highlight the DQNGuard decision steps (predicted class, calibration, threshold) within that flow.
- **H4:** Use labeled blocks, arrows, and stages. For example:
  1. Input RF window & backbone outputs.
  2. Predicted-class calibration.
  3. Variance/energy guard score.
  4. Budgeted threshold decision.
- **H5:** Emulate Wei’s unified flow style; avoid separate small figures for each step.
- **H6:** Provide a descriptive caption (explaining how evidence flows through DQNGuard to known/unknown outputs).
- **H7:** Avoid pseudocode or dense equations; the figure should communicate the logic visually.
