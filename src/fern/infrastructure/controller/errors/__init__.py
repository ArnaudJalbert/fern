"""Controller errors package.

Re-exports all controller-specific error classes for convenient imports.
"""

from .page_errors import (
    PageNotFoundError,
    PropertyAlreadyExistsOnPageError,
    PropertyNotFoundOnPageError,
)
from .property_errors import (
    PropertyAlreadyExistsError,
    PropertyNotFoundError,
)
from .recent_vaults_errors import (
    RecentVaultNotFoundError,
    RecentVaultsError,
    RecentVaultsPersistenceError,
)
from .vault_errors import VaultNotFoundError

__all__ = [
    "VaultNotFoundError",
    "PageNotFoundError",
    "PropertyNotFoundError",
    "PropertyAlreadyExistsError",
    "PropertyAlreadyExistsOnPageError",
    "PropertyNotFoundOnPageError",
    "RecentVaultsError",
    "RecentVaultNotFoundError",
    "RecentVaultsPersistenceError",
]
