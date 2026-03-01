from __future__ import annotations

import time
from pathlib import Path

from fastmcp import FastMCP

from rules_mcp.registry import Registry
from rules_mcp.repo import ensure_repo

mcp = FastMCP(
    "rules",
    instructions="AI coding rules lookup — Python, JS, CSS, C++, Rust, Kotlin standards. Call help() to get started.",
)

_registry = Registry()
_repo_path: Path | None = None
_last_pull: float = 0.0
_PULL_TTL = 3600.0  # re-pull at most once per hour


def _ensure_loaded() -> Path:
    """Ensure repo is cloned and registry is loaded. Re-pulls at most once per hour."""
    global _repo_path, _last_pull
    now = time.monotonic()
    if _repo_path is None or (now - _last_pull) > _PULL_TTL:
        _repo_path = ensure_repo()
        _registry.load(_repo_path)
        _last_pull = now
    return _repo_path


@mcp.tool()
def help() -> str:
    """Get started with the Rules MCP server. Shows available tools, categories, and quick start examples."""
    _ensure_loaded()

    # Dynamic stats
    total_rules = len(_registry.entries)
    cats = _registry.categories()
    rule_count = sum(len(e.get("rules", [])) for e in _registry.entries)
    banned_count = sum(len(e.get("banned", [])) for e in _registry.entries)

    cat_list = ", ".join(cats)

    return f"""# Rules MCP — AI coding standards lookup

**{total_rules} rules** across **{len(cats)} categories** ({rule_count} RULE markers, {banned_count} BANNED markers)

## Tools

| Tool | Purpose | Example |
|------|---------|---------|
| `help()` | This overview | — |
| `search_rules(query)` | Find rules by keyword | `search_rules("testing")` |
| `get_rule(file)` | Read full rule content | `get_rule("python/types.md")` |
| `get_context(languages)` | All rules for languages | `get_context(["python", "js"])` |
| `get_learning_path(languages)` | Phased reading order | `get_learning_path(["cpp"], phase=1)` |
| `list_rules(category)` | Browse available rules | `list_rules("rust")` |
| `get_related(file)` | Follow edges to related rules | `get_related("python/types.md")` |

## Quick start

- **App architecture / folder layout** → `get_context(["global"])`
- **New project setup** → `get_context(["global", "project-files"])`
- **Learn a language's rules** → `get_learning_path(["python"], phase=1)`
- **Search a topic** → `search_rules("error handling")`
- **Browse everything** → `list_rules()`

## Categories

{cat_list}"""


@mcp.tool()
def search_rules(
    query: str, category: str | None = None, limit: int = 10
) -> str:
    """Search rules by keyword. Matches tags, concepts, keywords, title.

    Args:
        query: Search terms (e.g. "ownership threading types")
        category: Filter by category (python, js, css, cpp, rust, kotlin, global, project-files, automation, devops, ipc, platform-ux)
        limit: Max results (default 10)
    """
    _ensure_loaded()
    results = _registry.search(query, category=category, limit=limit)
    if not results:
        return "No matching rules found."

    lines: list[str] = []
    for entry in results:
        file = entry.get("file", "")
        title = entry.get("title", "")
        tags = ", ".join(entry.get("tags", [])[:5])
        lines.append(f"- **{file}**: {title}")
        if tags:
            lines.append(f"  tags: {tags}")
    return "\n".join(lines)


@mcp.tool()
def get_rule(file: str) -> str:
    """Get full markdown content of a specific rule file.

    Args:
        file: Path relative to repo root (e.g. "python/types.md")
    """
    repo_path = _ensure_loaded()
    target = repo_path / file
    if not target.is_file():
        return f"File not found: {file}"
    return target.read_text(encoding="utf-8")


@mcp.tool()
def get_context(
    languages: list[str], topics: list[str] | None = None
) -> str:
    """Get combined rules context for given languages and topics.

    Args:
        languages: Language categories (e.g. ["python", "js"])
        topics: Optional concept filter (e.g. ["types", "testing"])
    """
    repo_path = _ensure_loaded()
    topic_set = {t.lower() for t in topics} if topics else set()
    lang_set = {lang.lower() for lang in languages}

    matched: list[dict] = []
    for entry in _registry.entries:
        cat = entry.get("category", "").lower()
        concepts = {c.lower() for c in entry.get("concepts", [])}
        tags = {t.lower() for t in entry.get("tags", [])}

        if cat in lang_set:
            matched.append(entry)
        elif topic_set and (concepts & topic_set or tags & topic_set):
            matched.append(entry)

    if not matched:
        return "No rules found for the given languages/topics."

    sections: list[str] = []
    for entry in matched:
        file_path = repo_path / entry.get("file", "")
        if not file_path.is_file():
            continue
        content = file_path.read_text(encoding="utf-8")
        rules = entry.get("rules", [])
        banned = entry.get("banned", [])

        header = f"## {entry.get('file', '')}"
        sections.append(header)
        if rules:
            sections.append("**RULES:** " + " | ".join(rules))
        if banned:
            sections.append("**BANNED:** " + " | ".join(banned))
        sections.append(content)
        sections.append("---")

    return "\n\n".join(sections)


@mcp.tool()
def get_learning_path(
    languages: list[str], phase: int | None = None
) -> str:
    """Get rules in implementation order — foundational first, dependent later.

    Returns rules grouped in phases (layers). Phase 1 = read first,
    Phase 2 = read next, etc. Avoids rule overflow by giving only
    what's relevant for the current stage.

    Args:
        languages: Language categories (e.g. ["python", "js"])
        phase: Optional 1-based phase number. Omit for full path overview.
    """
    _ensure_loaded()
    layers = _registry.learning_path(languages, phase=phase)
    if not layers:
        return "No rules found for the given languages."

    sections: list[str] = []
    for i, layer in enumerate(layers, start=1):
        phase_num = phase if phase else i
        sections.append(f"## Phase {phase_num}: {len(layer)} rules")
        for entry in layer:
            f = entry.get("file", "")
            title = entry.get("title", "")
            rules = entry.get("rules", [])
            banned = entry.get("banned", [])
            markers: list[str] = []
            if rules:
                markers.append(f"RULES: {len(rules)}")
            if banned:
                markers.append(f"BANNED: {len(banned)}")
            marker_str = f" [{', '.join(markers)}]" if markers else ""
            sections.append(f"- {f}: {title}{marker_str}")
        sections.append("")

    total = sum(len(layer) for layer in layers)
    total_phases = phase if phase else len(layers)
    sections.insert(
        0,
        f"# Learning Path: {', '.join(languages)} — {total} rules in {total_phases} phases\n",
    )
    return "\n".join(sections)


@mcp.tool()
def get_related(file: str) -> str:
    """Get related rules by following graph edges from a specific rule file.

    Shows requires, required_by, feeds, fed_by, and related edges.

    Args:
        file: Path relative to repo root (e.g. "python/types.md")
    """
    _ensure_loaded()
    entry = _registry.find_by_file(file)
    if not entry:
        return f"File not found: {file}"

    edges = entry.get("edges", {})
    if not any(edges.get(k, []) for k in ("requires", "required_by", "feeds", "fed_by", "related")):
        return f"No edges found for {file}"

    lines: list[str] = [f"# Edges for {file}\n"]

    labels = {
        "requires": "Depends on (must read first)",
        "required_by": "Depended on by",
        "feeds": "Feeds into",
        "fed_by": "Fed by",
        "related": "Related",
    }

    for edge_type, label in labels.items():
        targets = edges.get(edge_type, [])
        if not targets:
            continue
        lines.append(f"## {label}")
        for target in targets:
            target_entry = _registry.find_by_file(target)
            title = target_entry.get("title", "") if target_entry else "(not found)"
            lines.append(f"- {target}: {title}")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
def list_rules(category: str | None = None) -> str:
    """List available rule files, optionally filtered by category.

    Args:
        category: Filter by category (python, js, css, cpp, rust, kotlin, global, project-files, automation, devops, ipc, platform-ux). Omit for all.
    """
    _ensure_loaded()

    if category:
        entries = _registry.list_files(category=category)
    else:
        entries = _registry.list_files()

    if not entries:
        available = ", ".join(_registry.categories())
        return f"No rules found. Available categories: {available}"

    lines: list[str] = []
    current_cat = ""
    for entry in entries:
        cat = entry.get("category", "")
        if cat != current_cat:
            current_cat = cat
            lines.append(f"\n### {cat}")
        file = entry.get("file", "")
        title = entry.get("title", "")
        lines.append(f"- {file}: {title}")

    return "\n".join(lines)
