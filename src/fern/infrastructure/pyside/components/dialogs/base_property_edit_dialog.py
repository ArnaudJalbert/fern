"""
Base dialog for editing a single property by type.

Subclass for each property type (Boolean, String, Status). Each provides
get_name() and type-specific data; the manager uses TYPE_KEY to dispatch.
"""

from __future__ import annotations

from PySide6.QtWidgets import QDialog, QWidget


class BasePropertyEditDialog(QDialog):
    """
    Base for type-specific property edit windows.

    Subclasses must set TYPE_KEY (e.g. "boolean", "string", "status") and
    implement get_name(). Status subclass also implements get_choices().
    """

    TYPE_KEY: str = "string"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

    def get_name(self) -> str:
        """Return the property display name. Subclasses must implement."""
        raise NotImplementedError
