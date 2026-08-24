"""Pairwise Pearson correlation matrix: APA lower-triangle table + heatmap
figure + a plain-language summary of the strongest relationship."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

from statrep.figures.plots import plot_correlation_heatmap
from statrep.tables.apa import correlation_strength_key

from .context import AnalysisContext
from .results import AnalysisResult, FigureRef, TableSpec


def run_correlation_matrix(
    df: pd.DataFrame, variables: list[str], ctx: AnalysisContext
) -> AnalysisResult:
    t, fmt = ctx.t, ctx.fmt
    data = df[variables].dropna()
    n = len(data)

    corr = data.corr(method="pearson")
    p_matrix = pd.DataFrame(np.ones((len(variables), len(variables))), index=variables, columns=variables)
    pairs: list[tuple[str, str, float, float]] = []
    for i, a in enumerate(variables):
        for j, b in enumerate(variables):
            if i >= j:
                continue
            r, p = scipy_stats.pearsonr(data[a], data[b])
            p_matrix.loc[a, b] = p
            p_matrix.loc[b, a] = p
            pairs.append((a, b, float(r), float(p)))

    # Lower-triangle APA table.
    headers = [t("term.variable")] + [str(i + 1) for i in range(len(variables) - 1)]
    rows: list[list[str]] = []
    for i, a in enumerate(variables):
        row = [f"{i + 1}. {a}"]
        for j in range(len(variables) - 1):
            b = variables[j]
            if j >= i:
                row.append("")
            else:
                r = corr.loc[a, b]
                p = p_matrix.loc[a, b]
                star = "*" * sum(p < thr for thr in (0.05, 0.01, 0.001))
                row.append(f"{fmt.r(r)}{star}")
        rows.append(row)

    table = TableSpec(
        id="table_correlation",
        caption=t("table.correlation.caption", n=ctx.next_table()),
        headers=headers,
        rows=rows,
        numeric_columns=list(range(1, len(headers))),
        note=t("table.note.apa_stars"),
    )

    fig_path = plot_correlation_heatmap(
        corr, p_matrix, title=t("section.correlation"),
        save_path=ctx.figures_dir / "fig-correlation-heatmap.png",
    )
    figures = [FigureRef(
        id="fig_correlation_heatmap", path=str(fig_path),
        caption=t("figure.correlation_heatmap.caption", n=ctx.next_figure()),
    )]

    stats: dict[str, dict] = {
        f"{a}~{b}": {"r": r, "p": p, "n": n} for a, b, r, p in pairs
    }

    strongest = max(pairs, key=lambda p: abs(p[2])) if pairs else None
    auto_prose = ""
    if strongest is not None:
        a, b, r, p = strongest
        strength_word = t(correlation_strength_key(r))
        auto_prose = t(
            "prose.correlation_summary", var_a=a, var_b=b, strength=strength_word,
            df=fmt.integer(n - 2), r=fmt.r(r), p=fmt.p(p),
        )

    spss_vars = " ".join(v.replace(" ", "_") for v in variables)
    spss_syntax = f"CORRELATIONS /VARIABLES={spss_vars}\n  /PRINT=TWOTAIL SIG\n  /MISSING=PAIRWISE."

    return AnalysisResult(
        id="correlation",
        heading=t("section.correlation"),
        tables=[table],
        figures=figures,
        stats=stats,
        auto_prose=auto_prose,
        spss_syntax=spss_syntax,
    )
