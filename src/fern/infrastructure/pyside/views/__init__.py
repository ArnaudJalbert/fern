"""
PySide6 view classes for the Fern application.

This package contains all screen-level views: the main window, welcome flow,
and vault flow (database list, pages list, editor). Re-exported here so
callers can use::

    from fern.infrastructure.pyside.views import FernView, MainWindow, ...
"""

from .base import FernView
from .database_view import DatabaseView
from .editor_view import EditorView
from .main_window import MainWindow
from .pages_view import PagesView
from .vault_view import VaultView
from .welcome_page import WelcomePage

__all__ = [
    "DatabaseView",
    "EditorView",
    "FernView",
    "MainWindow",
    "PagesView",
    "VaultView",
    "WelcomePage",
]
