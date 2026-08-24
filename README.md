# statistical-reporting

Excel/CSV in, a finished Word report out — no Microsoft Office, SPSS, or R
installation required to *produce* the report (only to open the `.docx`
afterward, and any office suite works, including free ones).

This repo is two things:

1. **`statrep`** — a Python CLI (`src/statrep/`) that profiles your data,
   runs the right statistical tests (with automatic method-switching when
   assumptions fail — e.g. t-test → Mann-Whitney U when normality fails),
   and assembles a bilingual (Turkish/English) Word report with APA-style
   tables, 300dpi figures, a working table of contents, an Excel export of
   every table, and SPSS syntax you can run in your own SPSS to verify the
   results.
2. A set of [Claude Code Agent Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills)
   under `.claude/` for statistical analysis, data-analytics, and diagram
   work inside a Claude Code session. See
   [`.claude/skills/README.md`](.claude/skills/README.md) for what's
   installed and where each skill came from.

## Quick start

```bash
git clone https://github.com/AlperenAydiner/statistical-reporting
cd statistical-reporting
./setup.sh                     # Windows: .\setup.ps1
source .venv/bin/activate

statrep build --input your-data.xlsx --lang tr
# -> output/report.docx, report.html, tables.xlsx, analysis.sps, manifest.json
```

`setup.sh` provisions everything into `.venv/` — it never touches your
system Python. It also probes for optional extras (R, LibreOffice) and
tells you plainly what's missing rather than failing silently; re-run the
probe any time with `statrep doctor`.

See [`examples/sample-report/`](examples/sample-report/) for a report
generated from [`tests/fixtures/likert_tr.xlsx`](tests/fixtures/likert_tr.xlsx)
— open `report.docx` to see the actual output before running anything
yourself.

### What you don't need installed

| | |
|---|---|
| Excel | Not needed — `.xlsx`/`.xls`/`.csv`/`.tsv` are read directly. |
| Word | Not needed to *produce* `report.docx` — [pandoc](https://pandoc.org) ships inside the `pypandoc-binary` pip package, no system install. |
| SPSS | Never needed — `analysis.sps` is a plain-text syntax file your own SPSS can run against your *original* data file to verify the results. |
| R | Optional — only used (if present) for methods Python doesn't cover well (SEM/HLM). |

The only real requirement to *open* the finished report is something that
reads `.docx`: Word, [LibreOffice](https://www.libreoffice.org/) (free),
Google Docs (free), or WPS. If none of those are available either, `statrep`
also writes `report.html` — a single self-contained file, images embedded,
that opens in any browser.

## Highlights

- **`statrep`** (this repo's own code) — the report-generation pipeline above.
- **`statistical-analysis`** skill — data profiling, assumption checks, automatic method
  selection (t-test/ANOVA/regression/SEM), and APA-style method references.
- 31 data-analytics skills covering EDA, data quality, cohort/funnel/segmentation analysis,
  A/B testing, dashboards, and stakeholder communication.
- **`diagram-design`** — 39 editorial diagram types (architecture, ER, sequence, Gantt, etc.)
  rendered as self-contained HTML/SVG.
- **`find-skill`** / **`create-skill-file`** — discover and install more skills, or write new
  ones, from inside a Claude Code session.
- **`stop-slop`** — cleans AI writing tells out of drafted prose.

## Status

v1 (M1) covers the Standard report tier: descriptive statistics, group
comparisons (t-test/Welch/Mann-Whitney/ANOVA/Kruskal-Wallis, assumption-routed),
correlation, and linear regression — in Turkish or English, ~15-25 pages
depending on your data. Shorter/longer tiers (Brief/Comprehensive/Thesis),
the business report template's full styling, SPSS variable-name mapping for
Turkish characters, and an R bridge for SEM/HLM are on the roadmap.

## Using the skills in a Claude Code session

Open a Claude Code session pointed at this repo and ask for the analysis you need —
skills trigger automatically based on the request (e.g. "run a statistical analysis on this
CSV", "find me a skill for X", "draw an ER diagram of this schema").
