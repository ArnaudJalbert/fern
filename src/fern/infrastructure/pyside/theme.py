"""
Load the global application stylesheet from multiple QSS files.

Styles are loaded from the pyside/styles/ directory in a fixed order: base first,
then feature-specific files (welcome, card, table, vault, editor). Later files
override earlier rules when the same selector is used.
"""

from pathlib import Path

from PySide6.QtWidgets import QApplication

# Load order: base first, then feature-specific (later files override when same selector).
_STYLE_FILES = (
    "base.qss",
    "splash.qss",
    "welcome.qss",
    "card.qss",
    "table.qss",
    "vault.qss",
    "editor.qss",
)


def load_global_stylesheet(app: QApplication) -> None:
    """
    Apply the global QSS to the application.

    Call once after creating QApplication. Reads all _STYLE_FILES from pyside/styles/
    and concatenates them into a single stylesheet.
    """
    styles_dir = Path(__file__).resolve().parent / "styles"
    parts = []
    for name in _STYLE_FILES:
        path = styles_dir / name
        if path.is_file():
            parts.append(path.read_text(encoding="utf-8"))
    if parts:
        app.setStyleSheet("\n\n".join(parts))
