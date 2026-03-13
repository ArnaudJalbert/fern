"""
PySide6 UI layer for the Fern application.

Contains views (main window, welcome, vault, database list, pages list, editor),
reusable components (Card, Table, MarkdownHighlighter), styles (QSS), and icons.
Import the main window and theme loader from here::

    from fern.infrastructure.pyside import MainWindow
    from fern.infrastructure.pyside.theme import load_global_stylesheet
"""

from fern.infrastructure.pyside.views import (
    DatabaseView,
    EditorView,
    FernView,
    MainWindow,
    PagesView,
    VaultView,
    WelcomePage,
)

__all__ = [
    "DatabaseView",
    "EditorView",
    "FernView",
    "MainWindow",
    "PagesView",
    "VaultView",
    "WelcomePage",
]
