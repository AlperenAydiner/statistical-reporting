"""Data profiling — the single source of truth for "what does this dataset
look like before any analysis runs."

This is a strict superset of two things that used to be duplicated in the
repo: `statistical-analysis`'s Step 0 (N, types, missing patterns,
skew/kurtosis, normality routing, 3SD outliers, alert lines) and
`programmatic-eda`'s per-column dtype/null/unique summary plus |r| > 0.8
multicollinearity flagging. The five `programmatic-eda/scripts/*.py`
wrappers call into this module rather than reimplementing it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats


@dataclass
class VariableProfile:
    name: str
    kind: str  # "numeric" | "categorical" | "datetime" | "text"
    n: int
    n_missing: int
    missing_rate: float
    n_unique: int
    # numeric-only fields (None otherwise)
    mean: float | None = None
    sd: float | None = None
    minimum: float | None = None
    maximum: float | None = None
    skewness: float | None = None
    kurtosis: float | None = None
    normality_test: str | None = None  # "shapiro" | "skew_kurtosis_heuristic"
    normality_p: float | None = None
    is_normal: bool | None = None
    n_outliers_3sd: int | None = None


@dataclass
class CorrelationFlag:
    var_a: str
    var_b: str
    r: float


@dataclass
class DataProfile:
    n_rows: int
    n_columns: int
    variables: list[VariableProfile] = field(default_factory=list)
    multicollinearity: list[CorrelationFlag] = field(default_factory=list)
    alerts: list[str] = field(default_factory=list)

    @property
    def n_numeric(self) -> int:
        return sum(1 for v in self.variables if v.kind == "numeric")

    @property
    def n_categorical(self) -> int:
        return sum(1 for v in self.variables if v.kind == "categorical")

    def by_name(self, name: str) -> VariableProfile | None:
        return next((v for v in self.variables if v.name == name), None)


def _missing_tier(rate: float) -> str:
    """statistical-analysis's missing-data policy tiers (informational —
    remediation is an analysis-time decision, this just classifies)."""
    if rate < 0.05:
        return "listwise-safe"
    if rate <= 0.20:
        return "consider-mice"
    return "investigate-mcar"


def _classify_column(series: pd.Series) -> str:
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    n = len(series)
    n_unique = series.nunique(dropna=True)
    # A low-cardinality object/string column is treated as categorical;
    # a high-cardinality one (free text, IDs) is left as "text".
    if n == 0:
        return "categorical"
    if n_unique <= max(20, int(n * 0.05)):
        return "categorical"
    return "text"


def _profile_numeric(series: pd.Series, vp: VariableProfile) -> None:
    values = series.dropna().astype(float)
    n = len(values)
    if n == 0:
        return
    vp.mean = float(values.mean())
    vp.sd = float(values.std(ddof=1)) if n > 1 else 0.0
    vp.minimum = float(values.min())
    vp.maximum = float(values.max())
    vp.skewness = float(values.skew()) if n > 2 else None
    vp.kurtosis = float(values.kurtosis()) if n > 3 else None

    # Normality routing, matching statistical-analysis Step 0:
    # n < 50 -> Shapiro-Wilk; otherwise a skew/kurtosis heuristic
    # (|skew| < 2 and |kurtosis| < 7 is treated as "roughly normal" —
    # Shapiro over-rejects at large n).
    if n < 50 and n >= 3:
        try:
            _, p = stats.shapiro(values)
            vp.normality_test = "shapiro"
            vp.normality_p = float(p)
            vp.is_normal = p >= 0.05
        except Exception:
            vp.normality_test = None
    elif n >= 50 and vp.skewness is not None and vp.kurtosis is not None:
        vp.normality_test = "skew_kurtosis_heuristic"
        vp.is_normal = abs(vp.skewness) < 2 and abs(vp.kurtosis) < 7

    if vp.sd and vp.sd > 0:
        z = (values - vp.mean) / vp.sd
        vp.n_outliers_3sd = int((z.abs() > 3).sum())
    else:
        vp.n_outliers_3sd = 0


def profile(df: pd.DataFrame) -> DataProfile:
    """Profile a DataFrame: per-column stats, normality routing, 3SD
    outlier counts, and |r| > 0.8 multicollinearity flags."""
    n_rows, n_columns = df.shape
    result = DataProfile(n_rows=n_rows, n_columns=n_columns)

    for col in df.columns:
        series = df[col]
        n_missing = int(series.isna().sum())
        kind = _classify_column(series)
        vp = VariableProfile(
            name=str(col),
            kind=kind,
            n=n_rows,
            n_missing=n_missing,
            missing_rate=(n_missing / n_rows) if n_rows else 0.0,
            n_unique=int(series.nunique(dropna=True)),
        )
        if kind == "numeric":
            _profile_numeric(series, vp)
        result.variables.append(vp)

        if vp.missing_rate > 0.20:
            result.alerts.append(
                f"'{vp.name}': {vp.missing_rate:.1%} missing — investigate whether "
                f"missingness is random (Little's MCAR test) before imputing."
            )
        elif vp.missing_rate >= 0.05:
            result.alerts.append(
                f"'{vp.name}': {vp.missing_rate:.1%} missing — consider multiple "
                f"imputation (MICE) rather than listwise deletion."
            )

        if kind == "numeric" and vp.n_outliers_3sd:
            result.alerts.append(
                f"'{vp.name}': {vp.n_outliers_3sd} value(s) beyond 3 SD from the mean."
            )
        if kind == "numeric" and vp.is_normal is False:
            test_label = "Shapiro-Wilk" if vp.normality_test == "shapiro" else "skew/kurtosis heuristic"
            result.alerts.append(
                f"'{vp.name}': fails normality ({test_label}) — non-parametric or "
                f"robust methods may be more appropriate."
            )

    # Multicollinearity: |r| > 0.8 among numeric columns.
    numeric_cols = [v.name for v in result.variables if v.kind == "numeric"]
    if len(numeric_cols) >= 2:
        corr = df[numeric_cols].corr(method="pearson")
        for a, b in combinations(numeric_cols, 2):
            r = corr.loc[a, b]
            if pd.notna(r) and abs(r) > 0.8:
                result.multicollinearity.append(CorrelationFlag(var_a=a, var_b=b, r=float(r)))
        if result.multicollinearity:
            pairs = ", ".join(f"{f.var_a}~{f.var_b} (r={f.r:.2f})" for f in result.multicollinearity)
            result.alerts.append(f"Possible multicollinearity: {pairs}.")

    return result
