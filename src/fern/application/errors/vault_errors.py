"""Vault-related use case errors."""

from __future__ import annotations


class VaultNotFoundError(Exception):
    """Raised when the vault path is invalid or the vault cannot be opened."""

    def __init__(
        self,
        message: str | None = None,
        *,
        path: str | None = None,
    ) -> None:
        if message is not None:
            detail = message
        elif path is not None:
            detail = f"Vault not found or invalid: {path}"
        else:
            detail = "Invalid or missing vault."
        super().__init__(detail)
        self.message = detail
