"""Render a list of ``AnalysisResult``s into a single pandoc-flavoured
Markdown document — the input to the pandoc conversion pass.

Table syntax: a ``: Caption`` line immediately before a pipe table makes
pandoc attach it as that table's caption (verified in the M0.5 spike: this
round-trips through docx with headers, decimal-comma content, and italic
markup intact).

Figure syntax: an image alone in its own paragraph (``![caption](path)``)
is pandoc's "implicit figure" — the docx writer renders it as an embedded
image followed by a centered caption paragraph.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from statrep.analysis.results import AnalysisResult, TableSpec

if TYPE_CHECKING:
    from statrep.report.narrative import ReportNarrative


@dataclass
class ReportMeta:
    title: str
    subtitle: str
    date: str
    lang: str  # "tr" | "en"
    author: str | None = None


def _page_break() -> str:
    return '\n```{=openxml}\n<w:p><w:r><w:br w:type="page"/></w:r></w:p>\n```\n\n<div style="page-break-before: always;"></div>\n\n'


def _render_table(table: TableSpec) -> str:
    lines = [f": {table.caption}", ""]
    lines.append("| " + " | ".join(table.headers) + " |")
    aligns = [
        ("---:" if i in table.numeric_columns else "---")
        for i in range(len(table.headers))
    ]
    lines.append("|" + "|".join(aligns) + "|")
    for row in table.rows:
        # Escape pipe characters in cell content so they don't break the table grid.
        safe_row = [str(cell).replace("|", "\\|") for cell in row]
        lines.append("| " + " | ".join(safe_row) + " |")
    lines.append("")
    if table.note:
        lines.append(f"*{table.note}*")
        lines.append("")
    return "\n".join(lines)


def _render_result(result: AnalysisResult, section_num: int | None = None) -> str:
    prefix = f"{section_num}. " if section_num is not None else ""
    parts = [f"# {prefix}{result.heading}", ""]
    if result.auto_prose:
        parts.append(result.auto_prose)
        parts.append("")
    for table in result.tables:
        parts.append(_render_table(table))
    for fig in result.figures:
        parts.append(f"![{fig.caption}]({fig.path})")
        parts.append("")
    if result.assumption_notes:
        for note in result.assumption_notes:
            parts.append(f"> {note}")
        parts.append("")
    return "\n".join(parts)


def render_markdown(
    meta: ReportMeta,
    results: list[AnalysisResult],
    narrative: ReportNarrative | None = None,
) -> str:
    lang_tag = "tr-TR" if meta.lang == "tr" else "en-US"
    frontmatter_lines = [
        "---",
        f'title: "{meta.title}"',
        f'subtitle: "{meta.subtitle}"',
        f"lang: {lang_tag}",
        f'date: "{meta.date}"',
    ]
    if meta.author:
        frontmatter_lines.append(f'author: "{meta.author}"')
    frontmatter_lines += ["---", ""]

    if narrative is None:
        body = "\n\n".join(_render_result(r) for r in results)
        return "\n".join(frontmatter_lines) + "\n" + body + "\n"

    # Full institutional report structure matching the sample format
    sections: list[str] = []

    # 1. Giriş / Introduction
    sec1_title = "1. Giriş" if meta.lang == "tr" else "1. Introduction"
    sections.append(f"# {sec1_title}\n\n{narrative.introduction}")

    # 2. Çalışmanın Amacı / Purpose
    sec2_title = "2. Çalışmanın Amacı" if meta.lang == "tr" else "2. Purpose of the Study"
    sections.append(f"# {sec2_title}\n\n{narrative.purpose}")

    # 3. Veri Setinin Tanıtımı / Dataset Overview
    sec3_title = "3. Veri Setinin Tanıtımı" if meta.lang == "tr" else "3. Dataset Overview"
    sections.append(f"# {sec3_title}\n\n{narrative.dataset_overview}\n\n{_render_table(narrative.dataset_table)}")

    # 4. Veri Hazırlama Süreci / Data Preparation Process
    sec4_title = "4. Veri Hazırlama Süreci" if meta.lang == "tr" else "4. Data Preparation Process"
    sections.append(f"# {sec4_title}\n\n{narrative.data_prep}")

    # 5..N Analiz Bölümleri
    current_sec = 5
    for r in results:
        sections.append(_render_result(r, section_num=current_sec))
        current_sec += 1

    # N+1 Sonuç ve Öneriler / Conclusions and Recommendations
    sec_concl_title = f"{current_sec}. Sonuç ve Öneriler" if meta.lang == "tr" else f"{current_sec}. Conclusions and Recommendations"
    sections.append(f"# {sec_concl_title}\n\n{narrative.conclusion}")
    current_sec += 1

    # N+2 Ekler / Appendices
    sec_app_title = f"{current_sec}. Ekler" if meta.lang == "tr" else f"{current_sec}. Appendices"
    sections.append(f"# {sec_app_title}\n\n{_render_table(narrative.appendix_table)}")

    pb = _page_break()
    body = pb.join(sections)
    return "\n".join(frontmatter_lines) + "\n" + body + "\n"

