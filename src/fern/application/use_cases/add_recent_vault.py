"""Use case for adding a vault to the recent list."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fern.application.repositories.recent_vaults_repository import (
    RecentVaultsRepository,
)


class AddRecentVaultUseCase:
    """Add a vault to the recent list."""

    @dataclass(frozen=True)
    class Input:
        """Input containing the vault path to add."""

        path: Path

    def __init__(self, repository: RecentVaultsRepository) -> None:
        """Initialize the use case with the recent vaults repository.

        Args:
            repository: The repository for persisting recent vault paths.
        """
        self._repository = repository

    def execute(self, input_data: Input) -> None:
        """Add the vault path to the recent list.

        Args:
            input_data: The input containing the vault path to add.
        """
        self._repository.add(input_data.path.resolve())
