"""Application-layer errors raised by use cases.

Use cases raise specific errors; the controller catches the concrete type
and handles (e.g. return failure result, show message).
"""

from fern.application.errors.page_errors import PageNotFoundError
from fern.application.errors.property_errors import (
    PropertyAlreadyExistsError,
    PropertyAlreadyExistsOnPageError,
    PropertyNotFoundError,
    PropertyNotFoundOnPageError,
)
from fern.application.errors.vault_errors import VaultNotFoundError

__all__ = [
    "VaultNotFoundError",
    "PageNotFoundError",
    "PropertyNotFoundError",
    "PropertyAlreadyExistsError",
    "PropertyAlreadyExistsOnPageError",
    "PropertyNotFoundOnPageError",
]
