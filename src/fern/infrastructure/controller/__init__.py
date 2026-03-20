"""Controller package - provides controllers, factory, and errors.

This package contains the infrastructure layer's controller components:
- VaultController: For operations on a specific vault
- RecentVaultsController: For managing the recent vaults list
- ControllerFactory: Creates controller instances with default dependencies
- errors: Controller-specific error classes
"""

# Re-export recent vaults use cases for UI convenience
# Import AppController and RecentVaultsPort from the sibling controller.py module
# Re-export recent vaults use cases for UI convenience
from fern.application.use_cases.add_recent_vault import AddRecentVaultUseCase
from fern.application.use_cases.get_recent_vaults import GetRecentVaultsUseCase
from fern.application.use_cases.open_vault import OpenVaultUseCase
from fern.application.use_cases.remove_recent_vault import RemoveRecentVaultUseCase
from fern.domain.entities import PropertyType
from fern.infrastructure.controller.errors.controller_errors import (
    PageNotFoundError,
    PropertyAlreadyExistsError,
    PropertyAlreadyExistsOnPageError,
    PropertyNotFoundError,
    PropertyNotFoundOnPageError,
    RecentVaultNotFoundError,
    RecentVaultsError,
    RecentVaultsPersistenceError,
    VaultNotFoundError,
)
from fern.infrastructure.controller.factories.controller_factory import (
    ControllerFactory,
)
from fern.infrastructure.controller.recent_vaults_controller import (
    RecentVaultsController,
)

from .vault_controller import VaultController

# Output types
VaultOutput = OpenVaultUseCase.Output
ChoiceOutput = OpenVaultUseCase.ChoiceOutput


# Utility functions
def default_value_for_type(type_key: str) -> object:
    """Return the default value for a property type key (e.g. False for boolean)."""
    return PropertyType.from_key(type_key).default_value_for_type()


def user_creatable_type_keys() -> list[str]:
    """Return type keys the user can choose from (excludes id/title)."""
    return [member.key() for member in PropertyType.user_creatable()]


__all__ = [
    # Controllers
    "VaultController",
    "RecentVaultsController",
    "ControllerFactory",
    # Errors
    "VaultNotFoundError",
    "PageNotFoundError",
    "PropertyNotFoundError",
    "PropertyAlreadyExistsError",
    "PropertyAlreadyExistsOnPageError",
    "PropertyNotFoundOnPageError",
    "RecentVaultsError",
    "RecentVaultNotFoundError",
    "RecentVaultsPersistenceError",
    # Use cases
    "AddRecentVaultUseCase",
    "GetRecentVaultsUseCase",
    "RemoveRecentVaultUseCase",
    # Output types and utilities
    "VaultOutput",
    "ChoiceOutput",
    "CreateRootPageOutput",
    "default_value_for_type",
    "user_creatable_type_keys",
]
