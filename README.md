# statistical-reporting

A Claude Code skills toolkit for statistical analysis and reporting.

This repo has no application code — it's a set of [Claude Code Agent Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills)
and slash commands under `.claude/`, ready to use in any Claude Code session opened against
this repo. See [`.claude/skills/README.md`](.claude/skills/README.md) for what's installed and
where each skill came from.

## Highlights

- **`statistical-analysis`** — data profiling, assumption checks, automatic method selection
  (t-test/ANOVA/regression/SEM), and APA-style report generation.
- 31 data-analytics skills covering EDA, data quality, cohort/funnel/segmentation analysis,
  A/B testing, dashboards, and stakeholder communication.
- **`diagram-design`** — 39 editorial diagram types (architecture, ER, sequence, Gantt, etc.)
  rendered as self-contained HTML/SVG.
- **`find-skill`** / **`create-skill-file`** — discover and install more skills, or write new
  ones, from inside a session.
- **`stop-slop`** — cleans AI writing tells out of drafted prose.
- **`mcp-analytics`** — optional hosted MCP server for commissioning statistical reports
  (`.mcp.json`; requires a free account at [mcpanalytics.ai](https://mcpanalytics.ai)).

## Usage

Open a Claude Code session pointed at this repo and just ask for the analysis you need —
skills trigger automatically based on the request (e.g. "run a statistical analysis on this
CSV", "find me a skill for X", "draw an ER diagram of this schema").
