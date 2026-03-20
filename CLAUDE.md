# RulesMCP — CLAUDE.md

MCP server that exposes the coding rule library (`github.com/lpmwfx/Rules`) to Claude Code.

## What this server does

`rules-mcp` clones/pulls the Rules repo into `~/.cache/rules-mcp/Rules/` (max 1 pull/hour)
and serves rule lookups to the AI. This is what powers the `mcp__rules__*` tools in Claude Code.

## Tools exposed (MCP)

| Tool | Purpose |
|---|---|
| `help()` | Get started — shows categories, quick examples |
| `get_rule(file)` | Fetch full rule file content (e.g. `"rust/errors.md"`) |
| `search_rules(query)` | Weighted keyword search across all rules |
| `list_rules(category)` | List rules by category |
| `get_related(file)` | Get related rule files via graph edges |
| `get_context(file)` | Get rule + its requires/related files |
| `get_learning_path(topic)` | Get ordered learning path for a topic |

## Rule ID → file mapping

```
rust/errors/no-unwrap          →  rust/errors.md
rust/modules/no-sibling-coupling →  rust/modules.md
global/nesting                 →  global/nesting.md
uiux/tokens/no-hardcoded-color →  uiux/tokens.md
```

Rule: take first two path segments + `.md`

## Key files

| File | Purpose |
|---|---|
| `server.py` | FastMCP app, tool definitions, lazy `_ensure_loaded()` |
| `registry.py` | In-memory JSONL loader + weighted search |
| `repo.py` | Git clone/pull of lpmwfx/Rules into `~/.cache/rules-mcp/Rules/` |

## Installation

```bash
pip install git+https://github.com/lpmwfx/RulesMCP
```

MCP registration:
```bash
claude mcp add rules rules-mcp --scope user
```

## Startup rule

ALWAYS call `get_rule("global/startup.md")` at the start of every session
before reading project files or forming a plan.

## Relationship to other repos

- Rule content sourced from: `github.com/lpmwfx/Rules`
- Scanner enforcement via: `github.com/lpmwfx/RulesTools` + `github.com/lpmwfx/RulesToolsMCP`


---

<!-- LARS:START -->
<a href="https://lpmathiasen.com">
  <img src="https://carousel.lpmathiasen.com/carousel.svg?slot=3" alt="Lars P. Mathiasen"/>
</a>
<!-- LARS:END -->
