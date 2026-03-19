"""Vault-related controller errors."""

from pathlib import Path


class VaultNotFoundError(Exception):
    """Raised when the vault path is invalid or the vault cannot be opened."""

    def __init__(self, path: Path, message: str | None = None) -> None:
        self.path = path
        super().__init__(message or f"Vault not found at {path}")
