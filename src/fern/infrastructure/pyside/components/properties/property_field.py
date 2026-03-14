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
from PySide6.QtGui import QColor

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

# Role to store choice color on combo items (status editor)
_STATUS_COLOR_ROLE = Qt.ItemDataRole.UserRole

# Type: (create_widget(parent, **kwargs), get_value(widget), set_value(widget, value), connect(widget, callback))
_EditorAdapter = tuple[
    Callable[..., QWidget],
    Callable[[QWidget], Any],
    Callable[[QWidget, Any], None],
    Callable[[QWidget, Callable[[], None]], None],
]

_REGISTRY: dict[str, _EditorAdapter] = {}


def _boolean_editor() -> _EditorAdapter:
    def create(parent: QWidget, **kwargs: Any) -> QWidget:
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
    def create(parent: QWidget, **kwargs: Any) -> QWidget:
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


def _status_choice_color(combo: QComboBox) -> str | None:
    """Return the hex color for the current combo selection, or None."""
    idx = combo.currentIndex()
    if idx < 0:
        return None
    data = combo.itemData(idx, _STATUS_COLOR_ROLE)
    if data is None:
        return None
    s = str(data).strip()
    return s if s else None


def _status_apply_background(combo: QComboBox) -> None:
    """Set combo background to the selected choice color, or clear if none."""
    hex_str = _status_choice_color(combo)
    if hex_str and hex_str.startswith("#"):
        c = QColor(hex_str)
        if c.isValid():
            r, g, b = c.redF(), c.greenF(), c.blueF()
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            text_color = "#ffffff" if lum < 0.5 else "#000000"
            combo.setStyleSheet(
                f"QComboBox#propertyFieldStatusCombo {{ background: {hex_str}; color: {text_color}; }}"
            )
            return
    combo.setStyleSheet("")


def _status_editor() -> _EditorAdapter:
    def create(parent: QWidget, **kwargs: Any) -> QWidget:
        w = QComboBox(parent)
        w.setObjectName("propertyFieldStatusCombo")
        w.setEditable(False)
        choices = kwargs.get("choices") or []
        for c in choices:
            name = getattr(c, "name", str(c))
            color = getattr(c, "color", None)
            idx = w.count()
            w.addItem(name, name)
            if color:
                w.setItemData(idx, (str(color).strip() or None), _STATUS_COLOR_ROLE)
        w.addItem("", "")
        return w

    def get_value(w: QWidget) -> str:
        return w.currentText().strip()

    def set_value(w: QWidget, value: Any) -> None:
        if not isinstance(w, QComboBox):
            return
        text = str(value) if value is not None else ""
        idx = w.findText(text)
        if idx >= 0:
            w.setCurrentIndex(idx)
        else:
            w.setCurrentIndex(w.count() - 1)
        _status_apply_background(w)

    def connect(w: QWidget, callback: Callable[[], None]) -> None:
        if isinstance(w, QComboBox):

            def on_change() -> None:
                _status_apply_background(w)
                callback()

            w.currentIndexChanged.connect(on_change)

    return create, get_value, set_value, connect


def _register_builtins() -> None:
    if "boolean" not in _REGISTRY:
        _REGISTRY["boolean"] = _boolean_editor()
    if "string" not in _REGISTRY:
        _REGISTRY["string"] = _string_editor()
    if "status" not in _REGISTRY:
        _REGISTRY["status"] = _status_editor()


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
        create_widget: Callable[..., QWidget],
        get_value: Callable[[QWidget], Any],
        set_value: Callable[[QWidget, Any], None],
        connect_changed: Callable[[QWidget, Callable[[], None]], None],
    ) -> None:
        """Register an editor for a type. Use to add new property types dynamically.

        create_widget(parent, **kwargs) may receive extra kwargs from set_property (e.g. choices for status).
        """
        _REGISTRY[type_key] = (create_widget, get_value, set_value, connect_changed)

    def set_property(
        self, label: str, property_type: str, value: Any, **kwargs: Any
    ) -> None:
        """Update label, switch editor to the given type, and set value. Pass choices=... for status."""
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

        self._editor_widget = create(self, **kwargs)
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
