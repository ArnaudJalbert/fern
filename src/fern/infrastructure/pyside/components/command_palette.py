"""
Command palette (control panel): type to filter, select to run.

Opened with Cmd+P / Ctrl+P or from View > Command Palette. Lists actions
(New page, New database, Delete, etc.) and runs the selected one on Enter.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

_BG = "#1f1f23"
_BORDER = "#27272a"
_ITEM_HEIGHT = 32
_MAX_VISIBLE = 10

_PALETTE_STYLE = f"""
    QFrame#fernCommandPalette {{
        background-color: {_BG};
        border: 1px solid {_BORDER};
        border-radius: 8px;
    }}
    #fernCommandPaletteSearch {{
        background-color: #27272a;
        border: none;
        border-bottom: 1px solid #3f3f46;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        color: #fafafa;
        font-size: 13px;
        padding: 10px 12px;
    }}
    #fernCommandPaletteSearch::placeholder {{
        color: #71717a;
    }}
    #fernCommandPaletteList {{
        background-color: transparent;
        border: none;
        outline: none;
        padding: 4px 0;
    }}
    #fernCommandPaletteList::item {{
        padding: 6px 12px;
        color: #d4d4d8;
        min-height: {_ITEM_HEIGHT - 4}px;
    }}
    #fernCommandPaletteList::item:selected {{
        background-color: #3f3f46;
        color: #fafafa;
    }}
    #fernCommandPaletteList::item:hover {{
        background-color: #27272a;
    }}
"""


@dataclass
class CommandItem:
    """A single command in the palette."""

    label: str
    shortcut: str  # display only, e.g. "⌘P"
    callback: Callable[[], None]


class CommandPalette(QFrame):
    """
    Search line + filtered list of commands. Embed in a page or overlay.
    Type to filter, Enter to run selected, Escape to close. Emits closed() when done.
    """

    closed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("fernCommandPalette")
        self.setStyleSheet(_PALETTE_STYLE)
        self.setMinimumWidth(400)
        self.setMaximumWidth(560)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._search = QLineEdit()
        self._search.setObjectName("fernCommandPaletteSearch")
        self._search.setPlaceholderText("Type a command...")
        self._search.textChanged.connect(self._on_filter_changed)
        self._search.returnPressed.connect(self._on_enter)
        self._search.installEventFilter(self)
        layout.addWidget(self._search)

        self._list = QListWidget()
        self._list.setObjectName("fernCommandPaletteList")
        self._list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list.itemClicked.connect(self._on_item_activated)
        self._list.itemDoubleClicked.connect(self._on_item_activated)
        self._list.installEventFilter(self)
        layout.addWidget(self._list)

        self._all_items: list[CommandItem] = []
        self._filtered_items: list[CommandItem] = []
        self._last_activated_at: float = 0.0

    def set_actions(self, items: list[CommandItem]) -> None:
        """Set the list of commands (label, shortcut, callback)."""
        self._all_items = list(items)
        self._apply_filter(self._search.text().strip())

    def _apply_filter(self, text: str) -> None:
        text_lower = text.lower()
        if not text_lower:
            self._filtered_items = list(self._all_items)
        else:
            self._filtered_items = [
                item for item in self._all_items if text_lower in item.label.lower()
            ]

        self._list.clear()
        for item in self._filtered_items:
            row = QListWidgetItem(item.label)
            if item.shortcut:
                row.setText(f"{item.label}  \t{item.shortcut}")
            row.setData(Qt.ItemDataRole.UserRole, item)
            self._list.addItem(row)

        if self._filtered_items:
            self._list.setCurrentRow(0)
        self._list.setMaximumHeight(
            min(len(self._filtered_items), _MAX_VISIBLE) * _ITEM_HEIGHT + 8
        )

    def _on_filter_changed(self, text: str) -> None:
        self._apply_filter(text.strip())

    def _on_enter(self) -> None:
        row = self._list.currentRow()
        if 0 <= row < len(self._filtered_items):
            callback = self._filtered_items[row].callback
            self.closed.emit()
            callback()
        else:
            self.closed.emit()

    def _on_item_activated(self, item: QListWidgetItem) -> None:
        now = time.monotonic()
        if now - self._last_activated_at < 0.3:
            return
        self._last_activated_at = now
        cmd = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(cmd, CommandItem):
            callback = cmd.callback
            self.closed.emit()
            callback()
        else:
            self.closed.emit()

    def eventFilter(self, obj: QWidget, event) -> bool:
        # Guard: _list may not exist yet if Qt delivers events during __init__
        _list = getattr(self, "_list", None)
        _filtered = getattr(self, "_filtered_items", [])

        if obj is self._search and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Down and _filtered and _list is not None:
                _list.setFocus()
                _list.setCurrentRow(0)
                return True
        if _list is not None and obj is _list and event.type() == event.Type.KeyPress:
            key = event.key()
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self._on_enter()
                return True
            if key == Qt.Key.Key_Escape:
                self.closed.emit()
                return True
            if key == Qt.Key.Key_Up and _list.currentRow() <= 0:
                self._search.setFocus()
                return True
            if key in (Qt.Key.Key_Up, Qt.Key.Key_Down):
                return False  # let list handle
            # Forward other keys to search box
            self._search.setFocus()
            copy = QKeyEvent(
                event.type(),
                event.key(),
                event.modifiers(),
                event.text(),
            )
            QApplication.sendEvent(self._search, copy)
            return True
        return super().eventFilter(obj, event)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._search.setFocus()
        self._search.clear()
        self._apply_filter("")
