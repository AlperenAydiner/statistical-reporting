"""Shared result types every analysis function returns.

A ``manifest.json`` (a list of serialized ``AnalysisResult``s) is the single
intermediate the whole pipeline is built around: every number is computed
here, once, and frozen. Rendering (Markdown → pandoc → docx post-process)
never recomputes a statistic — it only formats and lays out what is already
in the manifest. This is also the anti-hallucination boundary: any narrative
text a model writes may only cite numbers that already appear in ``stats``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class TableSpec:
    id: str
    caption: str  # already localized, e.g. "Table 1. Descriptive Statistics"
    headers: list[str]  # already localized column headers
    rows: list[list[str]]  # already formatted cell strings
    numeric_columns: list[int] = field(default_factory=list)  # indices for right/decimal alignment
    note: str | None = None  # already localized "Note. ..." footer
    merged_header_spans: list[tuple[int, int, str]] = field(default_factory=list)
    """Optional (col_start, col_end, label) spans for a merged super-header
    row (e.g. APA hierarchical regression, SPSS pivot style). Applied by
    docx/postprocess.py — pandoc's docx writer cannot emit merged cells."""


@dataclass
class FigureRef:
    id: str
    path: str
    caption: str  # already localized


@dataclass
class AnalysisResult:
    id: str
    heading: str  # already localized section heading
    tables: list[TableSpec] = field(default_factory=list)
    figures: list[FigureRef] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)  # the number whitelist for narrative checks
    auto_prose: str = ""  # deterministic, always-correct sentence(s)
    spss_syntax: str | None = None
    assumption_notes: list[str] = field(default_factory=list)
    method_switched: str | None = None  # e.g. "t-test -> Mann-Whitney U (normality failed)"

    def to_dict(self) -> dict:
        return asdict(self)
