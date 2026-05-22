# MILCOM 2026 Hand-In Manifest

This file documents the final hand-in source state for the MILCOM 2026 DQNGuard paper.

## Paper

Title:

    DQNGuard: Towards Open-World RF Preliminary-Action Detection

Main source:

    main.tex

Section directory:

    sections/

Bibliography:

    references.bib

Expected compiled length:

    6 pages

## Final Section Order

    Abstract
    I. Introduction
    II. Related Works
    III. Methodology
    IV. Experimental Design
    V. Results
    VI. Discussion
    VII. Conclusion
    References

## Final Figures and Table

Figure 1:

    End-to-end DQNGuard evidence flow
    figures/hero_figure/hero_dqnguard_pipeline_s22_tikz.pdf

Figure 2:

    Target--Surrogate Matrix
    figures/target_surrogate_matrix/target_surrogate_unknown_f1_matrix.pdf

Table I:

    Fixed Scan-surrogate OSR comparison
    tables/main_results/main_osr_results_table.tex

## Final Core Claims

1. DQNGuard is a budgeted OSR decision layer for OTA RF preliminary-action recognition.
2. DQNGuard improves the fixed-budget operating point relative to VarMax and a DQN-IDS-style confidence head.
3. Surrogate-open calibration is target-dependent.
4. The Target--Surrogate Matrix is a useful diagnostic for surrogate transfer.
5. The method is a sensing and triage layer for QR-CWoS, not a complete response system.

## Build Verification

From this directory:

    latexmk -C -outdir=build main.tex >/dev/null 2>&1 || true
    latexmk -pdf -bibtex -interaction=nonstopmode -file-line-error -synctex=1 -outdir=build main.tex
    latexmk -pdf -bibtex -interaction=nonstopmode -file-line-error -synctex=1 -outdir=build main.tex
    latexmk -pdf -bibtex -interaction=nonstopmode -file-line-error -synctex=1 -outdir=build main.tex

Expected:

    pdfinfo build/main.pdf | grep Pages
    Pages: 6

    pdftotext build/main.pdf - | grep -n "\?\?\|\[\?\]" || true
    No output

## Overleaf Migration Warning

If Overleaf shows the Target--Surrogate Matrix on page 1, or if the Abstract begins with Results text, the section files are mismatched. Re-export a clean ZIP and upload into a new blank Overleaf project.

