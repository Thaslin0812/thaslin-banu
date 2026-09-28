"""Formatting utilities: sanitize_text, format_docx, format_pdf, format_html_preview."""
import html
import io
import os
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont

import config

_REPLACEMENTS = {
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u2013": "-", "\u2014": "-", "\u2026": "...", "\u00a0": " ", "\u2022": "-",
}


def ensure_logo(path=config.LOGO_PATH, dark=False):
    """Create a simple placeholder logo if none exists (replace with your own PNG)."""
    if os.path.exists(path):
        return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fg, bg = ((255, 255, 255, 255), (0, 0, 0, 0)) if dark else ((20, 20, 20, 255), (255, 255, 255, 0))
    img = Image.new("RGBA", (520, 120), bg)
    try:
        font = ImageFont.load_default(size=64)
    except TypeError:
        font = ImageFont.load_default()
    ImageDraw.Draw(img).text((20, 25), "LegalEase", fill=fg, font=font)
    img.save(path)
    return path


def sanitize_text(text):
    for k, v in _REPLACEMENTS.items():
        text = text.replace(k, v)
    text = text.replace("\r\n", "\n")
    text = re.sub(r"(?m)^\s*\*\s+", "- ", text)      # markdown bullets -> "- "
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)     # strip bold markers
    return text.strip()


def parse_blocks(text):
    """Return list of (kind, text); kind in title/heading/bullet/para."""
    blocks = []
    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            kind = "title" if not blocks else "heading"
            blocks.append((kind, line.lstrip("#").strip()))
        elif re.match(r"^-\s+", line):
            blocks.append(("bullet", line[1:].strip()))
        elif (re.match(r"^\d+\.\s+\S", line) and len(line) < 80 and not line.endswith(".")) \
                or (line.endswith(":") and len(line) < 60) \
                or (line.isupper() and len(line) < 80):
            blocks.append(("heading", line))
        else:
            blocks.append(("para", line))
    return blocks


def _split_terms(terms):
    return [t.strip() for t in (terms or "").split(";") if t.strip()]


# ---------- DOCX ----------
def format_docx(text, doc_type, terms=""):
    doc = Document()
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    normal.element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), "Times New Roman")

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(ensure_logo(), width=Inches(2.2))

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run(doc_type)
    run.bold = True
    run.font.size = Pt(16)

    for kind, content in parse_blocks(sanitize_text(text)):
        if kind == "title":
            continue
        if kind == "heading":
            doc.add_paragraph().add_run(content).bold = True
        elif kind == "bullet":
            doc.add_paragraph(content, style="List Bullet")
        else:
            doc.add_paragraph(content)

    items = _split_terms(terms)
    if items:
        doc.add_paragraph().add_run("Summary of Key Terms").bold = True
        table = doc.add_table(rows=1, cols=2)
        table.style = "Table Grid"
        table.rows[0].cells[0].text, table.rows[0].cells[1].text = "No.", "Term"
        for i, item in enumerate(items, 1):
            row = table.add_row().cells
            row[0].text, row[1].text = str(i), item

    footer = doc.sections[0].footer.paragraphs[0]
    footer.text = config.FOOTER_TEXT
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ---------- PDF ----------
def _latin(s):
    return s.encode("latin-1", "replace").decode("latin-1")


class _LegalPDF(FPDF):
    def header(self):
        logo = ensure_logo()
        with Image.open(logo) as im:
            w = 38
            h = w * im.height / im.width
        self.image(logo, x=(self.w - w) / 2, y=8, w=w)
        self.set_y(8 + h + 4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Times", "I", 8)
        self.cell(0, 10, _latin(f"{config.FOOTER_TEXT}   Page {self.page_no()}"), align="C")


def format_pdf(text, doc_type, terms=""):
    pdf = _LegalPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    pdf.set_font("Times", "B", 16)
    pdf.cell(0, 10, _latin(doc_type), align="C")
    pdf.ln(12)

    for kind, content in parse_blocks(sanitize_text(text)):
        if kind == "title":
            continue
        pdf.set_x(pdf.l_margin)
        if kind == "heading":
            pdf.ln(2)
            pdf.set_font("Times", "B", 12)
            pdf.multi_cell(0, 7, _latin(content))
        elif kind == "bullet":
            pdf.set_font("Times", "", 12)
            pdf.set_x(pdf.l_margin + 6)
            pdf.multi_cell(0, 6, _latin("- " + content))
        else:
            pdf.set_font("Times", "", 12)
            pdf.multi_cell(0, 6, _latin(content))
        pdf.ln(1)

    items = _split_terms(terms)
    if items:
        pdf.ln(3)
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Times", "B", 12)
        pdf.multi_cell(0, 7, "Summary of Key Terms")
        pdf.set_font("Times", "", 12)
        for item in items:
            pdf.set_x(pdf.l_margin + 6)
            pdf.multi_cell(0, 6, _latin("- " + item))

    out = pdf.output(dest="S")
    return out.encode("latin-1") if isinstance(out, str) else bytes(out)


# ---------- HTML preview ----------
def format_html_preview(text):
    parts = []
    for kind, content in parse_blocks(sanitize_text(text)):
        c = html.escape(content)
        if kind == "title":
            parts.append(f"<h2 style='text-align:center'>{c}</h2>")
        elif kind == "heading":
            parts.append(f"<h4 style='margin:14px 0 4px'>{c}</h4>")
        elif kind == "bullet":
            parts.append(f"<div style='margin-left:18px'>&bull; {c}</div>")
        else:
            parts.append(f"<p style='margin:4px 0'>{c}</p>")
    return "\n".join(parts)
