"""Controller for managing recent vaults list.

This controller handles operations related to the list of recently opened vaults,
independent of any specific vault. It uses the RecentVaultsRepository to persist
the list to disk.
"""

from __future__ import annotations

from pathlib import Path

from fern.application.repositories.recent_vaults_repository import (
    RecentVaultsRepository,
)
from fern.application.use_cases.add_recent_vault import AddRecentVaultUseCase
from fern.application.use_cases.get_recent_vaults import GetRecentVaultsUseCase
from fern.application.use_cases.remove_recent_vault import RemoveRecentVaultUseCase
from fern.infrastructure.controller.errors import (
    RecentVaultNotFoundError,
    RecentVaultsPersistenceError,
)


class RecentVaultsController:
    """Controller for recent vaults operations.

    This controller manages the list of recently opened vaults. It does not
    require a specific vault path and can be used independently of any
    open vault session.
    """

    def __init__(self, repository: RecentVaultsRepository) -> None:
        """Initialize the recent vaults controller.

        Args:
            repository: The repository for persisting/retrieving recent vaults.
        """
        self._repository = repository
        self._get_use_case = GetRecentVaultsUseCase(repository)
        self._add_use_case = AddRecentVaultUseCase(repository)
        self._remove_use_case = RemoveRecentVaultUseCase(repository)

    def get_recent_vaults(self) -> list[Path]:
        """Return the list of recently opened vaults (most recent first).

        Returns:
            A list of Path objects representing the recent vaults.

        Raises:
            RecentVaultsPersistenceError: If there is an error reading the recent vaults file.
        """
        try:
            output = self._get_use_case.execute(GetRecentVaultsUseCase.Input())
            return [Path(p) for p in output.paths]
        except Exception as error:
            raise RecentVaultsPersistenceError(
                message=f"Failed to load recent vaults: {error}"
            ) from error

    def add_recent_vault(self, vault_path: Path) -> None:
        """Add a vault to the recent list.

        The vault is added to the front of the list and duplicates are removed.
        The list is truncated to the maximum size (typically 10 entries).

        Args:
            vault_path: The path to the vault to add.

        Raises:
            RecentVaultsPersistenceError: If there is an error saving the recent vaults file.
        """
        try:
            self._add_use_case.execute(
                AddRecentVaultUseCase.Input(path=vault_path.resolve())
            )
        except Exception as error:
            raise RecentVaultsPersistenceError(
                message=f"Failed to save recent vault: {error}"
            ) from error

    def remove_recent_vault(self, vault_path: Path) -> None:
        """Remove a vault from the recent list.

        Args:
            vault_path: The path to the vault to remove.

        Raises:
            RecentVaultNotFoundError: If the vault is not in the recent list.
            RecentVaultsPersistenceError: If there is an error saving the recent vaults file.
        """
        try:
            self._remove_use_case.execute(
                RemoveRecentVaultUseCase.Input(path=vault_path.resolve())
            )
        except Exception as error:
            # Check if it's a "not found" error from the use case
            if "not in recent list" in str(error).lower():
                raise RecentVaultNotFoundError(
                    path=vault_path, message=str(error)
                ) from error
            raise RecentVaultsPersistenceError(
                message=f"Failed to remove recent vault: {error}"
            ) from error
