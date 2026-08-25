"""Thin wrapper around pypandoc — the actual conversion calls, isolated
here so the rest of the codebase never imports pypandoc directly.

Uses ``pypandoc-binary``: pandoc ships inside the wheel, no system install
needed (verified in the M0.5 spike — pandoc 3.9, no ``apt``/``brew`` step).
Pandoc itself is GPL-2.0+; invoking it as a subprocess (which is all
pypandoc does) does not extend that license to this codebase.
"""

from __future__ import annotations

from pathlib import Path

import pypandoc


def markdown_to_docx(
    markdown_path: str | Path,
    output_path: str | Path,
    reference_docx: str | Path,
    toc: bool = True,
    toc_depth: int = 3,
    toc_title: str | None = None,
) -> Path:
    """Convert a Markdown file to .docx using ``reference_docx`` for
    styles/margins/fonts. Produces a real Word TOC field when ``toc=True``
    (page numbers populate when the file is next opened in Word/LibreOffice).
    ``toc_title`` localizes the TOC heading (pandoc defaults to English
    "Table of Contents" otherwise, wrong for a Turkish report)."""
    extra_args = ["--standalone", f"--reference-doc={reference_docx}"]
    if toc:
        extra_args += ["--toc", f"--toc-depth={toc_depth}"]
        if toc_title:
            # Two separate argv tokens, not one "-V toc-title=..." string —
            # pandoc's arg parser does not split a glued "-V value" token,
            # so passing it as a single extra_args entry is silently a no-op.
            extra_args += ["-V", f"toc-title={toc_title}"]
    pypandoc.convert_file(str(markdown_path), "docx", outputfile=str(output_path), extra_args=extra_args)
    return Path(output_path)


def markdown_to_html(
    markdown_path: str | Path,
    output_path: str | Path,
    toc: bool = True,
    toc_depth: int = 3,
    toc_title: str | None = None,
) -> Path:
    """Convert a Markdown file to a single self-contained HTML file (images
    embedded as data URIs) — the fallback for readers with no Office
    program at all. Always has a filled, clickable TOC."""
    extra_args = ["--standalone", "--embed-resources"]
    if toc:
        extra_args += ["--toc", f"--toc-depth={toc_depth}"]
        if toc_title:
            # Two separate argv tokens, not one "-V toc-title=..." string —
            # pandoc's arg parser does not split a glued "-V value" token,
            # so passing it as a single extra_args entry is silently a no-op.
            extra_args += ["-V", f"toc-title={toc_title}"]
    pypandoc.convert_file(str(markdown_path), "html", outputfile=str(output_path), extra_args=extra_args)
    return Path(output_path)
