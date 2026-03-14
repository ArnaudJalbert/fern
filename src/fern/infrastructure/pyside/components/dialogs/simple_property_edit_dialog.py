"""Edit dialog for properties that only need a name (boolean, string, etc.)."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from .base_property_edit_dialog import BasePropertyEditDialog


class SimplePropertyEditDialog(BasePropertyEditDialog):
    """Name-only edit dialog for boolean, string, or any simple property type."""

    def __init__(
        self,
        type_key: str,
        name: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.TYPE_KEY = type_key
        self.setWindowTitle(f"Edit {type_key} property")
        self.setObjectName(f"{type_key}PropertyEditDialog")

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        self._name_edit = QLineEdit()
        self._name_edit.setObjectName(f"{type_key}PropertyName")
        self._name_edit.setPlaceholderText("Property name")
        self._name_edit.setText(name or "")
        form.addRow("Name:", self._name_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_name(self) -> str:
        return (self._name_edit.text() or "").strip()


def run_simple_property_editor(
    type_key: str,
    name: str = "",
    parent: QWidget | None = None,
) -> str | None:
    """Show a name-only property editor. Returns name on Ok, None on Cancel."""
    dialog = SimplePropertyEditDialog(type_key=type_key, name=name, parent=parent)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.get_name()
    return None


def run_boolean_property_editor(
    name: str = "",
    parent: QWidget | None = None,
) -> str | None:
    """Show a boolean property editor. Returns name on Ok, None on Cancel."""
    return run_simple_property_editor("boolean", name=name, parent=parent)


def run_string_property_editor(
    name: str = "",
    parent: QWidget | None = None,
) -> str | None:
    """Show a string property editor. Returns name on Ok, None on Cancel."""
    return run_simple_property_editor("string", name=name, parent=parent)
