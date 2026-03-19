"""Filesystem implementation of RecentVaultsRepository.

Stores paths in a JSON file under the user's home directory (~/.fern/recent_vaults.json).
"""

import json
from pathlib import Path

from fern.application.repositories.recent_vaults_repository import (
    RecentVaultsRepository,
)

MAX_RECENT = 10


def _config_dir() -> Path:
    """Return the Fern config directory (e.g. ~/.fern)."""
    return Path.home() / ".fern"


def _recent_file() -> Path:
    """Return the path to the recent vaults JSON file."""
    return _config_dir() / "recent_vaults.json"


class JsonRecentVaultsRepository(RecentVaultsRepository):
    """Persist recent vaults to a JSON file on disk."""

    def get(self) -> list[Path]:
        """Return list of recent vault paths (most recent first), up to MAX_RECENT."""
        path = _recent_file()
        if not path.is_file():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            out = [Path(p) for p in (data or []) if isinstance(p, str)]
            return out[:MAX_RECENT]
        except (json.JSONDecodeError, OSError):
            return []

    def add(self, vault_path: Path) -> None:
        """Prepend vault path to the recent list (deduplicating) and persist to disk."""
        vault_path = vault_path.resolve()
        recent = [p for p in self.get() if p != vault_path]
        recent.insert(0, vault_path)
        recent = recent[:MAX_RECENT]
        _config_dir().mkdir(parents=True, exist_ok=True)
        _recent_file().write_text(
            json.dumps([str(p) for p in recent], indent=2),
            encoding="utf-8",
        )

    def remove(self, vault_path: Path) -> None:
        """Remove a path from the recent list and persist to disk."""
        vault_path = vault_path.resolve()
        recent = [p for p in self.get() if p != vault_path]
        _config_dir().mkdir(parents=True, exist_ok=True)
        _recent_file().write_text(
            json.dumps([str(p) for p in recent], indent=2),
            encoding="utf-8",
        )
