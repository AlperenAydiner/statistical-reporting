"""Load Excel/CSV/TSV data into a pandas DataFrame, robust to the Turkish-data
hazards that plain ``pd.read_csv`` gets wrong silently: mixed encodings,
``;``-delimited exports, and decimal-comma numbers.

Every inference this module makes (encoding, delimiter, decimal separator,
which columns were re-parsed) is recorded in ``LoadedData.warnings`` so it
can be surfaced in the report's Data Quality section — nothing is silently
assumed.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

# Turkish-specific diacritics used to score a decoding attempt.
_TURKISH_CHARS = set("çğıöşüÇĞİÖŞÜ")

# Byte sequences that only appear when UTF-8 text has been mis-decoded as
# Windows-1252/Latin-1 and re-encoded (a classic "mojibake" signature).
_MOJIBAKE_MARKERS = ("Ã§", "Ã¼", "Ã¶", "Ã–", "Å\x9f", "Å\x9e", "Ä°", "Ä±", "Ã‡")

# Fallback decode order when charset-normalizer is not confident.
_ENCODING_FALLBACKS = ("utf-8", "utf-8-sig", "cp1254", "iso-8859-9")

# A value that looks like a European-style number: thousands separated by
# '.', decimal separated by ','  e.g. "1.234,56" or "-3,5" or "12,0"
_DECIMAL_COMMA_RE = re.compile(r"^-?\d{1,3}(\.\d{3})*(,\d+)?$|^-?\d+,\d+$")


@dataclass
class LoadedData:
    df: pd.DataFrame
    source_path: str
    file_kind: str  # "excel" | "csv"
    encoding: str | None = None
    delimiter: str | None = None
    decimal: str = "."
    sheet_name: str | None = None
    decimal_comma_columns: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _score_text(text: str) -> int:
    """Higher is better: rewards Turkish diacritics, penalizes mojibake."""
    score = sum(1 for ch in text if ch in _TURKISH_CHARS)
    score -= 5 * sum(text.count(marker) for marker in _MOJIBAKE_MARKERS)
    return score


def _detect_encoding(raw: bytes) -> tuple[str, list[str]]:
    """Return (encoding, warnings). Tries charset-normalizer first, then a
    fallback chain scored by Turkish-character plausibility."""
    warnings: list[str] = []

    try:
        from charset_normalizer import from_bytes

        best = from_bytes(raw).best()
        if best is not None and best.encoding:
            # Sanity-check charset-normalizer's guess against the scoring
            # heuristic too — it occasionally prefers an encoding that
            # decodes cleanly but wrongly for Turkish-specific bytes.
            try:
                sample = raw[:20000].decode(best.encoding)
                candidates = {best.encoding: _score_text(sample)}
                for enc in _ENCODING_FALLBACKS:
                    try:
                        candidates[enc] = _score_text(raw[:20000].decode(enc))
                    except (UnicodeDecodeError, LookupError):
                        continue
                winner = max(candidates, key=candidates.get)
                if winner != best.encoding:
                    warnings.append(
                        f"Encoding auto-detection: charset-normalizer suggested "
                        f"'{best.encoding}' but '{winner}' scored higher on Turkish "
                        f"character plausibility; using '{winner}'."
                    )
                return winner, warnings
            except Exception:
                warnings.append(f"Encoding detected via charset-normalizer: '{best.encoding}'.")
                return best.encoding, warnings
    except ImportError:
        pass

    # Fallback chain, scored.
    scores: dict[str, int] = {}
    for enc in _ENCODING_FALLBACKS:
        try:
            scores[enc] = _score_text(raw.decode(enc))
        except (UnicodeDecodeError, LookupError):
            continue
    if not scores:
        warnings.append("Could not confidently decode file; falling back to 'utf-8' with errors='replace'.")
        return "utf-8", warnings
    winner = max(scores, key=scores.get)
    warnings.append(f"Encoding auto-detected as '{winner}' (fallback scoring chain).")
    return winner, warnings


def _detect_delimiter(sample: str) -> tuple[str, list[str]]:
    """Detect the CSV delimiter, biased toward ';' because Turkish Excel
    exports use ';' precisely because ',' is the decimal separator."""
    warnings: list[str] = []
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,\t|")
        delim = dialect.delimiter
        warnings.append(f"Delimiter auto-detected as '{delim}'.")
        return delim, warnings
    except csv.Error:
        # Sniffer failed (e.g. single column). Count candidates on the
        # first line and prefer ';' on a tie, since that is the Turkish norm.
        first_line = sample.splitlines()[0] if sample else ""
        counts = {d: first_line.count(d) for d in (";", ",", "\t", "|")}
        best = max(counts, key=lambda d: (counts[d], d == ";"))
        if counts[best] == 0:
            warnings.append("No delimiter detected (single column?); defaulting to ','.")
            return ",", warnings
        warnings.append(f"Delimiter sniffing failed; heuristic fallback chose '{best}'.")
        return best, warnings


def _looks_decimal_comma(series: pd.Series) -> bool:
    """True if a majority of non-null string values in this column match
    the '1.234,56' / '3,5' European number pattern."""
    non_null = series.dropna().astype(str).str.strip()
    if non_null.empty:
        return False
    sample = non_null.head(200)
    matches = sample.apply(lambda v: bool(_DECIMAL_COMMA_RE.match(v)))
    return matches.mean() > 0.7


def _convert_decimal_comma_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Re-parse non-numeric columns that look like European-formatted
    numbers into proper floats. Returns (df, converted_column_names).

    Checks ``is_numeric_dtype`` rather than ``dtype == object`` — pandas
    3.x's default string dtype for text columns is no longer plain
    ``object``, so an equality check against ``object`` silently skips
    every text column read from a CSV.
    """
    converted: list[str] = []
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            continue
        if _looks_decimal_comma(df[col]):
            cleaned = (
                df[col]
                .astype(str)
                .str.strip()
                .str.replace(".", "", regex=False)  # thousands separator
                .str.replace(",", ".", regex=False)  # decimal separator
            )
            numeric = pd.to_numeric(cleaned, errors="coerce")
            # Only commit the conversion if it didn't destroy most of the data.
            if numeric.notna().mean() >= df[col].notna().mean() * 0.9:
                df[col] = numeric
                converted.append(str(col))
    return df, converted


def load(path: str | Path, sheet_name: str | int | None = 0) -> LoadedData:
    """Load an Excel (.xlsx/.xls) or CSV/TSV file into a LoadedData bundle.

    For CSV/TSV, encoding and delimiter are auto-detected; columns that look
    like European-formatted numbers ("1.234,56") are re-parsed to float.
    All inferences are recorded in ``LoadedData.warnings``.
    """
    path = Path(path)
    suffix = path.suffix.lower()
    warnings: list[str] = []

    if suffix in (".xlsx", ".xlsm", ".xltx", ".xltm"):
        df = pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl")
        resolved_sheet = str(sheet_name)
        return LoadedData(
            df=df, source_path=str(path), file_kind="excel",
            sheet_name=resolved_sheet, warnings=warnings,
        )

    if suffix == ".xls":
        df = pd.read_excel(path, sheet_name=sheet_name, engine="xlrd")
        resolved_sheet = str(sheet_name)
        return LoadedData(
            df=df, source_path=str(path), file_kind="excel",
            sheet_name=resolved_sheet, warnings=warnings,
        )

    # CSV / TSV path.
    raw = path.read_bytes()
    encoding, enc_warnings = _detect_encoding(raw)
    warnings.extend(enc_warnings)

    text = raw.decode(encoding, errors="replace")
    sample = "\n".join(text.splitlines()[:20])
    delimiter, delim_warnings = _detect_delimiter(sample)
    warnings.extend(delim_warnings)

    if suffix == ".tsv" and delimiter != "\t":
        # A .tsv extension is a strong prior; trust it over sniffing.
        delimiter = "\t"
        warnings.append("File extension is .tsv; overriding sniffed delimiter with tab.")

    df = pd.read_csv(path, encoding=encoding, sep=delimiter, engine="python")
    df, converted_cols = _convert_decimal_comma_columns(df)
    decimal = ","
    if converted_cols:
        warnings.append(
            f"Detected decimal-comma formatting and converted {len(converted_cols)} "
            f"column(s) to numeric: {', '.join(converted_cols)}."
        )
    else:
        decimal = "."

    return LoadedData(
        df=df, source_path=str(path), file_kind="csv",
        encoding=encoding, delimiter=delimiter, decimal=decimal,
        decimal_comma_columns=converted_cols, warnings=warnings,
    )
