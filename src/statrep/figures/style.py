"""Shared figure styling — the single source of truth for how statrep
figures look. Migrated from `statistical-analysis/SKILL.md`'s inline
`init_figure()`; `visualization-builder/scripts/chart_builder.py` keeps its
own `CHART_RULES` chart-*selection* logic and imports this module for
*rendering* rather than duplicating a second matplotlib convention.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # headless: no display server needed

import matplotlib.pyplot as plt
import seaborn as sns

# Qualitative palette shared by every plot function in this package.
PALETTE = {
    "primary": "#4C72B0",
    "secondary": "#DD8452",
    "positive": "#C44E52",
    "negative": "#4C72B0",
    "tertiary": "#55A868",
}

DPI = 300


def init_figure(figsize: tuple[float, float] = (10, 6)):
    """Unified figure initialization: Turkish/Latin-safe fonts + APA-ish style.

    No system font hunting: DejaVu Sans ships with matplotlib and fully
    covers Turkish diacritics (ş ğ ı ö ç ü), so it is set explicitly rather
    than left to fallback.
    """
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.dpi"] = DPI
    plt.rcParams["savefig.dpi"] = DPI
    plt.rcParams["savefig.bbox"] = "tight"
    sns.set_style("white")
    sns.set_context("paper", font_scale=1.2)
    fig, ax = plt.subplots(figsize=figsize)
    return fig, ax


def significance_star(p: float) -> str:
    """APA-style significance star for a p-value."""
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return ""
