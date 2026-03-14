"""
Property card: a small card (frame) that wraps a single property label + editor.

Reuses PropertyField inside a styled QFrame. Use PropertyCardsWidget to lay out
multiple PropertyCards together in a grid.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QVBoxLayout, QWidget

from .property_field import PropertyField


class PropertyCard(QFrame):
    """
    Card-style wrapper for one property: label + typed editor inside a bordered frame.

    Forwards value_changed, get_value, set_value, get_property_id from the inner PropertyField.
    """

    value_changed = Signal(object)

    def __init__(
        self,
        label: str = "",
        property_type: str = "string",
        value: Any = None,
        property_id: str = "",
        *,
        vertical: bool = False,
        label_width: int | None = None,
        choices: list | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("propertyCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._field = PropertyField(
            label=label,
            property_type=property_type,
            value=value,
            property_id=property_id,
            vertical=vertical,
            label_width=label_width,
            parent=self,
        )
        if choices is not None and (property_type or "").strip().lower() == "status":
            self._field.set_property(label, property_type, value, choices=choices)
        self._field.value_changed.connect(self.value_changed.emit)
        layout.addWidget(self._field)

    def get_value(self) -> Any:
        return self._field.get_value()

    def set_value(self, value: Any) -> None:
        self._field.set_value(value)

    def get_property_id(self) -> str:
        return self._field.get_property_id()

    def set_property_id(self, property_id: str) -> None:
        self._field.set_property_id(property_id)

    def set_property(
        self, label: str, property_type: str, value: Any, **kwargs: Any
    ) -> None:
        self._field.set_property(label, property_type, value, **kwargs)
