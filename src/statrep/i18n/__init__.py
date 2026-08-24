"""Bilingual (TR/EN) string lookup. No user-visible literal text lives in
Python or YAML outside this module's data files — every heading, table
header, and prose sentence is looked up by a dotted key so a report can be
generated in either language from the same code path.

Also home to the two small Turkish-specific text helpers that generic
``str.upper()``/``str.title()`` get wrong: ``tr_upper`` / ``tr_title``
(dotted/dotless I).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_DATA_DIR = Path(__file__).parent


def _flatten(data: dict, prefix: str = "") -> dict[str, str]:
    """Flatten a nested dict into dotted keys: {"a": {"b": "x"}} -> {"a.b": "x"}."""
    out: dict[str, str] = {}
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            out.update(_flatten(value, full_key))
        else:
            out[full_key] = value
    return out


class Translator:
    """Looks up dotted i18n keys for one language and formats them with
    keyword arguments. A missing key renders visibly (``[[MISSING:key]]``)
    instead of silently falling back to English or crashing — this is what
    the pseudolocale verification pass (see plan) scans for."""

    def __init__(self, lang: str, data_dir: Path | None = None):
        if lang not in ("en", "tr"):
            raise ValueError(f"Unsupported language: {lang!r} (expected 'en' or 'tr')")
        self.lang = lang
        data_dir = data_dir or _DATA_DIR
        raw = yaml.safe_load((data_dir / f"{lang}.yaml").read_text(encoding="utf-8"))
        self._flat = _flatten(raw)

    def __call__(self, key: str, **kwargs: Any) -> str:
        template = self._flat.get(key)
        if template is None:
            return f"[[MISSING:{key}]]"
        return template.format(**kwargs) if kwargs else template

    def has(self, key: str) -> bool:
        return key in self._flat


def tr_upper(text: str) -> str:
    """Turkish-correct uppercase: 'i' -> 'İ', 'ı' -> 'I' (plain str.upper()
    wrongly maps 'i' -> 'I', losing the dot)."""
    out = []
    for ch in text:
        if ch == "i":
            out.append("İ")
        elif ch == "ı":
            out.append("I")
        else:
            out.append(ch.upper())
    return "".join(out)


def tr_lower(text: str) -> str:
    """Turkish-correct lowercase: 'İ' -> 'i', 'I' -> 'ı'."""
    out = []
    for ch in text:
        if ch == "İ":
            out.append("i")
        elif ch == "I":
            out.append("ı")
        else:
            out.append(ch.lower())
    return "".join(out)


def tr_title(text: str) -> str:
    """Turkish-correct title case, word by word."""
    words = text.split(" ")
    out = []
    for w in words:
        if not w:
            out.append(w)
            continue
        out.append(tr_upper(w[0]) + (tr_lower(w[1:]) if len(w) > 1 else ""))
    return " ".join(out)
