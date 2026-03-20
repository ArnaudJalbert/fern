"""Use case for removing a vault from the recent list."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fern.application.repositories.recent_vaults_repository import (
    RecentVaultsRepository,
)


class RemoveRecentVaultUseCase:
    """Remove a vault from the recent list."""

    def __init__(self, repository: RecentVaultsRepository) -> None:
        """Initialize the use case with the recent vaults repository.

        Args:
            repository: The repository for persisting recent vault paths.
        """
        self._repository = repository

    @dataclass(frozen=True)
    class Input:
        """Input containing the vault path to remove."""

        path: Path

    @dataclass(frozen=True)
    class Output:
        """No output data."""

        pass

    def execute(self, input_data: Input) -> None:
        """Remove the vault path from the recent list.

        Args:
            input_data: The input containing the vault path to remove.
        """
        self._repository.remove(input_data.path.resolve())
