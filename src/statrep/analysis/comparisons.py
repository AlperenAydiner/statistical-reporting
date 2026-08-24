"""Group comparisons, assumption-routed exactly like
`statistical-analysis/SKILL.md`'s `check_and_run_ttest()` policy:

- 2 groups: per-group normality (Shapiro n<50 / skew-kurtosis heuristic
  otherwise), then Levene's test -> Student's t / Welch's t / Mann-Whitney U.
- 3+ groups: per-group normality + Levene -> one-way ANOVA / Kruskal-Wallis.

Any automatic method switch is both recorded in `AnalysisResult.method_switched`
and folded into the printed assumption notes — never silent.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

from statrep.figures.plots import plot_anova_boxplot, plot_group_comparison

from .assumptions import check_normality, check_variance_homogeneity
from .context import AnalysisContext
from .results import AnalysisResult, FigureRef, TableSpec


def _welch_df(a: np.ndarray, b: np.ndarray) -> float:
    v1, v2 = a.var(ddof=1), b.var(ddof=1)
    n1, n2 = len(a), len(b)
    num = (v1 / n1 + v2 / n2) ** 2
    den = (v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1)
    return num / den if den else float(n1 + n2 - 2)


def _cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    n1, n2 = len(a), len(b)
    pooled_sd = np.sqrt(((n1 - 1) * a.var(ddof=1) + (n2 - 1) * b.var(ddof=1)) / (n1 + n2 - 2))
    return float((a.mean() - b.mean()) / pooled_sd) if pooled_sd else 0.0


def run_comparison(
    df: pd.DataFrame, dv: str, group_var: str, ctx: AnalysisContext
) -> AnalysisResult:
    groups = [g for g in df[group_var].dropna().unique()]
    if len(groups) < 2:
        raise ValueError(f"'{group_var}' needs at least 2 groups, found {len(groups)}")
    if len(groups) == 2:
        return _run_two_group(df, dv, group_var, groups, ctx)
    return _run_multi_group(df, dv, group_var, groups, ctx)


def _run_two_group(df, dv, group_var, groups, ctx: AnalysisContext) -> AnalysisResult:
    t, fmt = ctx.t, ctx.fmt
    name_a, name_b = groups[0], groups[1]
    a = df.loc[df[group_var] == name_a, dv].dropna().to_numpy(dtype=float)
    b = df.loc[df[group_var] == name_b, dv].dropna().to_numpy(dtype=float)

    norm_a, norm_b = check_normality(a), check_normality(b)
    assumption_notes: list[str] = []
    method_switched: str | None = None

    if norm_a.is_normal and norm_b.is_normal:
        var_check = check_variance_homogeneity(a, b)
        if var_check.equal_variance:
            stat, p = scipy_stats.ttest_ind(a, b, equal_var=True)
            test_key, df_val = "term.independent_ttest", len(a) + len(b) - 2
        else:
            stat, p = scipy_stats.ttest_ind(a, b, equal_var=False)
            test_key, df_val = "term.welch_ttest", _welch_df(a, b)
            method_switched = t("prose.method_switched_variance", p=fmt.p(var_check.levene_p))
            assumption_notes.append(method_switched)
        effect = _cohens_d(a, b)
        prose_key = "prose.comparison_ttest" if p < 0.05 else "prose.comparison_ttest_ns"
        prose_kwargs = dict(
            test_name=t(test_key), dv=dv, group_a=str(name_a), group_b=str(name_b),
            m_a=fmt.number(a.mean()), sd_a=fmt.number(a.std(ddof=1)),
            m_b=fmt.number(b.mean()), sd_b=fmt.number(b.std(ddof=1)),
            stat_symbol="t", df=fmt.integer(round(df_val)) if isinstance(df_val, int) else fmt.number(df_val, 2),
            stat=fmt.stat(stat), p=fmt.p(p), effect_symbol=t("term.cohens_d"), effect=fmt.number(effect),
        )
        stats = {"test": test_key, "statistic": float(stat), "df": float(df_val), "p": float(p),
                 "cohens_d": effect, "n_a": len(a), "n_b": len(b), "mean_a": float(a.mean()),
                 "mean_b": float(b.mean())}
    else:
        stat, p = scipy_stats.mannwhitneyu(a, b, alternative="two-sided")
        test_key = "term.mann_whitney"
        n1, n2 = len(a), len(b)
        effect = 1 - (2 * stat) / (n1 * n2)  # rank-biserial correlation
        failing = norm_a if not norm_a.is_normal else norm_b
        failing_group = name_a if not norm_a.is_normal else name_b
        method_switched = t(
            "prose.method_switched_normality", var=f"{dv} ({failing_group})",
            test_name=failing.test, p=fmt.p(failing.p_value) if failing.p_value is not None else "—",
            alt_method=t(test_key),
        )
        assumption_notes.append(method_switched)
        prose_key = "prose.comparison_mannwhitney" if p < 0.05 else "prose.comparison_mannwhitney_ns"
        prose_kwargs = dict(
            test_name=t(test_key), dv=dv, group_a=str(name_a), group_b=str(name_b),
            mdn_a=fmt.number(float(np.median(a))), mdn_b=fmt.number(float(np.median(b))),
            stat=fmt.stat(stat), p=fmt.p(p), effect=fmt.number(effect),
        )
        stats = {"test": test_key, "statistic": float(stat), "p": float(p), "rank_biserial_r": effect,
                  "n_a": len(a), "n_b": len(b), "median_a": float(np.median(a)), "median_b": float(np.median(b))}

    headers = [t("term.group"), t("term.n"), t("term.mean"), t("term.sd")]
    rows = [
        [str(name_a), fmt.integer(len(a)), fmt.number(a.mean()), fmt.number(a.std(ddof=1))],
        [str(name_b), fmt.integer(len(b)), fmt.number(b.mean()), fmt.number(b.std(ddof=1))],
    ]
    table = TableSpec(
        id=f"table_comparison_{dv}",
        caption=t("table.comparison.caption", n=ctx.next_table(), dv=dv, group=group_var),
        headers=headers, rows=rows, numeric_columns=[1, 2, 3],
    )

    fig_path = plot_group_comparison(
        means=[[a.mean()], [b.mean()]], sds=[[a.std(ddof=1)], [b.std(ddof=1)]],
        group_labels=[str(name_a), str(name_b)], dv_labels=[dv],
        title=f"{dv} {t('term.by')} {group_var}",
        save_path=ctx.figures_dir / f"fig-comparison-{dv}.png", p_values=[p],
    )
    figures = [FigureRef(
        id=f"fig_comparison_{dv}", path=str(fig_path),
        caption=t("figure.group_comparison.caption", n=ctx.next_figure(), dv=dv, group=group_var),
    )]

    spss_syntax = (
        f"T-TEST GROUPS={group_var.replace(' ', '_')}\n"
        f"  /VARIABLES={dv.replace(' ', '_')}\n"
        f"  /CRITERIA=CI(.95)."
    )

    return AnalysisResult(
        id=f"comparison_{dv}", heading=t("section.comparisons"), tables=[table], figures=figures,
        stats=stats, auto_prose=t(prose_key, **prose_kwargs), spss_syntax=spss_syntax,
        assumption_notes=assumption_notes, method_switched=method_switched,
    )


def _run_multi_group(df, dv, group_var, groups, ctx: AnalysisContext) -> AnalysisResult:
    t, fmt = ctx.t, ctx.fmt
    samples = [df.loc[df[group_var] == g, dv].dropna().to_numpy(dtype=float) for g in groups]
    norm_checks = [check_normality(s) for s in samples]
    var_check = check_variance_homogeneity(*samples)
    all_normal = all(c.is_normal for c in norm_checks)
    assumption_notes: list[str] = []
    method_switched: str | None = None

    if all_normal and var_check.equal_variance:
        stat, p = scipy_stats.f_oneway(*samples)
        test_key = "term.one_way_anova"
        df1, df2 = len(groups) - 1, sum(len(s) for s in samples) - len(groups)
        grand_mean = np.concatenate(samples).mean()
        ss_between = sum(len(s) * (s.mean() - grand_mean) ** 2 for s in samples)
        ss_total = sum(((np.concatenate(samples) - grand_mean) ** 2))
        effect = float(ss_between / ss_total) if ss_total else 0.0
        prose_key = "prose.comparison_anova" if p < 0.05 else "prose.comparison_anova_ns"
        stats = {"test": test_key, "statistic": float(stat), "df1": df1, "df2": df2,
                 "p": float(p), "eta_squared": effect}
    else:
        stat, p = scipy_stats.kruskal(*samples)
        test_key = "term.kruskal_wallis"
        df1, df2 = len(groups) - 1, None
        effect = None
        reason = "normality" if not all_normal else "variance"
        if reason == "normality":
            failing = next(c for c in norm_checks if not c.is_normal)
            method_switched = t("prose.method_switched_normality", var=dv, test_name=failing.test,
                                 p=fmt.p(failing.p_value) if failing.p_value is not None else "—",
                                 alt_method=t(test_key))
        else:
            method_switched = t("prose.method_switched_variance", p=fmt.p(var_check.levene_p))
        assumption_notes.append(method_switched)
        prose_key = "prose.comparison_anova" if p < 0.05 else "prose.comparison_anova_ns"
        stats = {"test": test_key, "statistic": float(stat), "df1": df1, "p": float(p)}

    headers = [t("term.group"), t("term.n"), t("term.mean"), t("term.sd")]
    rows = [
        [str(g), fmt.integer(len(s)), fmt.number(s.mean()), fmt.number(s.std(ddof=1))]
        for g, s in zip(groups, samples)
    ]
    table = TableSpec(
        id=f"table_comparison_{dv}",
        caption=t("table.comparison.caption", n=ctx.next_table(), dv=dv, group=group_var),
        headers=headers, rows=rows, numeric_columns=[1, 2, 3],
    )

    fig_path = plot_anova_boxplot(
        df, group_var=group_var, dv_vars=[dv],
        title=f"{dv} {t('term.by')} {group_var}",
        save_path=ctx.figures_dir / f"fig-anova-{dv}.png",
    )
    figures = [FigureRef(
        id=f"fig_anova_{dv}", path=str(fig_path),
        caption=t("figure.anova_boxplot.caption", n=ctx.next_figure(), dv=dv, group=group_var),
    )]

    prose_kwargs = dict(test_name=t(test_key), dv=dv, group=group_var,
                         df1=df1, df2=df2 if df2 is not None else "—",
                         stat=fmt.stat(stat), p=fmt.p(p),
                         effect=fmt.number(effect) if effect is not None else "—")

    spss_syntax = (
        f"ONEWAY {dv.replace(' ', '_')} BY {group_var.replace(' ', '_')}\n"
        f"  /STATISTICS DESCRIPTIVES HOMOGENEITY\n"
        f"  /POSTHOC=TUKEY ALPHA(0.05)."
    )

    return AnalysisResult(
        id=f"comparison_{dv}", heading=t("section.comparisons"), tables=[table], figures=figures,
        stats=stats, auto_prose=t(prose_key, **prose_kwargs), spss_syntax=spss_syntax,
        assumption_notes=assumption_notes, method_switched=method_switched,
    )
