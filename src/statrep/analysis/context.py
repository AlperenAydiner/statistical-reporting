"""Shared, mutable state threaded through every analysis function: the
translator, number formatter, output directory for figures, and the
running Table/Figure counters (report-wide, so "Table 4" always means the
same table whether it's cited from prose, an appendix, or the .sps file)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from statrep.i18n import Translator
from statrep.tables.apa import NumberFormatter


@dataclass
class AnalysisContext:
    t: Translator
    fmt: NumberFormatter
    figures_dir: Path
    table_n: int = 0
    figure_n: int = 0

    def next_table(self) -> int:
        self.table_n += 1
        return self.table_n

    def next_figure(self) -> int:
        self.figure_n += 1
        return self.figure_n


def make_context(lang: str, figures_dir: Path) -> AnalysisContext:
    figures_dir.mkdir(parents=True, exist_ok=True)
    return AnalysisContext(t=Translator(lang), fmt=NumberFormatter(lang), figures_dir=figures_dir)
