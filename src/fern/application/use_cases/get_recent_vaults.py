"""Use case for getting the list of recently opened vaults."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fern.application.repositories.recent_vaults_repository import (
    RecentVaultsRepository,
)


class GetRecentVaultsUseCase:
    """Get the list of recently opened vaults."""

    def __init__(self, repository: RecentVaultsRepository) -> None:
        """Initialize the use case with the recent vaults repository.

        Args:
            repository: The repository for loading recent vault paths.
        """
        self._repository = repository

    @dataclass(frozen=True)
    class Input:
        """No input required."""

        pass

    @dataclass(frozen=True)
    class Output:
        """Output containing the list of recent vault paths."""

        paths: list[Path]

    def execute(self, input_data: Input) -> Output:
        """Return the list of recent vault paths.

        Returns:
            Output containing the recent vault paths (most recent first).
        """
        paths = self._repository.get()
        return self.Output(paths=paths)
