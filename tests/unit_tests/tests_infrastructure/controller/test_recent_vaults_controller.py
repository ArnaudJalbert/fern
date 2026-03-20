"""Unit tests for RecentVaultsController."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from fern.application.repositories.recent_vaults_repository import (
    RecentVaultsRepository,
)
from fern.infrastructure.controller.errors import (
    RecentVaultNotFoundError,
    RecentVaultsPersistenceError,
)
from fern.infrastructure.controller.recent_vaults_controller import (
    RecentVaultsController,
)


def test_get_recent_vaults_success() -> None:
    """get_recent_vaults returns list of paths when repository succeeds."""
    repo = MagicMock(spec=RecentVaultsRepository)
    paths = [Path("/vault1"), Path("/vault2"), Path("/vault3")]
    repo.get.return_value = paths

    controller = RecentVaultsController(repo)
    result = controller.get_recent_vaults()

    assert result == paths
    repo.get.assert_called_once()


def test_get_recent_vaults_empty() -> None:
    """get_recent_vaults returns empty list when no recent vaults."""
    repo = MagicMock(spec=RecentVaultsRepository)
    repo.get.return_value = []

    controller = RecentVaultsController(repo)
    result = controller.get_recent_vaults()

    assert result == []
    repo.get.assert_called_once()


def test_get_recent_vaults_persistence_error() -> None:
    """get_recent_vaults raises RecentVaultsPersistenceError on repository failure."""
    repo = MagicMock(spec=RecentVaultsRepository)
    repo.get.side_effect = OSError("Disk error")

    controller = RecentVaultsController(repo)

    with pytest.raises(RecentVaultsPersistenceError) as exc_info:
        controller.get_recent_vaults()

    assert "Failed to load recent vaults" in str(exc_info.value)
    repo.get.assert_called_once()


def test_add_recent_vault_success() -> None:
    """add_recent_vault calls repository.add with resolved path."""
    repo = MagicMock(spec=RecentVaultsRepository)
    vault_path = Path("/my/vault")

    controller = RecentVaultsController(repo)
    controller.add_recent_vault(vault_path)

    repo.add.assert_called_once_with(vault_path.resolve())


def test_add_recent_vault_persistence_error() -> None:
    """add_recent_vault raises RecentVaultsPersistenceError on failure."""
    repo = MagicMock(spec=RecentVaultsRepository)
    repo.add.side_effect = OSError("Cannot write")

    controller = RecentVaultsController(repo)
    vault_path = Path("/my/vault")

    with pytest.raises(RecentVaultsPersistenceError) as exc_info:
        controller.add_recent_vault(vault_path)

    assert "Failed to save recent vault" in str(exc_info.value)
    repo.add.assert_called_once_with(vault_path.resolve())


def test_remove_recent_vault_success() -> None:
    """remove_recent_vault calls repository.remove with resolved path."""
    repo = MagicMock(spec=RecentVaultsRepository)
    vault_path = Path("/my/vault")

    controller = RecentVaultsController(repo)
    controller.remove_recent_vault(vault_path)

    repo.remove.assert_called_once_with(vault_path.resolve())


def test_remove_recent_vault_not_found() -> None:
    """remove_recent_vault raises RecentVaultNotFoundError when vault not in list."""
    repo = MagicMock(spec=RecentVaultsRepository)
    repo.remove.side_effect = ValueError("Vault not in recent list")

    controller = RecentVaultsController(repo)
    vault_path = Path("/my/vault")

    with pytest.raises(RecentVaultNotFoundError) as exc_info:
        controller.remove_recent_vault(vault_path)

    assert vault_path == exc_info.value.path
    assert "not in recent list" in str(exc_info.value).lower()
    repo.remove.assert_called_once_with(vault_path.resolve())


def test_remove_recent_vault_persistence_error() -> None:
    """remove_recent_vault raises RecentVaultsPersistenceError on other failures."""
    repo = MagicMock(spec=RecentVaultsRepository)
    repo.remove.side_effect = OSError("Cannot write")

    controller = RecentVaultsController(repo)
    vault_path = Path("/my/vault")

    with pytest.raises(RecentVaultsPersistenceError) as exc_info:
        controller.remove_recent_vault(vault_path)

    assert "Failed to remove recent vault" in str(exc_info.value)
    repo.remove.assert_called_once_with(vault_path.resolve())
