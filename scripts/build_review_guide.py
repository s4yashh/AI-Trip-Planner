"""Build the review PDF from its editable Markdown source.

Documentation-only dependency: reportlab. Run from any working directory.
Supports the deliberately small Markdown subset used in REVIEW_GUIDE.md.
"""
from pathlib import Path
import argparse
import re
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]


def font_names():
    """Use an embedded readable font when available, with portable PDF fallback."""
    windows = Path("C:/Windows/Fonts")
    if all((windows / name).exists() for name in ("arial.ttf", "arialbd.ttf", "ariali.ttf", "arialbi.ttf")):
        for name, file in (("Guide", "arial.ttf"), ("Guide-Bold", "arialbd.ttf"),
                           ("Guide-Italic", "ariali.ttf"), ("Guide-BoldItalic", "arialbi.ttf")):
            pdfmetrics.registerFont(TTFont(name, str(windows / file)))
        pdfmetrics.registerFontFamily("Guide", normal="Guide", bold="Guide-Bold", italic="Guide-Italic", boldItalic="Guide-BoldItalic")
        return "Guide", "Guide-Bold"
    return "Helvetica", "Helvetica-Bold"


def inline(text):
    text = escape(text)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", r'<link href="\2" color="#234b68"><u>\1</u></link>', text)
    text = re.sub(r"`([^`]+)`", r'<font name="Courier" size="9">\1</font>', text)
    return re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)


def build(source, output):
    normal, bold = font_names()
    styles = {
        "body": ParagraphStyle("Body", fontName=normal, fontSize=10.3, leading=13.5, spaceAfter=6,
                               textColor=colors.HexColor("#20252b"), splitLongWords=True),
        "title": ParagraphStyle("Title", fontName=bold, fontSize=26, leading=31, spaceAfter=19,
                                textColor=colors.black, keepWithNext=True),
        "h2": ParagraphStyle("Heading2", fontName=bold, fontSize=19, leading=23, spaceAfter=12,
                             textColor=colors.black, keepWithNext=True),
        "h3": ParagraphStyle("Heading3", fontName=bold, fontSize=11.5, leading=15, spaceBefore=7,
                             spaceAfter=5, textColor=colors.black, keepWithNext=True),
        "cell": ParagraphStyle("TableBody", fontName=normal, fontSize=9.2, leading=12.5,
                               textColor=colors.HexColor("#20252b"), splitLongWords=True),
        "th": ParagraphStyle("TableHeader", fontName=bold, fontSize=9.2, leading=12.5, textColor=colors.white),
        "bullet": ParagraphStyle("Bullet", fontName=normal, fontSize=10.3, leading=14.1, leftIndent=11,
                                 firstLineIndent=-9, spaceAfter=6, textColor=colors.HexColor("#20252b")),
    }
    story = []
    lines = source.read_text(encoding="utf-8").splitlines()
    width = A4[0] - 40 * mm
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line:
            continue
        if line == "<!-- pagebreak -->":
            story.append(PageBreak())
        elif line.startswith("|"):
            rows = [line]
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip())
                i += 1
            cells = [[c.strip() for c in row.strip("|").split("|")] for row in rows]
            cells = [row for row in cells if not all(re.fullmatch(r":?-+:?", c) for c in row)]
            count = len(cells[0])
            first = cells[0][0]
            if first == "Segment":
                ratios = [.25, .17, .16, .42]
            elif first == "Step":
                ratios = [.09, .17, .37, .37]
            elif first == "Review area":
                ratios = [.19, .16, .34, .31]
            elif first == "Category":
                ratios = [.27, .24, .24, .25]
            elif first == "Evidence":
                ratios = [.27, .57, .16]
            else:
                ratios = [.25, .39, .36] if count == 3 else [1/count]*count
            data = [[Paragraph(inline(c), styles["th" if r == 0 else "cell"]) for c in row] for r, row in enumerate(cells)]
            table = Table(data, colWidths=[r*width for r in ratios], repeatRows=1, hAlign="LEFT")
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#263e51")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f4f6")]),
                ("GRID", (0, 0), (-1, -1), .5, colors.HexColor("#D9D9D9")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.extend([table, Spacer(1, 10)])
        elif line.startswith("# "):
            story.append(Paragraph(inline(line[2:]), styles["title"]))
        elif line.startswith("## "):
            story.append(Paragraph(inline(line[3:]), styles["h2"]))
        elif line.startswith("### "):
            story.append(Paragraph(inline(line[4:]), styles["h3"]))
        elif line.startswith("- "):
            story.append(Paragraph("- " + inline(line[2:]), styles["bullet"]))
        else:
            paragraph = [line]
            while i < len(lines) and lines[i].strip() and not lines[i].startswith(("#", "|", "- ", "<!--")):
                paragraph.append(lines[i].strip())
                i += 1
            story.append(Paragraph(inline(" ".join(paragraph)), styles["body"]))

    def page_furniture(canvas, doc):
        canvas.saveState()
        if doc.page > 1:
            canvas.setFont(normal, 8)
            canvas.setFillColor(colors.black)
            canvas.drawString(20*mm, A4[1]-14*mm, "AI Trip Planner Review Guide")
        canvas.setFont(normal, 8)
        canvas.setFillColor(colors.HexColor("#58616a"))
        canvas.drawString(20*mm, 13*mm, "Review baseline bf85fdd   |   23 September 2026")
        canvas.drawRightString(A4[0]-20*mm, 13*mm, str(doc.page))
        canvas.restoreState()

    output.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(output), pagesize=A4, leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=22*mm, bottomMargin=22*mm,
                            title="AI Trip Planner Review Guide", author="AI Trip Planner project",
                            subject="Reviewer guide, two presenter scripts, demonstration and follow up questions",
                            creator="AI Trip Planner review guide builder")
    doc.build(story, onFirstPage=page_furniture, onLaterPages=page_furniture)
    print(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "docs/review/REVIEW_GUIDE.md")
    parser.add_argument("--output", type=Path, default=ROOT / "output/pdf/AI_Trip_Planner_Review_Guide.pdf")
    args = parser.parse_args()
    build(args.source, args.output)
