"""Descriptive statistics block: one APA table + one distribution figure per
continuous variable (capped, per the Standard tier's "4-8 distribution
figures" budget), built on top of `statrep.io.profile` so the numbers here
are always identical to what the Data Quality section already reported —
no second, drifting implementation of mean/SD/skew/kurtosis."""

from __future__ import annotations

import pandas as pd

from statrep.figures.plots import plot_distribution
from statrep.io.profile import profile

from .context import AnalysisContext
from .results import AnalysisResult, FigureRef, TableSpec

MAX_DISTRIBUTION_FIGURES = 8


def run_descriptives_continuous(
    df: pd.DataFrame, variables: list[str], ctx: AnalysisContext
) -> AnalysisResult:
    t, fmt = ctx.t, ctx.fmt
    numeric_df = df[variables]
    data_profile = profile(numeric_df)
    var_profiles = [v for v in data_profile.variables if v.kind == "numeric"]

    headers = [
        t("term.variable"), t("term.n"), t("term.mean"), t("term.sd"),
        t("term.skewness"), t("term.kurtosis"),
    ]
    rows: list[list[str]] = []
    stats: dict[str, dict] = {}
    prose_parts: list[str] = []

    for vp in var_profiles:
        n_valid = vp.n - vp.n_missing
        rows.append([
            vp.name,
            fmt.integer(n_valid),
            fmt.number(vp.mean),
            fmt.number(vp.sd),
            fmt.number(vp.skewness),
            fmt.number(vp.kurtosis),
        ])
        stats[vp.name] = {
            "n": n_valid, "mean": vp.mean, "sd": vp.sd,
            "skewness": vp.skewness, "kurtosis": vp.kurtosis,
        }
        prose_parts.append(
            t("prose.descriptives_continuous", var=vp.name,
              m=fmt.number(vp.mean), sd=fmt.number(vp.sd), n=fmt.integer(n_valid))
        )

    table = TableSpec(
        id="table_desc_continuous",
        caption=t("table.desc_continuous.caption", n=ctx.next_table()),
        headers=headers,
        rows=rows,
        numeric_columns=[1, 2, 3, 4, 5],
    )

    figures: list[FigureRef] = []
    for vp in var_profiles[:MAX_DISTRIBUTION_FIGURES]:
        path = plot_distribution(
            numeric_df[vp.name], title=vp.name,
            save_path=ctx.figures_dir / f"fig-desc-{vp.name}.png",
        )
        figures.append(FigureRef(
            id=f"fig_desc_{vp.name}", path=str(path),
            caption=t("figure.distribution.caption", n=ctx.next_figure(), var=vp.name),
        ))

    spss_vars = " ".join(_spss_safe(v) for v in variables)
    spss_syntax = (
        f"DESCRIPTIVES VARIABLES={spss_vars}\n"
        f"  /STATISTICS=MEAN STDDEV SKEWNESS KURTOSIS MIN MAX."
    )

    return AnalysisResult(
        id="descriptives_continuous",
        heading=t("section.descriptives.continuous"),
        tables=[table],
        figures=figures,
        stats=stats,
        auto_prose=" ".join(prose_parts),
        spss_syntax=spss_syntax,
        assumption_notes=data_profile.alerts,
    )


def _spss_safe(name: str) -> str:
    """SPSS variable names cannot contain spaces; Turkish diacritics are
    risky too. This is a display-safe fallback — the full RENAME VARIABLES
    mapping layer lives in statrep.spss (M2)."""
    return "".join(ch if ch.isalnum() else "_" for ch in name)
