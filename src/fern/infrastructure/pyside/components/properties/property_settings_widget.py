"""
Widget for generic property settings: name and type only.

Used only in the Add-property flow. Type-specific editing (e.g. status choices)
is done in dedicated edit dialogs per type, not here.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLineEdit,
    QWidget,
)

TYPE_DISPLAY_TO_KEY = {"Boolean": "boolean", "String": "string", "Status": "status"}
TYPE_OPTIONS = list(TYPE_DISPLAY_TO_KEY)


def type_key_to_display(key: str) -> str:
    """Return display label for a type key (e.g. 'boolean' -> 'Boolean')."""
    for label, k in TYPE_DISPLAY_TO_KEY.items():
        if k == (key or "").strip().lower():
            return label
    return "String"


class PropertySettingsWidget(QWidget):
    """
    Name + type (Boolean / String / Status). No choices or type-specific fields.
    Use get_name() and get_type_key() after confirm.
    """

    def __init__(
        self,
        name: str = "",
        type_key: str = "boolean",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("propertySettingsWidget")
        layout = QFormLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._name_edit = QLineEdit()
        self._name_edit.setObjectName("propertySettingsName")
        self._name_edit.setPlaceholderText("Property name")
        self._name_edit.setText(name)
        layout.addRow("Name:", self._name_edit)

        self._type_combo = QComboBox()
        self._type_combo.setObjectName("propertySettingsType")
        self._type_combo.addItems(TYPE_OPTIONS)
        idx = TYPE_OPTIONS.index(type_key_to_display(type_key))
        self._type_combo.setCurrentIndex(max(0, idx))
        layout.addRow("Type:", self._type_combo)

    def get_name(self) -> str:
        return self._name_edit.text().strip()

    def set_name(self, value: str) -> None:
        self._name_edit.setText(value or "")

    def get_type_key(self) -> str:
        label = self._type_combo.currentText()
        return TYPE_DISPLAY_TO_KEY.get(label, "string")

    def set_type_key(self, key: str) -> None:
        label = type_key_to_display(key)
        idx = TYPE_OPTIONS.index(label) if label in TYPE_OPTIONS else 0
        self._type_combo.setCurrentIndex(idx)
