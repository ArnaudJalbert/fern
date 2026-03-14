"""
Shared PySide6 helpers: icons, property type key, and size policies.

Use these to avoid duplication across views and keep a single place for paths and helpers.
"""

import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QIcon, QPalette
from PySide6.QtWidgets import QLabel, QMenu, QSizePolicy, QWidgetAction, QWidget

_MENU_BG = "#1f1f23"

_ICONS_DIR = Path(__file__).resolve().parent / "icons"


def get_icons_dir() -> Path:
    """Return the path to the pyside/icons directory."""
    return _ICONS_DIR


def reveal_in_file_explorer(path: Path) -> None:
    """
    Open the system file manager and reveal the given file or folder.
    On macOS: reveals in Finder. On Windows: selects in Explorer. On Linux: opens parent or path.
    """
    path = path.resolve()
    if not path.exists():
        return
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", "-R", str(path)], check=False)
        elif sys.platform == "win32":
            path_str = str(path)
            arg = f'/select,"{path_str}"' if " " in path_str else f"/select,{path_str}"
            subprocess.run(["explorer", arg], check=False)
        else:
            target = path.parent if path.is_file() else path
            subprocess.run(["xdg-open", str(target)], check=False)
    except (OSError, ValueError):
        pass


def reveal_in_explorer_action_label() -> str:
    """Return the menu label for the reveal action (e.g. 'Reveal in Finder')."""
    if sys.platform == "darwin":
        return "Reveal in Finder"
    if sys.platform == "win32":
        return "Open in File Explorer"
    return "Open in File Manager"


def load_icon(name: str) -> QIcon:
    """Load an SVG icon from pyside/icons/{name}.svg. Returns an empty QIcon if not found."""
    path = _ICONS_DIR / f"{name}.svg"
    if path.is_file():
        return QIcon(str(path))
    return QIcon()


def property_type_key(property_type: Any) -> str:
    """Return the string type key for a property (e.g. 'boolean', 'string'). Handles enum or str."""
    if isinstance(property_type, str):
        return (property_type or "string").strip().lower()
    if hasattr(property_type, "key") and callable(getattr(property_type, "key")):
        return property_type.key()
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


class _ColoredMenuLabel(QLabel):
    """Label that triggers the given action on click, for use in QWidgetAction."""

    def __init__(self, text: str, color: str, action: QAction) -> None:
        super().__init__(text)
        self._action = action
        self.setStyleSheet(
            f"color: {color}; padding: 5px 16px; background: none; border: none;"
        )
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAutoFillBackground(False)
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor(_MENU_BG))
        pal.setColor(QPalette.ColorRole.Base, QColor(_MENU_BG))
        self.setPalette(pal)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._action.trigger()
        super().mouseReleaseEvent(event)


def add_colored_action(
    menu: QMenu,
    text: str,
    color: str,
    callback: Callable[[], None],
):
    """Add a menu action with colored text. Returns the action for further wiring if needed."""
    action = QWidgetAction(menu)
    label = _ColoredMenuLabel(text, color, action)
    action.setDefaultWidget(label)
    menu.addAction(action)
    action.triggered.connect(callback)
    return action
