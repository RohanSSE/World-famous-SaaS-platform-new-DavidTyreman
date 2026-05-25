"""
Premium styled brand deliverables — cover, hierarchy, DNA map (ReportLab).
"""
from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List, Tuple

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .brand_export_engine import _build_sections, _escape, _text_from_section

NAVY = colors.HexColor("#0a1727")
CYAN = colors.HexColor("#4fe5ff")
CYAN_DIM = colors.HexColor("#19869a")
SLATE = colors.HexColor("#b1b8c4")
WHITE = colors.white
ACCENT = colors.HexColor("#8b5cf6")


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(SLATE)
    canvas.drawString(50, 28, "GodFather — Enterprise Brand Intelligence")
    canvas.drawRightString(A4[0] - 50, 28, f"Page {doc.page}")
    canvas.restoreState()


def _cover_page(canvas, doc, title: str, client_name: str):
    w, h = A4
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, w, h, fill=True, stroke=False)
    canvas.setFillColor(CYAN)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(50, h - 60, "BRAND OPERATING SYSTEM")
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 28)
    canvas.drawString(50, h - 120, title[:60])
    canvas.setFont("Helvetica", 14)
    canvas.setFillColor(SLATE)
    canvas.drawString(50, h - 155, client_name[:80])
    canvas.setFillColor(CYAN_DIM)
    canvas.rect(50, 80, w - 100, 3, fill=True, stroke=False)
    canvas.setFillColor(SLATE)
    canvas.setFont("Helvetica", 9)
    canvas.drawString(50, 55, "Evidence-grounded strategic brand cognition")
    canvas.restoreState()


def _dna_map_table(package: Dict[str, Any]) -> Table | None:
    dna = package.get("brand_dna") or {}
    rows = [["Pillar", "Signal"]]
    if isinstance(dna, dict):
        for k, v in list(dna.items())[:8]:
            if k == "narrative":
                continue
            rows.append([k.replace("_", " ").title(), str(v)[:120]])
    if len(rows) < 2:
        return None
    t = Table(rows, colWidths=[2.2 * inch, 4.3 * inch])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f4f7fb"), WHITE]),
                ("GRID", (0, 0), (-1, -1), 0.25, SLATE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return t


def render_premium_brand_pdf(
    title: str,
    package: Dict[str, Any],
    narrative: str = "",
    client_name: str = "Confidential Client",
    brand_colors: Dict[str, str] | None = None,
) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=54,
        leftMargin=54,
        topMargin=72,
        bottomMargin=54,
    )
    styles = getSampleStyleSheet()
    toc_style = ParagraphStyle("TOC", parent=styles["Normal"], fontSize=10, textColor=NAVY)
    h2 = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontSize=16,
        textColor=NAVY,
        spaceBefore=20,
        spaceAfter=10,
        borderPadding=4,
    )
    body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10.5, leading=15, alignment=TA_LEFT)
    lead = ParagraphStyle("Lead", parent=body, fontSize=11, textColor=CYAN_DIM, spaceAfter=12)

    story: List[Any] = []
    story.append(PageBreak())  # cover drawn via onFirstPage

    story.append(Paragraph("Contents", h2))
    sections = _build_sections(package, narrative)
    for i, (heading, _) in enumerate(sections, 1):
        story.append(Paragraph(f"{i}. {_escape(heading)}", toc_style))
    story.append(Spacer(1, 0.3 * inch))

    dna_table = _dna_map_table(package)
    if dna_table:
        story.append(Paragraph("Brand DNA Map", h2))
        story.append(dna_table)
        story.append(Spacer(1, 0.2 * inch))

    for heading, text in sections:
        story.append(HRFlowable(width="100%", thickness=1, color=CYAN, spaceBefore=8, spaceAfter=8))
        story.append(Paragraph(_escape(heading), h2))
        first = True
        for para in text.split("\n\n"):
            para = para.strip()
            if not para:
                continue
            style = lead if first else body
            story.append(Paragraph(_escape(para.replace("\n", "<br/>")), style))
            first = False
        story.append(Spacer(1, 0.12 * inch))

    def _first(c, d):
        _cover_page(c, d, title, client_name)
        _footer(c, d)

    doc.build(story, onFirstPage=_first, onLaterPages=_footer)
    return buffer.getvalue()
