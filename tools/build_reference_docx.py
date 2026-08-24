#!/usr/bin/env python3
"""Generate statrep's pandoc reference.docx templates.

These files are committed as binaries (``src/statrep/render/reference/*.docx``)
so `setup.sh` doesn't need to run this script — but this script is what
produced them, and is how you regenerate them after a design change.

Starts from pandoc's own default reference.docx (which already carries
correct ``w:outlineLvl`` on every heading style — verified in the M0.5
spike, nothing to add there) and only touches fonts/alignment.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pypandoc
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.shared import Pt

OUT_DIR = Path(__file__).parent.parent / "src" / "statrep" / "render" / "reference"

# Turkish diacritics (ş ğ ı ö ç ü) need full Latin coverage; Liberation
# Serif/Sans are metric-compatible with Times New Roman/Arial so a Word
# document built on Linux still measures correctly once opened with the
# real fonts on Windows/Mac.
BODY_FONT = "Liberation Serif"
SANS_FONT = "Liberation Sans"


def _set_font(style, name: str, size_pt: float, bold: bool = False, italic: bool = False) -> None:
    style.font.name = name
    style.font.size = Pt(size_pt)
    style.font.bold = bold
    style.font.italic = italic
    r_pr = style.element.get_or_add_rPr()
    r_fonts = r_pr.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rFonts")
    if r_fonts is None:
        r_fonts = OxmlElement("w:rFonts")
        r_pr.append(r_fonts)
    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    for attr in ("ascii", "hAnsi", "cs"):
        r_fonts.set(f"{ns}{attr}", name)
    # Explicitly clear eastAsia so no CJK font ever gets inherited here.
    r_fonts.set(f"{ns}eastAsia", name)


def _set_1inch_margins(doc: Document) -> None:
    """Set 1" margins on every section. Also explicitly sets header/footer
    distance and gutter — python-docx's margin setters rewrite ``w:pgMar``
    from scratch and silently drop those three attributes if they weren't
    already present, which fails strict ISO-29500 XSD validation even
    though Word itself opens the file fine either way. Caught by running
    the bundled docx skill's validator against real output — worth setting
    explicitly rather than relying on Word's tolerance."""
    for sec in doc.sections:
        sec.left_margin = sec.right_margin = sec.top_margin = sec.bottom_margin = Pt(72)
        sec.header_distance = Pt(36)
        sec.footer_distance = Pt(36)
        sec.gutter = Pt(0)


def _extract_pandoc_default(dest: Path) -> None:
    pandoc_path = pypandoc.get_pandoc_path()
    subprocess.run(
        [pandoc_path, "-o", str(dest), "--print-default-data-file=reference.docx"],
        check=True,
        stdout=subprocess.DEVNULL,
    )


def build_academic(dest: Path) -> None:
    _extract_pandoc_default(dest)
    doc = Document(dest)

    _set_font(doc.styles["Normal"], BODY_FONT, 12)
    doc.styles["Normal"].paragraph_format.line_spacing = 2.0  # APA 7: double-spaced body

    _set_font(doc.styles["Title"], BODY_FONT, 16, bold=True)
    doc.styles["Title"].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # APA 7 heading levels: L1 centered bold, L2 flush-left bold,
    # L3 flush-left bold italic, L4+ inherits L3 (run-in headings are a
    # docx/postprocess.py concern, not a paragraph style concern).
    _set_font(doc.styles["Heading 1"], BODY_FONT, 14, bold=True)
    doc.styles["Heading 1"].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_font(doc.styles["Heading 2"], BODY_FONT, 12, bold=True)
    doc.styles["Heading 2"].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    _set_font(doc.styles["Heading 3"], BODY_FONT, 12, bold=True, italic=True)
    doc.styles["Heading 3"].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT

    _set_1inch_margins(doc)
    doc.save(dest)


def build_business(dest: Path) -> None:
    _extract_pandoc_default(dest)
    doc = Document(dest)

    _set_font(doc.styles["Normal"], SANS_FONT, 11)

    _set_font(doc.styles["Title"], SANS_FONT, 24, bold=True)
    doc.styles["Title"].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT

    _set_font(doc.styles["Heading 1"], SANS_FONT, 16, bold=True)
    doc.styles["Heading 1"].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    _set_font(doc.styles["Heading 2"], SANS_FONT, 13, bold=True)
    _set_font(doc.styles["Heading 3"], SANS_FONT, 11, bold=True)

    doc.save(dest)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    build_academic(OUT_DIR / "academic-apa7.docx")
    build_business(OUT_DIR / "business.docx")
    print(f"Wrote {OUT_DIR / 'academic-apa7.docx'}")
    print(f"Wrote {OUT_DIR / 'business.docx'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
