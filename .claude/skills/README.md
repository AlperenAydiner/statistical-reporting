# Installed skills

The skills in this folder were installed from seven source repos:

## 1. [nimrodfisher/data-analytics-skills](https://github.com/nimrodfisher/data-analytics-skills)
31 data-analytics skills (EDA, data-quality checks, cohort/funnel/segmentation analysis,
A/B testing, dashboard/report generation, stakeholder communication, etc). The original repo
grouped them as `NN-category/skill-name/`; here they were copied flat into the
`.claude/skills/<skill-name>/` layout Claude Code expects. Two skills (`metric-reconciliation`,
`schema-mapper`) were duplicated near-verbatim across two categories — deduplicated, keeping the
data-quality-validation copy.

## 2. [Giro03k/claude-statistical-analysis-skill](https://github.com/Giro03k/claude-statistical-analysis-skill)
The `statistical-analysis` skill: data profiling, assumption checks, automatic method selection
(t-test/ANOVA/regression/SEM, etc), and APA-style report generation. The packaged `.zip`
distribution (a duplicate of the source files) was left out — the skill was installed from its
plain source files.

## 3. [hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop)
The `stop-slop` skill: removes predictable AI writing patterns (filler phrases, formulaic
structures, passive voice, em-dash overuse, generic "quotable" sentences, etc) from drafted or
edited text.

## 4. [YYH211/claude-meta-skill](https://github.com/YYH211/claude-meta-skill) — `create-skill-file`
This repo actually bundles 11 unrelated skills (a news summarizer, a FastGPT workflow generator,
a copyright-filing writer, etc). Only the one that's genuinely a "meta-skill" was installed —
`create-skill-file` (English version): a guide, templates, and good/bad examples for writing
high-quality `SKILL.md` files. The other 10 skills were intentionally left out.

## 5. [fockus/claude-skill-find-skill](https://github.com/fockus/claude-skill-find-skill) — `find-skill`
Search/install commands (`/find-skill`, `/install-skill`) drawing on 4800+ skills from 14
sources. By design this tool uses **user-global** (`$HOME/.claude/skills/find-skill/...`) paths
rather than project-scoped ones — so only its static files (SKILL.md, the update and install
scripts, the `/install-skill` command) were committed here; `cache/catalogue.json` (a generated,
not-committed file) and the optional SkillsMP API key will be created automatically on the first
real `/find-skill` call. Its official `install.sh` was not run automatically in that session
(blocked by the shell-script permission classifier) — it can be run manually with confirmation
if needed.

## 6. [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design)
The `diagram-design` skill: renders 39 editorial diagram types (architecture, flowchart,
sequence, ER, swimlane, timeline, Gantt, Sankey, UML class, DB schema, etc) as self-contained
HTML/SVG files; redraws .drawio/Mermaid sources; can pull brand tokens from a website. The
skill's real content lived at `skills/diagram-design/` in the source repo rather than the repo
root, and was copied from there into `.claude/skills/diagram-design/`. Its companion
`/doctor`, `/export-diagram`, `/import-drawio`, `/import-mermaid`, `/profile` commands were
added under `.claude/commands/` (their relative paths match this project's layout exactly).

## 7. [embeddedlayers/mcp-analytics](https://github.com/embeddedlayers/mcp-analytics)
Not a skill — a hosted MCP server (paid/credit-based SaaS at mcpanalytics.ai). Its connection
config was added to `.mcp.json` at the repo root:

```json
{
  "mcpServers": {
    "mcp-analytics": {
      "command": "npx",
      "args": ["-y", "mcp-remote@latest", "https://api.mcpanalytics.ai/auth0"]
    }
  }
}
```

On first use it opens a browser for OAuth sign-in at [mcpanalytics.ai](https://mcpanalytics.ai)
(free account, 500 welcome credits) — that step requires signing up, so it wasn't done
automatically and needs to be completed by the account owner.
