"""Assumption checks that ROUTE method selection — not just report it.

Mirrors `statistical-analysis/SKILL.md`'s `check_and_run_ttest()` policy:
test normality per group (Shapiro-Wilk if n<50, else a skew/kurtosis
heuristic), then Levene's test for variance homogeneity, then let the
caller dispatch to the matching test. Every switch away from the
user's/default's requested method must be announced — callers set
``AnalysisResult.method_switched`` from the strings this module returns.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats


@dataclass
class NormalityCheck:
    test: str  # "shapiro" | "skew_kurtosis_heuristic"
    statistic: float | None
    p_value: float | None
    is_normal: bool


@dataclass
class VarianceCheck:
    levene_statistic: float
    levene_p: float
    equal_variance: bool


def check_normality(values: pd.Series | np.ndarray) -> NormalityCheck:
    values = pd.Series(values).dropna().astype(float)
    n = len(values)
    if n < 3:
        return NormalityCheck(test="insufficient_n", statistic=None, p_value=None, is_normal=True)
    if n < 50:
        stat, p = stats.shapiro(values)
        return NormalityCheck(test="shapiro", statistic=float(stat), p_value=float(p), is_normal=p >= 0.05)
    skew, kurt = float(values.skew()), float(values.kurtosis())
    is_normal = abs(skew) < 2 and abs(kurt) < 7
    return NormalityCheck(test="skew_kurtosis_heuristic", statistic=None, p_value=None, is_normal=is_normal)


def check_variance_homogeneity(*groups: pd.Series | np.ndarray) -> VarianceCheck:
    clean = [pd.Series(g).dropna().astype(float).to_numpy() for g in groups]
    stat, p = stats.levene(*clean)
    return VarianceCheck(levene_statistic=float(stat), levene_p=float(p), equal_variance=p >= 0.05)
