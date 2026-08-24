"""Orchestrates the full pipeline: load -> profile -> auto-select variables
-> run analyses -> assemble the manifest -> render report.docx/.html plus
the tables.xlsx / analysis.sps side files.

M1 executes the Standard tier's fixed section set directly (see
`outlines/standard.yaml`'s note) — variable auto-selection is a small,
explicit heuristic here rather than a generic rule engine, matching the
plan's decision to prove the end-to-end path before building the fuller
tier system.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pandas as pd

from statrep.analysis import registry
from statrep.analysis.context import make_context
from statrep.analysis.results import AnalysisResult, TableSpec
from statrep.io.loaders import load
from statrep.io.profile import DataProfile, profile
from statrep.render.markdown import ReportMeta, render_markdown
from statrep.render.pandoc import markdown_to_docx, markdown_to_html
from statrep.render.postprocess import postprocess

_REFERENCE_DIR = Path(__file__).resolve().parent.parent / "render" / "reference"

MAX_DESCRIPTIVES_VARS = 10
MAX_REGRESSION_PREDICTORS = 5


_ID_NAME_TOKENS = ("id", " no", "no.", "numara", "sıra no", "sira no", "index", "kod", "kimlik")


def _is_id_like(series: pd.Series, name: str) -> bool:
    """True for identifier-shaped columns (a row number, a participant ID)
    that are numeric in dtype but meaningless as an analysis variable —
    without this, a bare "Katılımcı No" column gets auto-selected as a
    regression predictor or t-test DV, which is statistically vacuous."""
    non_null = series.dropna()
    if len(non_null) < 2:
        return False
    is_whole = (non_null == non_null.round()).all()
    fully_unique = non_null.nunique() == len(non_null)
    if is_whole and fully_unique:
        values = sorted(non_null.astype(int).tolist())
        if values == list(range(values[0], values[0] + len(values))):
            return True  # a contiguous integer sequence, e.g. 1..n
    lname = name.lower()
    if any(tok in lname for tok in _ID_NAME_TOKENS) and non_null.nunique() / len(non_null) > 0.95:
        return True
    return False


def _select_numeric(df: pd.DataFrame, data_profile: DataProfile, cap: int) -> list[str]:
    candidates = [v.name for v in data_profile.variables if v.kind == "numeric"]
    substantive = [name for name in candidates if not _is_id_like(df[name], name)]
    return substantive[:cap]


def _select_categorical_for_comparison(data_profile: DataProfile) -> str | None:
    """Prefer a categorical column with few missing values and a small,
    report-friendly number of levels (2-6)."""
    candidates = [v for v in data_profile.variables if v.kind == "categorical" and 2 <= v.n_unique <= 6]
    if not candidates:
        return None
    candidates.sort(key=lambda v: (v.missing_rate, v.n_unique))
    return candidates[0].name


def _write_tables_xlsx(tables: list[TableSpec], path: Path) -> None:
    with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
        for i, table in enumerate(tables, start=1):
            frame = pd.DataFrame(table.rows, columns=table.headers)
            frame.to_excel(writer, sheet_name=f"Table{i}"[:31], index=False)


def build_report(
    input_path: str | Path,
    output_dir: str | Path,
    lang: str = "tr",
    title: str | None = None,
    template: str = "academic-apa7",
    dv: str | None = None,
    group_var: str | None = None,
    predictors: list[str] | None = None,
) -> dict:
    """Run the full pipeline and write every output file. Returns a summary
    dict of output paths and counts for the CLI to print."""
    output_dir = Path(output_dir)
    figures_dir = output_dir / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    loaded = load(input_path)
    data_profile = profile(loaded.df)
    ctx = make_context(lang, figures_dir)
    t = ctx.t

    numeric_vars = _select_numeric(loaded.df, data_profile, MAX_DESCRIPTIVES_VARS)
    results: list[AnalysisResult] = []

    if numeric_vars:
        results.append(registry.run(
            "descriptives_continuous", loaded.df, {"variables": numeric_vars}, ctx,
        ))

    if len(numeric_vars) >= 2:
        results.append(registry.run(
            "correlation", loaded.df, {"variables": numeric_vars}, ctx,
        ))

    chosen_group_var = group_var or _select_categorical_for_comparison(data_profile)
    if chosen_group_var and numeric_vars:
        chosen_dv = dv or numeric_vars[0]
        results.append(registry.run(
            "comparison", loaded.df, {"dv": chosen_dv, "group_var": chosen_group_var}, ctx,
        ))

    if len(numeric_vars) >= 2:
        reg_dv = dv or numeric_vars[-1]
        reg_predictors = predictors or [v for v in numeric_vars if v != reg_dv][:MAX_REGRESSION_PREDICTORS]
        if reg_predictors:
            results.append(registry.run(
                "regression", loaded.df, {"dv": reg_dv, "predictors": reg_predictors}, ctx,
            ))

    if not results:
        raise ValueError(
            "No analyses could be run on this dataset — need at least one numeric column."
        )

    report_title = title or Path(input_path).stem
    meta = ReportMeta(
        title=report_title,
        subtitle=t("section.cover.subtitle_default"),
        date=dt.date.today().isoformat(),
        lang=lang,
    )
    md_text = render_markdown(meta, results)
    md_path = output_dir / "report.md"
    md_path.write_text(md_text, encoding="utf-8")

    reference_docx = _REFERENCE_DIR / f"{template}.docx"
    docx_path = output_dir / "report.docx"
    markdown_to_docx(md_path, docx_path, reference_docx)
    all_tables = [tbl for r in results for tbl in r.tables]
    postprocess(docx_path, all_tables)

    html_path = output_dir / "report.html"
    markdown_to_html(md_path, html_path)

    tables_xlsx_path = output_dir / "tables.xlsx"
    _write_tables_xlsx(all_tables, tables_xlsx_path)

    sps_blocks = [r.spss_syntax for r in results if r.spss_syntax]
    sps_path = output_dir / "analysis.sps"
    sps_path.write_text("\n\n".join(sps_blocks) + "\n", encoding="utf-8")

    manifest = {
        "meta": {"title": meta.title, "lang": meta.lang, "date": meta.date, "input": str(input_path)},
        "loader": {
            "encoding": loaded.encoding, "delimiter": loaded.delimiter,
            "decimal": loaded.decimal, "warnings": loaded.warnings,
        },
        "profile_alerts": data_profile.alerts,
        "results": [r.to_dict() for r in results],
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "docx": str(docx_path), "html": str(html_path), "md": str(md_path),
        "tables_xlsx": str(tables_xlsx_path), "sps": str(sps_path),
        "manifest": str(manifest_path),
        "n_analyses": len(results), "n_tables": len(all_tables),
        "n_figures": sum(len(r.figures) for r in results),
        "loader_warnings": loaded.warnings,
        "profile_alerts": data_profile.alerts,
    }
