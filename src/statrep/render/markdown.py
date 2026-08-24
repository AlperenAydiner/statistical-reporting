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

from statrep.analysis.results import AnalysisResult, TableSpec


@dataclass
class ReportMeta:
    title: str
    subtitle: str
    date: str
    lang: str  # "tr" | "en"
    author: str | None = None


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


def _render_result(result: AnalysisResult) -> str:
    parts = [f"# {result.heading}", ""]
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


def render_markdown(meta: ReportMeta, results: list[AnalysisResult]) -> str:
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

    body = "\n\n".join(_render_result(r) for r in results)
    return "\n".join(frontmatter_lines) + "\n" + body + "\n"
