"""
Dialog to view and edit the list of status choices (name, category, color).

All editing in one window: table + inline color grid popup (no separate dialog).
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtCore import QPoint, QRect, QSize
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from fern.infrastructure.controller import ChoiceOutput

from .base_property_edit_dialog import BasePropertyEditDialog

_BTN_SIZE = 24
_BTN_RADIUS = 3
_PLUS_PAD = 4
_PLUS_PEN = 1

# Minimal preset palette (grays + accents) for in-window picker
_PRESET_COLORS = [
    "#94a3b8",
    "#64748b",
    "#475569",
    "#334155",
    "#1e293b",
    "#f87171",
    "#fb923c",
    "#fbbf24",
    "#4ade80",
    "#22d3ee",
    "#a78bfa",
    "#f472b6",
    "#fafafa",
    "#a1a1aa",
    "#71717a",
]


def _parse_color(text: str) -> QColor | None:
    """Parse hex color string to QColor; return None if invalid."""
    text = (text or "").strip()
    if not text:
        return None
    if not text.startswith("#"):
        text = "#" + text
    c = QColor(text)
    return c if c.isValid() else None


class _ColorGridPopup(QFrame):
    """Popup color grid shown inside the same window; click a swatch to set color."""

    def __init__(
        self,
        parent: QWidget,
        initial: QColor | None,
        on_chosen: Callable[[str], None],
    ) -> None:
        super().__init__(parent, Qt.WindowType.Popup)
        self._on_chosen = on_chosen
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            "background: #27272a; border: 1px solid #3f3f46; border-radius: 6px;"
        )
        layout = QGridLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)
        size = 20
        for i, hex_color in enumerate(_PRESET_COLORS):
            btn = QPushButton()
            btn.setFixedSize(size, size)
            btn.setStyleSheet(
                f"background: {hex_color}; border: 1px solid #52525b; border-radius: 3px;"
            )
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, h=hex_color: self._pick(h))
            layout.addWidget(btn, i // 5, i % 5)
        custom_btn = QPushButton("Custom…")
        custom_btn.setStyleSheet(
            "background: transparent; border: 1px solid #52525b; border-radius: 3px; padding: 4px 8px; font-size: 11px;"
        )
        custom_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        custom_btn.clicked.connect(self._open_custom)
        layout.addWidget(custom_btn, (len(_PRESET_COLORS) + 4) // 5, 0, 1, 5)
        self._initial = initial

    def _pick(self, hex_color: str) -> None:
        self._on_chosen(hex_color)
        # Defer close so the button's clicked signal is fully processed first (Popup can close before callback runs)
        QTimer.singleShot(0, self.close)

    def _open_custom(self) -> None:
        initial = self._initial or QColor(128, 128, 128)
        chosen = QColorDialog.getColor(initial, self, "Choose color")
        if chosen.isValid():
            self._on_chosen(chosen.name())
        self.close()


class _ColorPickerDelegate(QStyledItemDelegate):
    """Delegate for the Color column: minimal swatch + subtle plus; click shows in-window color grid."""

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        option_copy = QStyleOptionViewItem(option)
        option_copy.text = ""
        QApplication.style().drawControl(
            QStyle.ControlElement.CE_ItemViewItem, option_copy, painter, option.widget
        )
        text = index.data(Qt.ItemDataRole.EditRole) or ""
        color = _parse_color(text)
        is_empty = not color or not color.isValid()
        if is_empty:
            color = QColor(100, 100, 100)
        rect = option.rect
        btn_rect = QRect(0, 0, _BTN_SIZE, _BTN_SIZE)
        btn_rect.moveCenter(rect.center())
        painter.save()
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        painter.setBrush(color)
        painter.drawRoundedRect(btn_rect, _BTN_RADIUS, _BTN_RADIUS)
        if is_empty:
            c = btn_rect.center()
            painter.setPen(QPen(QColor(115, 115, 122), _PLUS_PEN))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawLine(
                QPoint(c.x() - _PLUS_PAD, c.y()), QPoint(c.x() + _PLUS_PAD, c.y())
            )
            painter.drawLine(
                QPoint(c.x(), c.y() - _PLUS_PAD), QPoint(c.x(), c.y() + _PLUS_PAD)
            )
        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:
        return QSize(_BTN_SIZE + 12, _BTN_SIZE + 6)

    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index
    ) -> None:
        return None

    def editorEvent(
        self, event: QEvent, model, option: QStyleOptionViewItem, index
    ) -> bool:
        if event.type() == QEvent.Type.MouseButtonRelease:
            table = option.widget
            if table is not None and isinstance(table, QTableWidget):
                row, col = index.row(), index.column()
                initial_text = index.data(Qt.ItemDataRole.EditRole) or ""
                initial = _parse_color(initial_text)
                cell_rect = option.rect
                global_pos = table.viewport().mapToGlobal(cell_rect.bottomLeft())

                def on_chosen(hex_str: str) -> None:
                    item = table.item(row, col)
                    if item is not None:
                        item.setText(hex_str)
                    else:
                        table.setItem(row, col, QTableWidgetItem(hex_str))

                popup = _ColorGridPopup(table, initial, on_chosen)
                popup.adjustSize()
                popup.move(global_pos.x(), global_pos.y() + 2)
                popup.show()
                return True
        return super().editorEvent(event, model, option, index)


class StatusPropertyEditDialog(BasePropertyEditDialog):
    """
    Modal dialog to edit the status property: name and list of choices in one window.

    Top: Property name (line edit). Below: table (Status, Category, Color), Add/Remove.
    """

    TYPE_KEY = "status"

    def __init__(
        self,
        choices: list[ChoiceOutput],
        parent: QWidget | None = None,
        name: str = "",
    ) -> None:
        super().__init__(parent)
        self.setObjectName("statusChoicesEditorDialog")
        self.setWindowTitle("Edit status property")
        self.setMinimumSize(480, 320)
        self.resize(520, 380)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        self._name_edit = QLineEdit()
        self._name_edit.setObjectName("statusPropertyName")
        self._name_edit.setPlaceholderText("Property name")
        self._name_edit.setText(name or "")
        form.addRow("Property name:", self._name_edit)
        layout.addLayout(form)

        hint = QLabel(
            "Double-click Status or Category to edit. Click the color swatch to pick a color. Add / Remove for rows."
        )
        hint.setObjectName("statusChoicesHint")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #a1a1aa; font-size: 11px;")
        layout.addWidget(hint)

        self._table = QTableWidget(0, 3)
        self._table.setObjectName("statusChoicesTable")
        self._table.setHorizontalHeaderLabels(["Status", "Category", "Color"])
        self._table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self._table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self._table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self._table.setEditTriggers(
            QTableWidget.EditTrigger.DoubleClicked
            | QTableWidget.EditTrigger.EditKeyPressed
        )
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.verticalHeader().setVisible(True)
        self._table.setItemDelegateForColumn(2, _ColorPickerDelegate(self._table))
        layout.addWidget(self._table)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        self._add_btn = QPushButton("Add")
        self._add_btn.setObjectName("statusChoicesAdd")
        self._remove_btn = QPushButton("Remove")
        self._remove_btn.setObjectName("statusChoicesRemove")
        self._add_btn.clicked.connect(self._on_add)
        self._remove_btn.clicked.connect(self._on_remove)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        btn_layout.addWidget(self._add_btn)
        btn_layout.addWidget(self._remove_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._populate(choices or [])
        self._on_selection_changed()

    def _populate(self, choices: list[ChoiceOutput]) -> None:
        self._table.setRowCount(len(choices))
        for row, c in enumerate(choices):
            self._table.setItem(row, 0, QTableWidgetItem(c.name))
            self._table.setItem(row, 1, QTableWidgetItem(c.category))
            self._table.setItem(row, 2, QTableWidgetItem(c.color))
        self._on_selection_changed()

    def _on_add(self) -> None:
        row = self._table.rowCount()
        self._table.insertRow(row)
        self._table.setItem(row, 0, QTableWidgetItem(""))
        self._table.setItem(row, 1, QTableWidgetItem(""))
        self._table.setItem(row, 2, QTableWidgetItem(""))
        self._table.setCurrentCell(row, 0)
        self._table.editItem(self._table.item(row, 0))

    def _on_remove(self) -> None:
        row = self._table.currentRow()
        if row >= 0:
            self._table.removeRow(row)
        self._on_selection_changed()

    def _on_selection_changed(self) -> None:
        self._remove_btn.setEnabled(self._table.currentRow() >= 0)

    def get_name(self) -> str:
        return (self._name_edit.text() or "").strip()

    def set_name(self, value: str) -> None:
        self._name_edit.setText(value or "")

    def get_choices(self) -> list[ChoiceOutput]:
        """Build and return the list of choices from the table (empty names skipped)."""
        out: list[ChoiceOutput] = []
        for row in range(self._table.rowCount()):
            name_item = self._table.item(row, 0)
            category_item = self._table.item(row, 1)
            color_item = self._table.item(row, 2)
            name = (name_item.text() if name_item else "").strip()
            category = (category_item.text() if category_item else "").strip()
            color = (color_item.text() if color_item else "").strip()
            if name:
                out.append(ChoiceOutput(name=name, category=category, color=color))
        return out


def run_status_choices_editor(
    choices: list[ChoiceOutput],
    parent: QWidget | None = None,
    name: str = "",
) -> tuple[list[ChoiceOutput], str] | None:
    """
    Show the status property editor (name + choices in one window).
    Returns (choices, property_name) on Ok, None on Cancel.
    """
    dialog = StatusPropertyEditDialog(choices=choices, parent=parent, name=name)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return (dialog.get_choices(), dialog.get_name())
    return None
