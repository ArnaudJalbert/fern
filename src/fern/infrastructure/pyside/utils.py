"""
Shared PySide6 helpers: icons, property type key, and size policies.

Use these to avoid duplication across views and keep a single place for paths and helpers.
"""

from pathlib import Path
from typing import Any

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QSizePolicy, QWidget

_ICONS_DIR = Path(__file__).resolve().parent / "icons"


def get_icons_dir() -> Path:
    """Return the path to the pyside/icons directory."""
    return _ICONS_DIR


def load_icon(name: str) -> QIcon:
    """Load an SVG icon from pyside/icons/{name}.svg. Returns an empty QIcon if not found."""
    path = _ICONS_DIR / f"{name}.svg"
    if path.is_file():
        return QIcon(str(path))
    return QIcon()


def property_type_key(ptype: Any) -> str:
    """Return the string type key for a property (e.g. 'boolean', 'string'). Handles enum or str."""
    if isinstance(ptype, str):
        return (ptype or "string").strip().lower()
    if hasattr(ptype, "key") and callable(getattr(ptype, "key")):
        return ptype.key()
    return "string"


def set_expanding(
    widget: QWidget,
    *,
    horizontal: bool = True,
    vertical: bool = False,
) -> None:
    """Set the widget's size policy to Expanding on the given axes."""
    sp = widget.sizePolicy()
    if horizontal:
        sp.setHorizontalPolicy(QSizePolicy.Policy.Expanding)
    if vertical:
        sp.setVerticalPolicy(QSizePolicy.Policy.Expanding)
    widget.setSizePolicy(sp)
