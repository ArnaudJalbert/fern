"""
Page editor view: title + property cards + markdown content.

Uses PropertyCardsWidget and PropertyCard. Emits save_requested (debounced),
delete_requested, property_value_changed when a property is edited.
"""

import sys

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLineEdit, QPlainTextEdit, QPushButton, QSizePolicy

from fern.infrastructure.pyside.components import (
    MarkdownHighlighter,
    PropertyCard,
    PropertyCardsWidget,
)
from fern.infrastructure.pyside.utils import property_type_key, set_expanding

from .base import FernView

_SAVE_DEBOUNCE_MS = 800


class EditorView(FernView):
    """
    Edit a single page: title, property fields (label + type-appropriate widget), markdown content.

    PropertyField components are built dynamically from the page's properties.
    Emits save_requested (debounced), property_value_changed, delete_requested.
    """

    view_id = "editor"
    page_saved = Signal(object)
    save_requested = Signal()
    delete_requested = Signal()
    property_value_changed = Signal(object, str, object)  # page, property_id, value

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("editorView")
        self._page = None
        self._property_cards_widget: PropertyCardsWidget | None = None
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._on_save_timer)
        self._build_content()
        self.set_back_visible(True)
        set_expanding(self, horizontal=True, vertical=True)

    def _build_content(self) -> None:
        self.content_layout().setContentsMargins(24, 16, 24, 0)
        self.content_layout().setSpacing(12)

        delete_btn = QPushButton("Delete")
        delete_btn.setObjectName("editorDeleteButton")
        delete_btn.clicked.connect(self.delete_requested.emit)
        self.add_toolbar_widget(delete_btn)

        self._title_edit = QLineEdit()
        self._title_edit.setObjectName("editorTitleEdit")
        self._title_edit.setPlaceholderText("Title")
        self._title_edit.textChanged.connect(self._on_text_changed)
        self.content_layout().addWidget(self._title_edit)

        self._property_cards_widget = PropertyCardsWidget()
        self._property_cards_widget.setObjectName("editorPropertiesContainer")
        self._property_cards_widget.setMinimumWidth(320)
        set_expanding(self._property_cards_widget, horizontal=True, vertical=False)
        self.content_layout().addWidget(
            self._property_cards_widget, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )

        self._content_edit = QPlainTextEdit()
        self._content_edit.setObjectName("editorContentEdit")
        self._content_edit.setPlaceholderText("Content (Markdown)…")
        font = QFont("Monaco", 13) if sys.platform == "darwin" else QFont("Consolas", 13)
        self._content_edit.setFont(font)
        MarkdownHighlighter(self._content_edit.document())
        self._content_edit.textChanged.connect(self._on_text_changed)
        self._content_edit.setMinimumHeight(80)
        self._content_edit.setMinimumWidth(0)
        set_expanding(self._content_edit, horizontal=True, vertical=True)
        self.content_layout().addWidget(self._content_edit, 1)
        self.content_layout().setStretchFactor(self._content_edit, 1)
        self.content_layout().setStretchFactor(self._title_edit, 0)
        self.content_layout().setStretchFactor(self._property_cards_widget, 0)

    def _on_text_changed(self) -> None:
        if self._page is not None:
            self._save_timer.start(_SAVE_DEBOUNCE_MS)

    def _on_save_timer(self) -> None:
        if self._page is not None:
            self.save_requested.emit()

    def _clear_properties(self) -> None:
        if self._property_cards_widget is not None:
            self._property_cards_widget.clear()

    def _on_property_value_changed(self, card: PropertyCard) -> None:
        if self._page is not None:
            self.property_value_changed.emit(
                self._page, card.get_property_id(), card.get_value()
            )

    def _rebuild_properties(self, page, property_order=None) -> None:
        self._clear_properties()
        if self._property_cards_widget is None:
            return
        props = [
            p for p in getattr(page, "properties", [])
            if getattr(p, "type", "") not in ("id", "title")
        ]
        if property_order:
            order_ids = [i for i in property_order if i not in ("id", "title")]
            by_id = {getattr(p, "id", ""): p for p in props}
            ordered = [by_id[i] for i in order_ids if i in by_id]
            rest = [p for p in props if getattr(p, "id", "") not in order_ids]
            props = ordered + rest
        for prop in props:
            pid = getattr(prop, "id", "")
            name = getattr(prop, "name", pid)
            ptype = getattr(prop, "type", "boolean")
            value = getattr(prop, "value", None)
            type_key = property_type_key(ptype)
            card = PropertyCard(
                label=name.rstrip(":") + ":",
                property_type=type_key,
                value=value,
                property_id=pid,
                parent=self._property_cards_widget,
            )
            card.value_changed.connect(lambda _val, c=card: self._on_property_value_changed(c))
            self._property_cards_widget.add_card(card)

    def set_page(self, page, property_order=None) -> None:
        self._save_timer.stop()
        self._page = page
        if page is None:
            self._title_edit.clear()
            self._clear_properties()
            self._content_edit.clear()
            return
        title = getattr(page, "title", "")
        content = getattr(page, "content", "")
        self._title_edit.blockSignals(True)
        self._content_edit.blockSignals(True)
        self._title_edit.setText(title)
        self._content_edit.setPlainText(content)
        self._title_edit.blockSignals(False)
        self._content_edit.blockSignals(False)
        self._rebuild_properties(page, property_order=property_order)

    def get_edited_page_data(self) -> tuple[int, str, str] | None:
        if self._page is None:
            return None
        return (
            getattr(self._page, "id", 0),
            self._title_edit.text().strip(),
            self._content_edit.toPlainText(),
        )
