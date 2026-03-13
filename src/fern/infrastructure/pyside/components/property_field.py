"""
Reusable property editor: label + widget chosen by type.

Registers editor factories per type key (e.g. 'boolean', 'string'). Each factory
creates the widget, and provides get/set value and connect-to-changed. Use
PropertyField.register_editor() to add new types; then create PropertyField(label, type_key, value).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

# Type: (create_widget(parent), get_value(widget), set_value(widget, value), connect(widget, callback))
_EditorAdapter = tuple[
    Callable[[QWidget], QWidget],
    Callable[[QWidget], Any],
    Callable[[QWidget, Any], None],
    Callable[[QWidget, Callable[[], None]], None],
]

_REGISTRY: dict[str, _EditorAdapter] = {}


def _boolean_editor() -> _EditorAdapter:
    def create(parent: QWidget) -> QWidget:
        w = QCheckBox(parent)
        w.setObjectName("propertyFieldCheckbox")
        return w

    def get_value(w: QWidget) -> bool:
        return w.isChecked()

    def set_value(w: QWidget, value: Any) -> None:
        w.setChecked(bool(value))

    def connect(w: QWidget, callback: Callable[[], None]) -> None:
        w.toggled.connect(lambda: callback())

    return create, get_value, set_value, connect


def _string_editor() -> _EditorAdapter:
    def create(parent: QWidget) -> QWidget:
        w = QLineEdit(parent)
        w.setObjectName("propertyFieldLineEdit")
        w.setClearButtonEnabled(True)
        return w

    def get_value(w: QWidget) -> str:
        return w.text().strip()

    def set_value(w: QWidget, value: Any) -> None:
        w.setText(str(value) if value is not None else "")

    def connect(w: QWidget, callback: Callable[[], None]) -> None:
        w.editingFinished.connect(callback)

    return create, get_value, set_value, connect


def _register_builtins() -> None:
    if "boolean" not in _REGISTRY:
        _REGISTRY["boolean"] = _boolean_editor()
    if "string" not in _REGISTRY:
        _REGISTRY["string"] = _string_editor()


_register_builtins()


class PropertyField(QWidget):
    """
    One row: label + editor widget. Editor is chosen by type_key from the registry.

    Set label, type_key and value via set_property(); read with get_value();
    value_changed is emitted when the user changes the value. Reusable anywhere
    you need a typed property editor row.
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
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("propertyField")
        self._property_id = property_id
        self._vertical = vertical
        self._label_width = label_width
        self._layout = QVBoxLayout(self) if vertical else QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)
        self._label = QLabel(label)
        self._label.setObjectName("propertyFieldLabel")
        if not vertical:
            self._label.setFixedWidth(label_width if label_width is not None else 120)
        else:
            self._label.setWordWrap(True)
        self._label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self._layout.addWidget(self._label, 0)
        self._editor_widget: QWidget | None = None
        self._get_value: Callable[[QWidget], Any] | None = None
        self._set_value: Callable[[QWidget, Any], None] | None = None
        self.set_property(label, property_type, value)

    @staticmethod
    def register_editor(
        type_key: str,
        create_widget: Callable[[QWidget], QWidget],
        get_value: Callable[[QWidget], Any],
        set_value: Callable[[QWidget, Any], None],
        connect_changed: Callable[[QWidget, Callable[[], None]], None],
    ) -> None:
        """Register an editor for a type. Use to add new property types dynamically."""
        _REGISTRY[type_key] = (create_widget, get_value, set_value, connect_changed)

    def set_property(self, label: str, property_type: str, value: Any) -> None:
        """Update label, switch editor to the given type, and set value."""
        self._label.setText(label)
        type_key = (property_type or "string").strip().lower()
        adapter = _REGISTRY.get(type_key) or _REGISTRY.get(
            "string", _REGISTRY["string"]
        )
        create, get_val, set_val, connect = adapter

        if self._editor_widget is not None:
            self._layout.removeWidget(self._editor_widget)
            self._editor_widget.deleteLater()
            self._editor_widget = None

        self._editor_widget = create(self)
        self._get_value = get_val
        self._set_value = set_val
        self._set_value(self._editor_widget, value)
        connect(self._editor_widget, self._emit_value_changed)
        editor_min = (
            180 if self._vertical else (100 if self._label_width is not None else 200)
        )
        self._editor_widget.setMinimumWidth(editor_min)
        sp = self._editor_widget.sizePolicy()
        sp.setHorizontalPolicy(QSizePolicy.Policy.Expanding)
        self._editor_widget.setSizePolicy(sp)
        self._layout.addWidget(self._editor_widget, 1)

    def _emit_value_changed(self) -> None:
        if self._editor_widget is not None and self._get_value is not None:
            self.value_changed.emit(self._get_value(self._editor_widget))

    def get_value(self) -> Any:
        if self._editor_widget is None or self._get_value is None:
            return None
        return self._get_value(self._editor_widget)

    def set_value(self, value: Any) -> None:
        if self._editor_widget is not None and self._set_value is not None:
            self._set_value(self._editor_widget, value)

    def get_property_id(self) -> str:
        return self._property_id

    def set_property_id(self, property_id: str) -> None:
        self._property_id = property_id
