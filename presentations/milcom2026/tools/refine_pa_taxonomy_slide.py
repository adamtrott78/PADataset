#!/usr/bin/env python3
"""Apply the locked MILCOM presentation revision to the PA-taxonomy slide.

This is a deterministic SVG post-processing step.  It intentionally edits the
vector slide source rather than a rendered slide image.
"""
from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SLIDE = ROOT / "slides" / "slide03_pa_taxonomy.svg"

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
Q = lambda tag: f"{{{SVG_NS}}}{tag}"

INK = "#102235"
SECOND = "#5D6C7B"
BORDER = "#D8E1EA"
PANEL = "#EEF3F7"
FONT = "Arial, Helvetica, sans-serif"

TITLE = "Preliminary Actions turn RF observations into precursor evidence"
TAXONOMY = (
    "RESEARCH TAXONOMY  ·  abstraction of precursor-level RF behavior, "
    "not a standardized attack ontology"
)


def remove_by_id(root: ET.Element, element_id: str) -> None:
    for parent in root.iter():
        for child in list(parent):
            if child.attrib.get("id") == element_id:
                parent.remove(child)
                return


def add_text(
    parent: ET.Element,
    *,
    element_id: str,
    x: float,
    y: float,
    text: str,
    size: int,
    bold: bool = False,
    color: str = INK,
    anchor: str = "start",
) -> ET.Element:
    node = ET.SubElement(
        parent,
        Q("text"),
        {
            "id": element_id,
            "x": str(x),
            "y": str(y),
            "font-family": FONT,
            "font-size": str(size),
            "font-weight": "700" if bold else "400",
            "fill": color,
            "text-anchor": anchor,
        },
    )
    span = ET.SubElement(node, Q("tspan"), {"x": str(x), "y": str(y)})
    span.text = text
    return node


def add_multiline_centered(
    parent: ET.Element,
    *,
    element_id: str,
    x: float,
    lines: list[str],
    baselines: list[float],
    size: int,
) -> None:
    node = ET.SubElement(
        parent,
        Q("text"),
        {
            "id": element_id,
            "x": str(x),
            "font-family": FONT,
            "font-size": str(size),
            "font-weight": "700",
            "fill": INK,
            "text-anchor": "middle",
        },
    )
    for line, y in zip(lines, baselines):
        span = ET.SubElement(node, Q("tspan"), {"x": str(x), "y": str(y)})
        span.text = line


def add_round_rect(parent: ET.Element, element_id: str, x: int, y: int, w: int, h: int) -> None:
    ET.SubElement(
        parent,
        Q("rect"),
        {
            "id": element_id,
            "x": str(x),
            "y": str(y),
            "width": str(w),
            "height": str(h),
            "rx": "16",
            "fill": PANEL,
            "stroke": BORDER,
            "stroke-width": "2",
        },
    )


def add_arrow(parent: ET.Element, element_id: str, x1: int, x2: int, y: int) -> None:
    # Explicit shaft + polygon head: geometric arrow, not text punctuation.
    head = 15
    base = x2 - head
    ET.SubElement(
        parent,
        Q("line"),
        {
            "id": element_id + "_shaft",
            "x1": str(x1),
            "y1": str(y),
            "x2": str(base),
            "y2": str(y),
            "stroke": SECOND,
            "stroke-width": "6",
            "stroke-linecap": "round",
        },
    )
    ET.SubElement(
        parent,
        Q("polygon"),
        {
            "id": element_id + "_head",
            "points": f"{base},{y-11} {base},{y+11} {x2},{y}",
            "fill": SECOND,
        },
    )


def rewrite_pretemplate_title(root: ET.Element) -> None:
    title = root.find(Q("title"))
    if title is None:
        raise RuntimeError("PA-taxonomy SVG is missing its <title> element")
    title.text = TITLE

    group = next((e for e in root.iter() if e.attrib.get("id") == "title_group"), None)
    if group is None:
        raise RuntimeError("PA-taxonomy SVG is missing title_group")
    for child in list(group):
        group.remove(child)
    add_text(
        group,
        element_id="title_revised",
        x=96,
        y=116,
        text=TITLE,
        size=52,
        bold=True,
    )


def main() -> None:
    if not SLIDE.exists():
        raise FileNotFoundError(SLIDE)

    tree = ET.parse(SLIDE)
    root = tree.getroot()

    rewrite_pretemplate_title(root)

    # Remove redundant explanatory material from the old composition.
    for element_id in (
        "supporting_sentence",
        "research_taxonomy_group",
        "tells_us_box",
        "does_not_claim_box",
        "optional_protocol_footer",
        "pa_evidence_flow_group",
    ):
        remove_by_id(root, element_id)

    # What PAs are: an explicit research abstraction, not a standards claim.
    taxonomy = ET.SubElement(root, Q("g"), {"id": "research_taxonomy_group"})
    ET.SubElement(
        taxonomy,
        Q("rect"),
        {
            "id": "research_taxonomy_box",
            "x": "180",
            "y": "164",
            "width": "1560",
            "height": "58",
            "rx": "14",
            "fill": PANEL,
            "stroke": BORDER,
            "stroke-width": "2",
        },
    )
    add_text(
        taxonomy,
        element_id="research_taxonomy_text",
        x=960,
        y=201,
        text=TAXONOMY,
        size=24,
        bold=True,
        color=SECOND,
        anchor="middle",
    )

    # What PAs do: RF observation -> PA evidence -> downstream reasoning.
    flow = ET.SubElement(root, Q("g"), {"id": "pa_evidence_flow_group"})
    box_y, box_h = 840, 105

    add_round_rect(flow, "rf_observation_box", 230, box_y, 430, box_h)
    add_text(
        flow,
        element_id="rf_observation_text",
        x=445,
        y=905,
        text="RF observation",
        size=28,
        bold=True,
        anchor="middle",
    )

    add_round_rect(flow, "pa_evidence_box", 730, box_y, 460, box_h)
    add_text(
        flow,
        element_id="pa_evidence_text",
        x=960,
        y=905,
        text="Preliminary-Action evidence",
        size=26,
        bold=True,
        anchor="middle",
    )

    add_round_rect(flow, "downstream_reasoning_box", 1260, box_y, 430, box_h)
    add_multiline_centered(
        flow,
        element_id="downstream_reasoning_text",
        x=1475,
        lines=["downstream cyber / EW /", "CWoS reasoning"],
        baselines=[890, 920],
        size=22,
    )

    add_arrow(flow, "arrow_rf_to_pa", 680, 710, 892)
    add_arrow(flow, "arrow_pa_to_downstream", 1210, 1240, 892)

    # Basic structural validation before the normal template integration step.
    ids = [e.attrib["id"] for e in root.iter() if "id" in e.attrib]
    if len(ids) != len(set(ids)):
        raise RuntimeError("Duplicate SVG IDs after PA-taxonomy revision")
    if root.attrib.get("viewBox") != "0 0 1920 1080":
        raise RuntimeError(f"Unexpected SVG viewBox: {root.attrib.get('viewBox')!r}")

    tree.write(SLIDE, encoding="utf-8", xml_declaration=False)
    print(f"refined {SLIDE.name}")


if __name__ == "__main__":
    main()
