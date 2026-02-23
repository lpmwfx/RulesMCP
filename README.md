# Rules MCP Server

MCP server for AI coding rules — Python, JS, CSS, C++, Rust, Kotlin standards.

Serves the [Rules](https://github.com/lpmwfx/Rules) repository via Model Context Protocol.

## Install

```bash
pipx install git+https://github.com/lpmwfx/RulesMCP.git
```

## Register with Claude Code

```bash
claude mcp add -s user rules -- rules-mcp
```

## Tools

| Tool | Description |
|------|-------------|
| `search_rules` | Search rules by keyword (tags, concepts, keywords, title) |
| `get_rule` | Get full markdown content of a specific rule file |
| `get_context` | Get combined rules for given languages and topics |
| `get_learning_path` | Get rules in implementation order (phased) |
| `list_rules` | List available rule files by category |

## Categories

`global`, `project-files`, `automation`, `devops`, `ipc`, `platform-ux`, `python`, `js`, `css`, `cpp`, `rust`, `kotlin`

## License

EUPL-1.2
