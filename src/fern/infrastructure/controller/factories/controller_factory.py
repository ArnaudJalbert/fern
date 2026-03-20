"""Factory that builds controller instances with default dependencies."""

from pathlib import Path

from fern.infrastructure.controller.factories.page_repository_factory import (
    PageRepositoryFactory,
)
from fern.infrastructure.controller.recent_vaults_controller import (
    RecentVaultsController,
)
from fern.infrastructure.controller.vault_controller import VaultController
from fern.interface_adapters.repositories.filesystem_vault_repository import (
    FilesystemVaultRepository,
)
from fern.interface_adapters.repositories.json_recent_vaults_repository import (
    JsonRecentVaultsRepository,
)
from fern.interface_adapters.repositories.vault_database_repository import (
    VaultDatabaseRepository,
)


class ControllerFactory:
    """Builds controller instances with default dependencies."""

    # Cache for vault controllers keyed by vault path
    _vault_controller_cache: dict[Path, VaultController] = {}
    # Singleton instance of RecentVaultsController
    _recent_vaults_controller: RecentVaultsController | None = None

    @classmethod
    def create_vault_controller(cls, vault_path: Path) -> VaultController:
        """Create and return a VaultController bound to the given vault path.

        Uses a cache to ensure only one instance exists per vault path.
        """
        # Normalize the path for consistent caching
        normalized_path = vault_path.resolve()

        # Check cache first
        if normalized_path in cls._vault_controller_cache:
            return cls._vault_controller_cache[normalized_path]

        # Create new controller
        vault_repository = FilesystemVaultRepository(normalized_path)
        database_repository = VaultDatabaseRepository(normalized_path)
        page_repository_factory = PageRepositoryFactory(normalized_path)
        controller = VaultController(
            vault_path=normalized_path,
            vault_repository=vault_repository,
            database_repository=database_repository,
            page_repository_factory=page_repository_factory,
        )

        # Cache and return
        cls._vault_controller_cache[normalized_path] = controller
        return controller

    @classmethod
    def create_recent_vaults_controller(cls) -> RecentVaultsController:
        """Create and return a RecentVaultsController.

        Returns a singleton instance - only one controller is ever created.
        """
        if cls._recent_vaults_controller is None:
            repository = JsonRecentVaultsRepository()
            cls._recent_vaults_controller = RecentVaultsController(repository)
        return cls._recent_vaults_controller
