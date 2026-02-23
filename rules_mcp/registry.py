from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Registry:
    """In-memory index of register.jsonl entries."""

    entries: list[dict] = field(default_factory=list)

    def load(self, repo_path: Path) -> None:
        """Load register.jsonl from repo into memory."""
        jsonl_path = repo_path / "register.jsonl"
        self.entries = []
        with jsonl_path.open() as fh:
            for line in fh:
                line = line.strip()
                if line:
                    self.entries.append(json.loads(line))

    def search(self, query: str, category: str | None = None, limit: int = 10) -> list[dict]:
        """Search entries by query tokens against tags, concepts, keywords, title."""
        tokens = query.lower().split()
        if not tokens:
            return []

        scored: list[tuple[int, dict]] = []
        for entry in self.entries:
            if category and entry.get("category") != category:
                continue
            score = _score_entry(entry, tokens)
            if score > 0:
                scored.append((score, entry))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [entry for _, entry in scored[:limit]]

    def list_files(self, category: str | None = None) -> list[dict]:
        """List entries, optionally filtered by category."""
        if category:
            return [e for e in self.entries if e.get("category") == category]
        return list(self.entries)

    def categories(self) -> list[str]:
        """Return unique categories."""
        return sorted({e.get("category", "") for e in self.entries})

    def learning_path(
        self,
        languages: list[str],
        phase: int | None = None,
    ) -> list[list[dict]]:
        """Return entries in topological layers for given languages.

        Layers are ordered: foundational first, dependent later.
        Uses referenced-by count to rank importance.
        If phase is given (1-based), return only that layer.
        """
        lang_set = {lang.lower() for lang in languages}
        # Always include global and project-files as foundational
        include_cats = lang_set | {"global", "project-files"}
        by_file = {e["file"]: e for e in self.entries}

        # Collect relevant files
        relevant: set[str] = set()
        for e in self.entries:
            cat = e.get("category", "").lower()
            if cat in include_cats:
                relevant.add(e["file"])

        # Count how many relevant files reference each file
        referenced_by: dict[str, int] = {f: 0 for f in relevant}
        for f in relevant:
            entry = by_file[f]
            cat = f.split("/")[0] if "/" in f else ""
            for ref in entry.get("refs", []):
                full_ref = f"{cat}/{ref}" if "/" not in ref else ref
                if full_ref in relevant:
                    referenced_by[full_ref] = referenced_by.get(full_ref, 0) + 1

        # Score: referenced_by count + bonus for rules/banned markers
        scores: dict[str, int] = {}
        for f in relevant:
            entry = by_file[f]
            ref_score = referenced_by.get(f, 0)
            rule_count = len(entry.get("rules", []))
            banned_count = len(entry.get("banned", []))
            has_examples = 1 if entry.get("has_examples") else 0
            scores[f] = ref_score * 3 + rule_count + banned_count + has_examples

        # Sort by score descending, split into layers
        sorted_files = sorted(relevant, key=lambda f: scores.get(f, 0), reverse=True)
        if not sorted_files:
            return []

        max_score = scores[sorted_files[0]]
        layers: list[list[dict]] = [[], [], [], []]
        for f in sorted_files:
            s = scores.get(f, 0)
            entry = by_file.get(f)
            if entry is None:
                continue
            ratio = s / max_score if max_score > 0 else 0
            if ratio >= 0.6:
                layers[0].append(entry)
            elif ratio >= 0.3:
                layers[1].append(entry)
            elif ratio > 0:
                layers[2].append(entry)
            else:
                layers[3].append(entry)

        # Remove empty layers, sort within each layer
        layers = [
            sorted(layer, key=lambda e: e.get("file", ""))
            for layer in layers
            if layer
        ]

        if phase is not None and 1 <= phase <= len(layers):
            return [layers[phase - 1]]
        return layers


def _score_entry(entry: dict, tokens: list[str]) -> int:
    """Score an entry by how many tokens match searchable fields."""
    searchable = _build_searchable(entry)
    score = 0
    for token in tokens:
        for field_text in searchable:
            if token in field_text:
                score += 1
                break
    return score


def _build_searchable(entry: dict) -> list[str]:
    """Build lowercase searchable strings from entry fields."""
    parts: list[str] = []
    parts.append(entry.get("title", "").lower())
    parts.append(entry.get("subtitle", "").lower())
    for tag in entry.get("tags", []):
        parts.append(tag.lower())
    for concept in entry.get("concepts", []):
        parts.append(concept.lower())
    for kw in entry.get("keywords", []):
        parts.append(kw.lower())
    parts.append(entry.get("category", "").lower())
    return parts
