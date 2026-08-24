"""Number formatting — the single choke point every number passes through
before it reaches a table, figure caption, or prose sentence.

Deliberately does NOT use ``locale.setlocale``: ``tr_TR.UTF-8`` is usually
not generated on a bare container and the failure is silent. All TR/EN
formatting differences are implemented by hand instead.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class NumberFormatter:
    """Formats numbers for one locale ("tr" or "en").

    TR: decimal comma, dot thousands separator — 1.234,56
    EN: decimal dot, comma thousands separator  — 1,234.56

    APA rule (both locales): p-values and correlation-like statistics that
    cannot exceed 1 in magnitude omit the leading zero — "p < ,001" / "r = ,45"
    in Turkish, "p < .001" / "r = .45" in English. Writing "p < 0,001" or
    "p < .001" in a Turkish report are both wrong; this class is the only
    place that decision is made.
    """

    locale: str  # "tr" | "en"

    def __post_init__(self):
        if self.locale not in ("tr", "en"):
            raise ValueError(f"Unsupported locale: {self.locale!r} (expected 'tr' or 'en')")

    @property
    def decimal_sep(self) -> str:
        return "," if self.locale == "tr" else "."

    @property
    def thousands_sep(self) -> str:
        return "." if self.locale == "tr" else ","

    def number(self, value: float | int | None, decimals: int = 2) -> str:
        """General-purpose number: thousands-grouped, locale decimal
        separator. Returns an em dash for None/NaN."""
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return "—"
        text = f"{value:,.{decimals}f}"  # always produced US-style first: "1,234.56"
        if self.locale == "tr":
            text = text.translate(str.maketrans({",": "\x00", ".": ","})).replace("\x00", ".")
        return text

    def integer(self, value: int | None) -> str:
        if value is None:
            return "—"
        return self.number(value, decimals=0)

    def _no_leading_zero(self, magnitude: float, decimals: int) -> str:
        """'0.45' -> '.45' (or ',45' in tr). Caller supplies a non-negative magnitude."""
        core = f"{magnitude:.{decimals}f}"  # "0.450"
        core = core[1:]  # ".450"
        if self.locale == "tr":
            core = "," + core[1:]
        return core

    def r(self, value: float | None, decimals: int = 2) -> str:
        """Correlation-like statistic (|value| <= 1): no leading zero, sign kept."""
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return "—"
        sign = "-" if value < 0 else ""
        return sign + self._no_leading_zero(abs(value), decimals)

    def p(self, value: float | None, decimals: int = 3) -> str:
        """APA p-value: '= .045' / '< .001' (or ',' in tr)."""
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return "—"
        threshold = 10 ** (-decimals)
        if value < threshold:
            return f"< {self._no_leading_zero(threshold, decimals)}"
        return f"= {self._no_leading_zero(value, decimals)}"

    def stat(self, value: float | None, decimals: int = 2) -> str:
        """Test statistic (t, F, etc.) — normal decimal formatting, no
        leading-zero suppression since these routinely exceed 1."""
        return self.number(value, decimals=decimals)


def correlation_strength_key(r: float) -> str:
    """Maps |r| to an i18n term key (term.corr_weak/moderate/strong) per the
    conventional Cohen (1988) thresholds."""
    magnitude = abs(r)
    if magnitude < 0.3:
        return "term.corr_weak"
    if magnitude < 0.5:
        return "term.corr_moderate"
    return "term.corr_strong"
