# MILCOM 2026 Paper Setup

This repository was initialized from the Overleaf source export.

## Main files

- `main.tex` — top-level paper file, renamed from `conference_101719.tex`
- `sections/` — section-level LaTeX files
- `references.bib` — BibTeX bibliography
- `IEEEtran.cls` — IEEE conference template class
- `fig1.png` — current figure asset

## Build once

```bash
make
```

The compiled PDF will be written to:

```text
build/main.pdf
```

## Auto-build while editing

```bash
make watch
```

## Browser preview over Tailscale

In another terminal from the repo root:

```bash
TS_IP=$(tailscale ip -4 | head -n 1)
python3 -m http.server 8123 --bind "$TS_IP"
```

Then open this on your laptop:

```text
http://<linux-tailscale-ip>:8123/preview.html
```

## Git workflow

```bash
git status
git add .
git commit -m "Update MILCOM draft"
git push
```

ChatGPT's GitHub connector will see the paper after the changes are pushed to GitHub.
