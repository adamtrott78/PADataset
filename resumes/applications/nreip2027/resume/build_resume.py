#!/usr/bin/env python3

from __future__ import annotations

import argparse
import html
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image


PAGE_W = 612.0
PAGE_H = 792.0

LEFT = 38.0
RIGHT = 38.0
CONTENT_W = PAGE_W - LEFT - RIGHT
BOTTOM = 30.0

FONT_FAMILY = "Liberation Sans"

NAME_SIZE = 18.8
CONTACT_SIZE = 9.0
SECTION_SIZE = 10.4
HEADING_SIZE = 9.6
BODY_SIZE = 9.1
META_SIZE = 8.8
PUB_SIZE = 8.9

BODY_LEADING = 10.45
META_LEADING = 9.95
HEADING_LEADING = 10.85
PUB_LEADING = 9.95

PUBLIC_CONTACT = "[private phone] | [university email]"
PUBLIC_CREDENTIAL = (
    "[private government application credential - withheld] | Jan. 2026-Present"
)

ROOT = Path(__file__).resolve().parent
APP_ROOT = ROOT.parent

PLAN_PATH = APP_ROOT / "RESUME_PLAN.md"
SPEC_PATH = APP_ROOT / "SVG_PRODUCTION_SPEC.md"
PRIVATE_OVERLAY_PATH = APP_ROOT / "private" / "RESUME_OVERLAY.md"

PUBLIC_DIR = ROOT / "public"
PRIVATE_DIR = ROOT / "private"


CONTENT = {
    "education": {
        "institution_grad": "University of Massachusetts Dartmouth",
        "degree_grad": (
            "Ph.D. in Engineering and Applied Science (EAS), Computer Science "
            "and Information Science (CSIS) Curriculum Option"
        ),
        "grad_meta": "Expected May 2030 | Graduate GPA: 4.0/4.0",
        "coursework_label": "Selected Graduate Coursework:",
        "coursework": (
            "Network Security & Data Assurance; Secure Software Development; "
            "Fundamentals of Deep Learning; Mathematics of Deep Learning; "
            "Scientific Machine Learning (in progress, Fall 2026)"
        ),
        "institution_bs": "University of Massachusetts Dartmouth",
        "degree_bs": (
            "B.S. in Computer Science, Cybersecurity concentration | May 2025"
        ),
        "bs_meta": "GPA: 3.379/4.0 | Cum Laude",
    },
    "research": {
        "ra_heading": (
            "Research Assistant - University of Massachusetts Dartmouth | "
            "Dartmouth, MA"
        ),
        "ra_dates": "Jun-Aug 2025; Jun-Aug 2026",
        "ra_bullet": (
            "Developed and tested an operational-AI red-teaming framework on an "
            "autonomous vehicle with cybersecurity, computer science, and "
            "electrical-engineering researchers using ROS2 and Gazebo."
        ),
        "dqn_title": "DQNGuard: Towards Open-World RF Preliminary-Action Detection",
        "dqn_meta": "First author | IEEE MILCOM 2026, accepted/to appear",
        "dqn_bullets": [
            (
                "Designed and implemented the end-to-end DQNGuard pipeline for "
                "open-world RF preliminary-action detection, including a "
                "multi-domain CNN and open-set decision layer; benchmarked "
                "against VarMax and a DQN-IDS-style baseline."
            ),
            (
                "Built an over-the-air SDR capture, preprocessing, and dataset "
                "pipeline for WiFi, Bluetooth, and Zigbee RF signals; designed, "
                "trained, and evaluated experiments across five preliminary "
                "actions: Scan, Burst, Sustain, Hop, and Replay."
            ),
            (
                "Achieved 0.865 mean unknown-class F1 under a 5% known-rejection "
                "calibration budget, compared with 0.745 for VarMax and 0.701 "
                "for the DQN-IDS-style comparison head; designed and analyzed "
                "a 20-condition Target-Surrogate Matrix."
            ),
        ],
        "hicss_title": (
            "Model Evaluation for Radio-Frequency Signal Modulation Classifiers "
            "in the Existence of Novel Samples"
        ),
        "hicss_meta": (
            "First author | HICSS-59, published 2026; presented Jan. 8, 2026"
        ),
        "hicss_bullets": [
            (
                "Developed and evaluated a class-conditioned RF "
                "open-set-recognition pipeline using an eight-channel CNN over "
                "raw I/Q, FFT, DCT, and polar representations."
            ),
            (
                "Evaluated nine open-set folds on RadioML 2018.01A, withholding "
                "one selected modulation as unknown per fold and running 30 "
                "runs per fold."
            ),
        ],
    },
    "publications": [
        (
            'Trott, A., Popillo, C., Bastian, N. D., Zhou, R., and Kul, G. '
            '"DQNGuard: Towards Open-World RF Preliminary-Action Detection." '
            "IEEE MILCOM 2026, accepted/to appear."
        ),
        (
            'Trott, A., Thompson, H., and Kul, G. "Model Evaluation for '
            "Radio-Frequency Signal Modulation Classifiers in the Existence of "
            'Novel Samples." Proceedings of the 59th Hawaii International '
            "Conference on System Sciences (HICSS-59), 2026."
        ),
    ],
    "skills": [
        (
            "AI / Machine Learning:",
            (
                "Python, PyTorch, Hugging Face, Jupyter; CNNs, transformers, "
                "open-set recognition, novelty/OOD detection, model calibration, "
                "experimental design, quantitative/statistical evaluation"
            ),
        ),
        (
            "RF / Signal Processing:",
            (
                "software-defined radio (SDR), RF signal analysis, complex I/Q, "
                "FFT, DCT, and polar representations; over-the-air WiFi, "
                "Bluetooth, and Zigbee data workflows"
            ),
        ),
        (
            "Cybersecurity / Systems / Software:",
            (
                "Linux/WSL, Docker/Docker Compose, networking, OpenSSL, Autopsy, "
                "Burp Suite, Flask, MongoDB, Nginx, ROS2, Gazebo"
            ),
        ),
    ],
    "experience": {
        "capstone_heading": (
            "Lead Backend Developer & Project Manager - UMass Dartmouth "
            "Senior Design Capstone"
        ),
        "capstone_meta": "Client: NUWC Newport | Sep. 2024-May 2025",
        "capstone_bullet": (
            "Led backend development and project management for a university "
            "team building a file-storage, viewing, and search system for a "
            "NUWC Newport client; coordinated technical work and delivery with "
            "the client."
        ),
        "cyber_heading": (
            "Teaching Assistant - Cyber Defense and Operations - "
            "University of Massachusetts Dartmouth | Jan.-May 2026"
        ),
        "cyber_bullets": [
            (
                "Designed and graded practical cybersecurity assignments "
                "involving risk analysis, cryptography, WebGoat SQL injection, "
                "and Burp Suite access-control/authentication attacks."
            ),
            (
                "Authored a Caesar Cipher/DES/3DES cryptanalysis project "
                "requiring candidate-key generation, brute-force search, "
                "plaintext verification, performance measurement, analytical "
                "reporting, and a recorded demonstration."
            ),
        ],
        "forensics_heading": (
            "Teaching Assistant - Digital Forensics - University of "
            "Massachusetts Dartmouth | Sep.-Dec. 2025"
        ),
        "forensics_bullet": (
            "Created Autopsy disk-image and Docker-based macOS log-analysis labs "
            "and guided students through query construction, visualization, and "
            "incident-style reporting."
        ),
    },
}


def run(cmd: list[str], *, capture: bool = False) -> str:
    proc = subprocess.run(
        cmd,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    return proc.stdout if capture else ""


def require_command(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(f"required command not found: {name}")


def fc_file(pattern: str) -> Path:
    result = run(
        ["fc-match", "-f", "%{file}\n", pattern],
        capture=True,
    ).strip().splitlines()

    if not result:
        raise RuntimeError(f"font not found: {pattern}")

    path = Path(result[0])
    if not path.is_file():
        raise RuntimeError(f"font path does not exist: {path}")
    return path


FONT_PATHS = {
    "regular": fc_file("Liberation Sans:style=Regular"),
    "bold": fc_file("Liberation Sans:style=Bold"),
    "italic": fc_file("Liberation Sans:style=Italic"),
    "bold_italic": fc_file("Liberation Sans:style=Bold Italic"),
}


class FontMetric:
    def __init__(self, path: Path):
        font = TTFont(path)
        self.units_per_em = font["head"].unitsPerEm
        self.hmtx = font["hmtx"].metrics
        self.cmap = font.getBestCmap()
        self.notdef = self.hmtx.get(".notdef", (self.units_per_em, 0))[0]

    def width(self, text: str, size: float) -> float:
        total = 0
        for char in text:
            glyph = self.cmap.get(ord(char))
            if glyph is None:
                total += self.notdef
            else:
                total += self.hmtx.get(glyph, (self.notdef, 0))[0]
        return total * size / self.units_per_em


METRICS = {
    key: FontMetric(path)
    for key, path in FONT_PATHS.items()
}


def measure(text: str, size: float, style: str = "regular") -> float:
    return METRICS[style].width(text, size)


def wrap(
    text: str,
    max_width: float,
    size: float,
    style: str = "regular",
) -> list[str]:
    words = text.split()
    if not words:
        return [""]

    lines: list[str] = []
    current = words[0]

    for word in words[1:]:
        candidate = current + " " + word
        if measure(candidate, size, style) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word

    lines.append(current)
    return lines


def norm(text: str) -> str:
    text = (
        text.replace("–", "-")
        .replace("—", "-")
        .replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
    )
    return re.sub(r"\s+", " ", text).strip()


def norm_locked_source(text: str) -> str:
    """Normalize Markdown presentation syntax for source-content comparison."""
    text = text.replace("**", "")
    text = text.replace("*", "")
    text = text.replace("`", "")
    return norm(text)


def verify_locked_sources() -> None:
    plan = PLAN_PATH.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")

    if "Status: **CONTENT LOCKED**" not in plan:
        raise RuntimeError("RESUME_PLAN.md is not content locked.")

    if "Status: **PRODUCTION LOCKED**" not in spec:
        raise RuntimeError("SVG_PRODUCTION_SPEC.md is not production locked.")

    plan_n = norm_locked_source(plan)

    required = [
        CONTENT["education"]["institution_grad"],
        CONTENT["education"]["degree_grad"],
        CONTENT["education"]["grad_meta"],
        CONTENT["education"]["institution_bs"],
        CONTENT["education"]["degree_bs"],
        CONTENT["education"]["bs_meta"],
        CONTENT["research"]["dqn_title"],
        CONTENT["research"]["dqn_meta"],
        CONTENT["research"]["hicss_title"],
        CONTENT["research"]["hicss_meta"],
        *CONTENT["research"]["dqn_bullets"],
        *CONTENT["research"]["hicss_bullets"],
        *CONTENT["publications"],
        CONTENT["experience"]["capstone_bullet"],
        *CONTENT["experience"]["cyber_bullets"],
        CONTENT["experience"]["forensics_bullet"],
    ]

    for label, body in CONTENT["skills"]:
        required.extend([label, body])

    for item in required:
        if norm(item) not in plan_n:
            raise RuntimeError(
                "builder content does not match locked RESUME_PLAN.md: "
                + item[:80]
            )


def private_values() -> tuple[str, str]:
    if not PRIVATE_OVERLAY_PATH.is_file():
        raise RuntimeError("private overlay is missing.")

    text = PRIVATE_OVERLAY_PATH.read_text(encoding="utf-8")

    if "Status: **CONTENT LOCKED — PRIVATE — DO NOT COMMIT**" not in text:
        raise RuntimeError("private overlay is not content locked.")

    credential_match = re.search(
        r"## Chosen NREIP wording.*?^\s*\"([^\n\"]+)\"\s*$",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if not credential_match:
        raise RuntimeError("could not parse private credential.")

    contact_section = re.search(
        r"## Private professional contact fields(.*?)(?=^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if not contact_section:
        raise RuntimeError("private contact section not found.")

    contact_match = re.search(
        r"^`([^`\n]*\|[^`\n]*)`\s*$",
        contact_section.group(1),
        re.MULTILINE,
    )
    if not contact_match:
        raise RuntimeError("could not parse private header contact line.")

    credential = credential_match.group(1).strip()
    contact = contact_match.group(1).strip()

    if "\n" in credential or "\n" in contact:
        raise RuntimeError("private substitutions must be single-line.")

    return contact, credential


@dataclass
class Page:
    number: int
    elements: list[str]
    y: float

    def add_raw(self, value: str) -> None:
        self.elements.append(value)

    def text(
        self,
        value: str,
        *,
        x: float,
        y: float,
        size: float,
        style: str = "regular",
        anchor: str = "start",
        fill: str = "#111111",
        letter_spacing: float | None = None,
    ) -> None:
        weight = "700" if "bold" in style else "400"
        italic = "italic" if "italic" in style else "normal"

        attrs = [
            f'x="{x:.2f}"',
            f'y="{y:.2f}"',
            f'font-family="{FONT_FAMILY}"',
            f'font-size="{size:.2f}"',
            f'font-weight="{weight}"',
            f'font-style="{italic}"',
            f'fill="{fill}"',
            f'text-anchor="{anchor}"',
        ]
        if letter_spacing is not None:
            attrs.append(f'letter-spacing="{letter_spacing:.2f}"')

        self.add_raw(
            "<text "
            + " ".join(attrs)
            + ">"
            + html.escape(value)
            + "</text>"
        )

    def wrapped(
        self,
        value: str,
        *,
        x: float,
        max_width: float,
        size: float,
        leading: float,
        style: str = "regular",
        fill: str = "#111111",
        hanging: float = 0.0,
    ) -> int:
        first_width = max_width
        lines = wrap(value, first_width, size, style)

        for idx, line in enumerate(lines):
            line_x = x if idx == 0 else x + hanging
            self.text(
                line,
                x=line_x,
                y=self.y,
                size=size,
                style=style,
                fill=fill,
            )
            self.y += leading

        return len(lines)

    def assert_fit(self) -> None:
        if self.y > PAGE_H - BOTTOM:
            raise RuntimeError(
                f"page {self.number} overflow: y={self.y:.1f}, "
                f"limit={PAGE_H - BOTTOM:.1f}"
            )


def section(page: Page, title: str, *, top_gap: float = 9.0) -> None:
    page.y += top_gap
    page.text(
        title,
        x=LEFT,
        y=page.y,
        size=SECTION_SIZE,
        style="bold",
        letter_spacing=0.35,
    )
    rule_y = page.y + 3.1
    page.add_raw(
        f'<line x1="{LEFT:.2f}" y1="{rule_y:.2f}" '
        f'x2="{PAGE_W - RIGHT:.2f}" y2="{rule_y:.2f}" '
        'stroke="#202020" stroke-width="0.75"/>'
    )
    page.y += 13.8


def heading(page: Page, value: str, *, gap: float = 0.0) -> None:
    page.y += gap
    page.wrapped(
        value,
        x=LEFT,
        max_width=CONTENT_W,
        size=HEADING_SIZE,
        leading=HEADING_LEADING,
        style="bold",
    )


def metadata(page: Page, value: str, *, gap: float = 1.0) -> None:
    page.y += gap
    page.wrapped(
        value,
        x=LEFT,
        max_width=CONTENT_W,
        size=META_SIZE,
        leading=META_LEADING,
        style="regular",
        fill="#333333",
    )


def bullet(page: Page, value: str, *, gap: float = 2.7) -> None:
    page.y += gap
    bullet_x = LEFT + 6.0
    text_x = LEFT + 17.0

    page.add_raw(
        f'<circle cx="{bullet_x:.2f}" cy="{page.y - 2.7:.2f}" '
        'r="1.65" fill="#111111"/>'
    )

    page.wrapped(
        value,
        x=text_x,
        max_width=(PAGE_W - RIGHT - text_x),
        size=BODY_SIZE,
        leading=BODY_LEADING,
        style="regular",
    )


def inline_label_block(
    page: Page,
    label: str,
    value: str,
    *,
    size: float = BODY_SIZE,
    leading: float = BODY_LEADING,
    gap: float = 0.0,
) -> None:
    page.y += gap

    label_width = measure(label + " ", size, "bold")
    words = value.split()

    first_words: list[str] = []
    rest_start = 0

    for i in range(len(words)):
        candidate = " ".join(words[: i + 1])
        if measure(candidate, size, "regular") + label_width <= CONTENT_W:
            first_words = words[: i + 1]
            rest_start = i + 1
        else:
            break

    if not first_words:
        page.text(
            label,
            x=LEFT,
            y=page.y,
            size=size,
            style="bold",
        )
        page.y += leading
        rest = value
    else:
        first_text = " ".join(first_words)

        page.text(
            label,
            x=LEFT,
            y=page.y,
            size=size,
            style="bold",
        )
        page.text(
            first_text,
            x=LEFT + label_width,
            y=page.y,
            size=size,
            style="regular",
        )
        page.y += leading
        rest = " ".join(words[rest_start:])

    if rest:
        page.wrapped(
            rest,
            x=LEFT,
            max_width=CONTENT_W,
            size=size,
            leading=leading,
            style="regular",
        )


def publication(page: Page, value: str, *, gap: float = 3.5) -> None:
    page.y += gap
    lines = wrap(value, CONTENT_W, PUB_SIZE, "regular")

    for idx, line in enumerate(lines):
        x = LEFT if idx == 0 else LEFT + 12.0
        page.text(
            line,
            x=x,
            y=page.y,
            size=PUB_SIZE,
            style="regular",
        )
        page.y += PUB_LEADING


def build_page(contact: str, credential: str) -> Page:
    page = Page(number=1, elements=[], y=40.0)

    page.text(
        "ADAM TROTT",
        x=PAGE_W / 2,
        y=page.y,
        size=NAME_SIZE,
        style="bold",
        anchor="middle",
    )
    page.y += 14.0

    page.text(
        contact,
        x=PAGE_W / 2,
        y=page.y,
        size=CONTACT_SIZE,
        style="regular",
        anchor="middle",
        fill="#303030",
    )
    page.y += 2.5

    section(page, "EDUCATION", top_gap=5.0)

    heading(page, CONTENT["education"]["institution_grad"])
    heading(
        page,
        CONTENT["education"]["degree_grad"],
        gap=0.8,
    )
    metadata(page, CONTENT["education"]["grad_meta"], gap=0.4)

    page.y += 0.7
    page.wrapped(
        credential,
        x=LEFT,
        max_width=CONTENT_W,
        size=9.0,
        leading=10.2,
        style="bold",
    )

    inline_label_block(
        page,
        CONTENT["education"]["coursework_label"],
        CONTENT["education"]["coursework"],
        size=8.9,
        leading=10.0,
        gap=1.3,
    )

    heading(
        page,
        CONTENT["education"]["institution_bs"],
        gap=3.8,
    )
    heading(
        page,
        CONTENT["education"]["degree_bs"],
        gap=0.6,
    )
    metadata(page, CONTENT["education"]["bs_meta"], gap=0.3)

    section(page, "RESEARCH EXPERIENCE", top_gap=5.8)

    heading(page, CONTENT["research"]["ra_heading"])
    metadata(page, CONTENT["research"]["ra_dates"], gap=0.4)
    bullet(page, CONTENT["research"]["ra_bullet"], gap=1.8)

    heading(page, CONTENT["research"]["dqn_title"], gap=3.8)
    metadata(page, CONTENT["research"]["dqn_meta"], gap=0.4)

    for item in CONTENT["research"]["dqn_bullets"]:
        bullet(page, item, gap=1.8)

    heading(page, CONTENT["research"]["hicss_title"], gap=3.8)
    metadata(page, CONTENT["research"]["hicss_meta"], gap=0.4)

    for item in CONTENT["research"]["hicss_bullets"]:
        bullet(page, item, gap=1.8)

    section(page, "SELECTED PUBLICATIONS", top_gap=5.7)
    publication(page, CONTENT["publications"][0], gap=0.2)
    publication(page, CONTENT["publications"][1], gap=2.8)

    section(page, "TECHNICAL SKILLS", top_gap=5.5)

    for idx, (label, body) in enumerate(CONTENT["skills"]):
        inline_label_block(
            page,
            label,
            body,
            size=8.9,
            leading=9.95,
            gap=0.0 if idx == 0 else 1.8,
        )

    section(
        page,
        "SELECTED TECHNICAL AND TEACHING EXPERIENCE",
        top_gap=5.6,
    )

    heading(page, CONTENT["experience"]["capstone_heading"])
    metadata(page, CONTENT["experience"]["capstone_meta"], gap=0.4)
    bullet(page, CONTENT["experience"]["capstone_bullet"], gap=1.8)

    heading(page, CONTENT["experience"]["cyber_heading"], gap=3.8)
    for item in CONTENT["experience"]["cyber_bullets"]:
        bullet(page, item, gap=1.8)

    heading(page, CONTENT["experience"]["forensics_heading"], gap=3.8)
    bullet(page, CONTENT["experience"]["forensics_bullet"], gap=1.8)

    page.assert_fit()

    return page

def svg(page: Page) -> str:
    body = "\n  ".join(page.elements)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     width="8.5in"
     height="11in"
     viewBox="0 0 612 792">
  <rect x="0" y="0" width="612" height="792" fill="#ffffff"/>
  {body}
</svg>
"""


def render_svg_to_pdf(svg_path: Path, pdf_path: Path) -> None:
    run(
        [
            "inkscape",
            str(svg_path),
            "--export-area-page",
            f"--export-filename={pdf_path}",
        ]
    )


def merge_pdf(page1: Path, page2: Path, output: Path) -> None:
    run(
        [
            "gs",
            "-q",
            "-dSAFER",
            "-dBATCH",
            "-dNOPAUSE",
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.6",
            f"-sOutputFile={output}",
            str(page1),
            str(page2),
        ]
    )


def pdfinfo(path: Path) -> str:
    return run(["pdfinfo", str(path)], capture=True)


def extract_text(path: Path) -> str:
    return run(["pdftotext", "-layout", str(path), "-"], capture=True)


def validate_pdf(path: Path, *, private: bool) -> str:
    info = pdfinfo(path)

    pages = re.search(r"^Pages:\s+(\d+)\s*$", info, re.MULTILINE)
    if not pages or int(pages.group(1)) != 1:
        raise RuntimeError("PDF is not exactly 1 page.")

    size = re.search(
        r"^Page size:\s+([\d.]+) x ([\d.]+) pts",
        info,
        re.MULTILINE,
    )
    if not size:
        raise RuntimeError("could not determine PDF page size.")

    width = float(size.group(1))
    height = float(size.group(2))

    if abs(width - 612.0) > 1.0 or abs(height - 792.0) > 1.0:
        raise RuntimeError(
            f"unexpected PDF page size: {width} x {height}"
        )

    encrypted = re.search(
        r"^Encrypted:\s+(\S+)",
        info,
        re.MULTILINE,
    )
    if encrypted and encrypted.group(1).lower() != "no":
        raise RuntimeError("PDF is encrypted.")

    byte_size = path.stat().st_size
    if byte_size >= 1_000_000:
        raise RuntimeError(
            f"PDF exceeds strict NREIP size limit: {byte_size} bytes"
        )

    extracted = extract_text(path)
    extracted_n = norm(extracted)

    required_tokens = [
        "ADAM TROTT",
        "University of Massachusetts Dartmouth",
        "DQNGuard",
        "open-world RF preliminary-action detection",
        "0.865",
        "RadioML 2018.01A",
        "NUWC Newport",
        "Cyber Defense and Operations",
        "Digital Forensics",
    ]

    for token in required_tokens:
        if norm(token) not in extracted_n:
            raise RuntimeError(
                f"required extracted text missing: {token}"
            )

    required_content = [
        CONTENT["research"]["ra_bullet"],
        *CONTENT["research"]["dqn_bullets"],
        *CONTENT["research"]["hicss_bullets"],
        *CONTENT["publications"],
        CONTENT["experience"]["capstone_bullet"],
        *CONTENT["experience"]["cyber_bullets"],
        CONTENT["experience"]["forensics_bullet"],
    ]

    for item in required_content:
        if norm(item) not in extracted_n:
            raise RuntimeError(
                "locked content missing or altered in PDF extraction: "
                + item[:80]
            )

    if private:
        contact, credential = private_values()

        if norm(contact) not in extracted_n:
            raise RuntimeError(
                "private contact substitution missing from PDF."
            )

        if norm(credential) not in extracted_n:
            raise RuntimeError(
                "private credential substitution missing from PDF."
            )

    return extracted


def render_poppler(pdf: Path, out_dir: Path) -> list[Path]:
    prefix = out_dir / "_render"
    run(
        [
            "pdftoppm",
            "-png",
            "-r",
            "200",
            str(pdf),
            str(prefix),
        ]
    )

    page = out_dir / "_render-1.png"
    if not page.is_file():
        raise RuntimeError(f"expected render missing: {page}")
    return [page]

def render_ghostscript(pdf: Path, temp_dir: Path) -> list[Path]:
    pattern = temp_dir / "gs-%d.png"

    run(
        [
            "gs",
            "-q",
            "-dSAFER",
            "-dBATCH",
            "-dNOPAUSE",
            "-sDEVICE=png16m",
            "-r200",
            f"-sOutputFile={pattern}",
            str(pdf),
        ]
    )

    page = temp_dir / "gs-1.png"

    if not page.is_file():
        raise RuntimeError("Ghostscript secondary render failed.")

    return [page]

def create_contact_sheet(
    page1: Path,
    page2: Path,
    output: Path,
) -> None:
    images = [
        Image.open(page1).convert("RGB"),
        Image.open(page2).convert("RGB"),
    ]

    target_h = 1100
    thumbs = []

    for image in images:
        scale = target_h / image.height
        target_w = round(image.width * scale)
        thumbs.append(
            image.resize(
                (target_w, target_h),
                Image.Resampling.LANCZOS,
            )
        )

    gap = 24
    margin = 18
    width = sum(img.width for img in thumbs) + gap + margin * 2
    height = target_h + margin * 2

    sheet = Image.new("RGB", (width, height), "white")

    x = margin
    for image in thumbs:
        sheet.paste(image, (x, margin))
        x += image.width + gap

    sheet.save(output, "PNG")


def check_renderer_dimensions(
    poppler_pages: list[Path],
    gs_pages: list[Path],
) -> None:
    for idx, (poppler, ghostscript) in enumerate(
        zip(poppler_pages, gs_pages),
        1,
    ):
        with Image.open(poppler) as a, Image.open(ghostscript) as b:
            if a.size != b.size:
                raise RuntimeError(
                    f"renderer page-size disagreement on page {idx}: "
                    f"{a.size} vs {b.size}"
                )


def cleanup_dir(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    for name in (
        "nreip2027_resume_public.svg",
        "nreip2027_resume_public.pdf",
        "nreip2027_resume.svg",
        "nreip2027_resume.pdf",
        "page1.png",
        "_render-1.png",
        # Obsolete first two-page prototype outputs:
        "nreip2027_resume_public_page1.svg",
        "nreip2027_resume_public_page2.svg",
        "nreip2027_resume_page1.svg",
        "nreip2027_resume_page2.svg",
        "page2.png",
        "contact_sheet.png",
    ):
        candidate = out_dir / name
        if candidate.exists():
            candidate.unlink()

def scan_public_for_private_values() -> None:
    if not PUBLIC_DIR.is_dir():
        return

    contact, credential = private_values()
    secrets = (contact, credential)

    public_svg = PUBLIC_DIR / "nreip2027_resume_public.svg"

    if public_svg.is_file():
        svg_text = public_svg.read_text(encoding="utf-8")
        for secret in secrets:
            if secret in svg_text:
                raise RuntimeError(
                    "private value leaked into public SVG."
                )

    public_pdf = PUBLIC_DIR / "nreip2027_resume_public.pdf"
    if public_pdf.is_file():
        extracted = extract_text(public_pdf)
        for secret in secrets:
            if norm(secret) in norm(extracted):
                raise RuntimeError(
                    "private value leaked into public PDF."
                )

def build(mode: str) -> None:
    verify_locked_sources()

    for command in (
        "fc-match",
        "inkscape",
        "gs",
        "pdfinfo",
        "pdftotext",
        "pdftoppm",
    ):
        require_command(command)

    if mode == "public":
        out_dir = PUBLIC_DIR
        contact = PUBLIC_CONTACT
        credential = PUBLIC_CREDENTIAL
        svg_name = "nreip2027_resume_public.svg"
        pdf_name = "nreip2027_resume_public.pdf"
    else:
        out_dir = PRIVATE_DIR
        contact, credential = private_values()
        svg_name = "nreip2027_resume.svg"
        pdf_name = "nreip2027_resume.pdf"

    cleanup_dir(out_dir)

    page = build_page(contact, credential)

    svg_path = out_dir / svg_name
    final_pdf = out_dir / pdf_name

    svg_path.write_text(svg(page), encoding="utf-8")

    render_svg_to_pdf(svg_path, final_pdf)

    validate_pdf(
        final_pdf,
        private=(mode == "private"),
    )

    poppler_pages = render_poppler(final_pdf, out_dir)

    target_page1 = out_dir / "page1.png"
    poppler_pages[0].replace(target_page1)

    with tempfile.TemporaryDirectory(prefix="nreip_resume_") as temp:
        temp_dir = Path(temp)
        gs_pages = render_ghostscript(final_pdf, temp_dir)

        check_renderer_dimensions(
            [target_page1],
            gs_pages,
        )

    if mode == "private":
        scan_public_for_private_values()

        public_width = measure(
            PUBLIC_CREDENTIAL,
            9.0,
            "bold",
        )
        private_width = measure(
            credential,
            9.0,
            "bold",
        )
        width_delta = abs(public_width - private_width)

        print(
            "private/public credential-width delta: "
            f"{width_delta:.1f} pt"
        )

    print(f"{mode.upper()}_BUILD_OK")
    print(f"page final y: {page.y:.1f} pt")
    print(f"bottom reserve: {PAGE_H - BOTTOM - page.y:.1f} pt")
    print(f"PDF size: {final_pdf.stat().st_size} bytes")
    print("secondary Ghostscript render: PASS")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        required=True,
        choices=("public", "private"),
    )
    args = parser.parse_args()
    build(args.mode)


if __name__ == "__main__":
    main()
