from __future__ import annotations

from pathlib import Path

from git import Repo
from platformdirs import user_cache_dir

REPO_URL = "https://github.com/lpmwfx/Rules.git"
CACHE_DIR = Path(user_cache_dir("rules-mcp")) / "Rules"


def ensure_repo() -> Path:
    """Clone repo if missing, pull if present. Return repo path."""
    if (CACHE_DIR / ".git").is_dir():
        repo = Repo(CACHE_DIR)
        repo.remotes.origin.pull()
    else:
        CACHE_DIR.parent.mkdir(parents=True, exist_ok=True)
        Repo.clone_from(REPO_URL, CACHE_DIR)
    return CACHE_DIR
