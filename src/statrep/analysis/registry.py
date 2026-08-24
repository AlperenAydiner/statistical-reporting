"""Single dispatch point from an outline entry's ``analysis`` id to the
function that runs it. Kept intentionally thin — each analysis function's
own module is the place to read for what it actually does; this just
avoids report/outline.py importing four modules directly and hardcoding
branch logic.

See `.claude/skills/statistical-analysis/references/methods-index.md` for
the full method-selection decision trees this registry's routing logic
(in `assumptions.py` / `comparisons.py`) implements a slice of.
"""

from __future__ import annotations

from typing import Callable

import pandas as pd

from .comparisons import run_comparison
from .context import AnalysisContext
from .correlation import run_correlation_matrix
from .descriptives import run_descriptives_continuous
from .regression import run_linear_regression
from .results import AnalysisResult

REGISTRY: dict[str, Callable[..., AnalysisResult]] = {
    "descriptives_continuous": run_descriptives_continuous,
    "comparison": run_comparison,
    "correlation": run_correlation_matrix,
    "regression": run_linear_regression,
}


def run(analysis_id: str, df: pd.DataFrame, params: dict, ctx: AnalysisContext) -> AnalysisResult:
    """Look up ``analysis_id`` in the registry and call it with ``df``,
    ``ctx``, and ``params`` unpacked as keyword arguments."""
    if analysis_id not in REGISTRY:
        raise KeyError(f"Unknown analysis id: {analysis_id!r} (known: {sorted(REGISTRY)})")
    return REGISTRY[analysis_id](df, ctx=ctx, **params)
