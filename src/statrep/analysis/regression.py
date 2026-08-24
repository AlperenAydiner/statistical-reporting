"""Multiple linear regression: unstandardized + standardized coefficients,
VIF collinearity diagnostics, model fit statistics, and a coefficient
forest plot. VIF > 5 is flagged in the assumption notes (a stricter,
more commonly cited threshold than the classic 10)."""

from __future__ import annotations

from statsmodels.regression.linear_model import OLS
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.tools import add_constant

from statrep.figures.plots import plot_regression_coefficients

from .assumptions import check_normality
from .context import AnalysisContext
from .results import AnalysisResult, FigureRef, TableSpec

VIF_FLAG_THRESHOLD = 5.0


def run_linear_regression(df, dv: str, predictors: list[str], ctx: AnalysisContext) -> AnalysisResult:
    t, fmt = ctx.t, ctx.fmt
    data = df[[dv, *predictors]].dropna()
    n = len(data)

    X_raw = add_constant(data[predictors])
    y = data[dv]
    model = OLS(y, X_raw).fit()

    def z(series):
        return (series - series.mean()) / series.std(ddof=1)

    Xz = add_constant(data[predictors].apply(z))
    yz = z(data[dv])
    model_z = OLS(yz, Xz).fit()
    betas = model_z.params.drop("const")
    ci = model_z.conf_int().drop("const")

    vif_values = {
        name: float(variance_inflation_factor(X_raw.values, i + 1))
        for i, name in enumerate(predictors)
    }

    headers = [t("term.predictor"), "B", "SE", t("term.beta"), "t", "p", t("term.vif")]
    rows = [[
        t("term.intercept"), fmt.number(model.params["const"]), fmt.number(model.bse["const"]),
        "—", fmt.stat(model.tvalues["const"]), fmt.p(model.pvalues["const"]), "—",
    ]]
    assumption_notes: list[str] = []
    for name in predictors:
        vif_val = vif_values[name]
        rows.append([
            name, fmt.number(model.params[name]), fmt.number(model.bse[name]),
            fmt.number(betas[name]), fmt.stat(model.tvalues[name]), fmt.p(model.pvalues[name]),
            fmt.number(vif_val, 1),
        ])
        if vif_val > VIF_FLAG_THRESHOLD:
            assumption_notes.append(
                f"'{name}': VIF = {fmt.number(vif_val, 1)} (> {VIF_FLAG_THRESHOLD:.0f}) — "
                f"possible multicollinearity."
            )

    resid_normality = check_normality(model.resid)
    if not resid_normality.is_normal:
        assumption_notes.append(
            f"Residuals fail normality ({resid_normality.test}"
            + (f", p = {fmt.p(resid_normality.p_value)}" if resid_normality.p_value is not None else "")
            + ") — interpret p-values with caution; consider a robust or bootstrap approach."
        )

    table = TableSpec(
        id=f"table_regression_{dv}",
        caption=t("table.regression.caption", n=ctx.next_table(), dv=dv),
        headers=headers, rows=rows, numeric_columns=[1, 2, 3, 4, 5, 6],
        note=t("table.note.apa_stars"),
    )

    fig_path = plot_regression_coefficients(
        names=list(betas.index), betas=list(betas.values),
        ci_lower=list(ci[0].values), ci_upper=list(ci[1].values),
        title=t("section.regression"),
        save_path=ctx.figures_dir / f"fig-regression-{dv}.png",
    )
    figures = [FigureRef(
        id=f"fig_regression_{dv}", path=str(fig_path),
        caption=t("figure.regression_coefficients.caption", n=ctx.next_figure()),
    )]

    stats = {
        "r_squared": float(model.rsquared), "adj_r_squared": float(model.rsquared_adj),
        "f": float(model.fvalue), "df1": int(model.df_model), "df2": int(model.df_resid),
        "f_p": float(model.f_pvalue), "n": n,
        "predictors": {
            name: {"b": float(model.params[name]), "beta": float(betas[name]),
                   "t": float(model.tvalues[name]), "p": float(model.pvalues[name]),
                   "vif": vif_values[name]}
            for name in predictors
        },
    }

    auto_prose = t(
        "prose.regression_summary", dv=dv,
        df1=fmt.integer(int(model.df_model)), df2=fmt.integer(int(model.df_resid)),
        f=fmt.stat(model.fvalue), p=fmt.p(model.f_pvalue),
        r2=fmt.number(model.rsquared), adj_r2=fmt.number(model.rsquared_adj),
    )

    spss_predictors = " ".join(p.replace(" ", "_") for p in predictors)
    spss_syntax = (
        f"REGRESSION /DEPENDENT {dv.replace(' ', '_')}\n"
        f"  /METHOD=ENTER {spss_predictors}\n"
        f"  /STATISTICS COEFF OUTS R ANOVA COLLIN TOL."
    )

    return AnalysisResult(
        id=f"regression_{dv}", heading=t("section.regression"), tables=[table], figures=figures,
        stats=stats, auto_prose=auto_prose, spss_syntax=spss_syntax,
        assumption_notes=assumption_notes,
    )
