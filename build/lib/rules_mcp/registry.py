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

    def find_by_file(self, file: str) -> dict | None:
        """Find a single entry by its file path."""
        for entry in self.entries:
            if entry.get("file") == file:
                return entry
        return None

    def learning_path(
        self,
        languages: list[str],
        phase: int | None = None,
    ) -> list[list[dict]]:
        """Return entries grouped by curated layer for given languages.

        Uses the 'layer' field from register.jsonl (1-6):
          1: Global foundations
          2: Project methodology
          3: Language core (types, structure, errors, naming)
          4: Language advanced (testing, tooling, platform)
          5: Infrastructure (automation, devops, ipc, platform-ux)
          6: Reference (READMEs, quick-refs)

        Only includes layers relevant to requested languages.
        If phase is given (1-based), return only that layer.
        """
        lang_set = {lang.lower() for lang in languages}
        # Always include global + project-files as foundation
        include_cats = lang_set | {"global", "project-files"}

        # Collect relevant entries
        relevant: list[dict] = []
        for e in self.entries:
            cat = e.get("category", "").lower()
            if cat in include_cats:
                relevant.append(e)

        if not relevant:
            return []

        # Group by layer field (default layer 4 for entries without it)
        layer_groups: dict[int, list[dict]] = {}
        for e in relevant:
            layer = e.get("layer", 4)
            layer_groups.setdefault(layer, []).append(e)

        # Build sorted layers (ascending layer number)
        layers: list[list[dict]] = []
        for layer_num in sorted(layer_groups):
            entries = sorted(layer_groups[layer_num], key=lambda e: e.get("file", ""))
            layers.append(entries)

        if phase is not None and 1 <= phase <= len(layers):
            return [layers[phase - 1]]
        return layers


def _matches(token: str, field: str) -> bool:
    """Bidirectional substring match."""
    return token in field or field in token


def _score_entry(entry: dict, tokens: list[str]) -> int:
    """Score entry with weighted fields and bidirectional matching."""
    fields = _build_weighted_fields(entry)
    score = 0
    for token in tokens:
        for field_text, weight in fields:
            if _matches(token, field_text):
                score += weight
    return score


def _build_weighted_fields(entry: dict) -> list[tuple[str, int]]:
    """Build (text, weight) pairs from entry fields."""
    fields: list[tuple[str, int]] = []
    # File path (weight 3) — matches "types" in "python/types.md"
    fields.append((entry.get("file", "").lower(), 3))
    # Title (weight 3)
    fields.append((entry.get("title", "").lower(), 3))
    # Subtitle (weight 1)
    fields.append((entry.get("subtitle", "").lower(), 1))
    # Tags (weight 2 each)
    for tag in entry.get("tags", []):
        fields.append((tag.lower(), 2))
    # Concepts (weight 2 each)
    for concept in entry.get("concepts", []):
        fields.append((concept.lower(), 2))
    # Keywords (weight 1 each)
    for kw in entry.get("keywords", []):
        fields.append((kw.lower(), 1))
    # Category (weight 1)
    fields.append((entry.get("category", "").lower(), 1))
    return fields
