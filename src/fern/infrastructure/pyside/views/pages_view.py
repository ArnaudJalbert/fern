"""
Pages list view: table of pages (ID, Title, property columns) with New page and context menu.

Reusable FernView that displays page-like items. Connect page_activated when
a row is double-clicked, new_page_requested for the New page button,
page_delete_requested when the user chooses Delete, and add_property_requested
when the user chooses Add property from the options menu.
"""

from collections.abc import Sequence
from typing import Any, Protocol

from PySide6.QtCore import QModelIndex, Qt, Signal
from PySide6.QtWidgets import QMenu, QPushButton

from fern.infrastructure.pyside.components import CheckboxDelegate, Table

from .base import FernView


class PageLike(Protocol):
    """Protocol for items passed to PagesView. Any object with these attributes works."""

    id: Any
    title: str
    content: str


class PagesView(FernView):
    """
    Table of pages (ID, Title, plus property columns) with back button, New page, and context menu.

    Schema is an optional sequence of property definitions (.id, .name, .type); boolean properties
    are shown as Yes/No. Connect add_property_requested to add a new property to the database.
    """

    view_id = "pages"
    page_activated = Signal(object)
    new_page_requested = Signal()
    page_delete_requested = Signal(object)
    add_property_requested = Signal()
    property_value_changed = Signal(object, str, object)  # page, property_id, value
    property_edit_requested = Signal(object)  # schema property (id, name, type)
    property_remove_requested = Signal(str)  # property_id

    def __init__(
        self,
        pages: Sequence[object] = (),
        title: str = "Pages",
        parent=None,
    ) -> None:
        self._pages: list[object] = list(pages)
        self._title = title
        self._schema: list[object] = []
        super().__init__(parent)
        self.setObjectName("pagesView")
        self._build_content()
        self.set_back_visible(True)

    def _build_content(self) -> None:
        new_btn = QPushButton("New page")
        new_btn.setObjectName("pagesNewPageButton")
        new_btn.setMinimumWidth(96)
        new_btn.clicked.connect(self.new_page_requested.emit)
        self.add_toolbar_widget(new_btn)
        self._table = Table()
        table_view = self._table.view()
        table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        table_view.customContextMenuRequested.connect(self._on_context_menu_requested)
        header = table_view.horizontalHeader()
        header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(self._on_header_context_menu_requested)
        table_view.doubleClicked.connect(self._on_row_activated)
        table_view.setEditTriggers(
            table_view.editTriggers()
            | table_view.EditTrigger.DoubleClicked
            | table_view.EditTrigger.EditKeyPressed
            | table_view.EditTrigger.SelectedClicked
        )
        self._table.model().dataChanged.connect(self._on_table_data_changed)
        self._checkbox_delegate = CheckboxDelegate(self)
        self.content_layout().addWidget(self._table)
        self.options_clicked.connect(self._on_options_clicked)
        self._fill_table()

    def _on_options_clicked(self) -> None:
        menu = QMenu(self)
        menu.setObjectName("vaultContentOptionsMenu")
        add_prop = menu.addAction("Add property")
        add_prop.triggered.connect(self.add_property_requested.emit)
        btn = self._options_btn
        pos = btn.mapToGlobal(btn.rect().topLeft())
        menu.exec(pos)

    def set_pages(
        self,
        pages: Sequence[object],
        title: str | None = None,
        schema: Sequence[object] | None = None,
    ) -> None:
        """Update the list of pages; schema is the list of property definitions (optional)."""
        self._pages = list(pages)
        if title is not None:
            self._title = title
        if schema is not None:
            self._schema = list(schema)
        self._fill_table()

    def get_pages(self) -> list[object]:
        """Return the current list of page objects (read-only copy)."""
        return list(self._pages)

    def get_schema(self) -> list[object]:
        """Return the current schema (read-only copy)."""
        return list(self._schema)

    def _fill_table(self) -> None:
        headers = ["ID", "Title"] + [getattr(p, "name", "") for p in self._schema]
        rows = []
        for page in self._pages:
            props = getattr(page, "properties", [])
            value_by_id = {
                getattr(p, "id", ""): getattr(p, "value", None) for p in props
            }
            row = {
                "ID": str(getattr(page, "id", "")),
                "Title": getattr(page, "title", str(page)),
            }
            for prop in self._schema:
                pid = getattr(prop, "id", "")
                ptype = getattr(prop, "type", "boolean")
                val = value_by_id.get(pid)
                if ptype == "boolean":
                    row[getattr(prop, "name", pid)] = (
                        bool(val) if val is not None else False
                    )
                else:
                    row[getattr(prop, "name", pid)] = (
                        str(val) if val is not None else ""
                    )
            rows.append(row)
        self._table.set_data(headers, rows)
        table_view = self._table.view()
        for col in range(2, 2 + len(self._schema)):
            if (
                col < len(headers)
                and getattr(self._schema[col - 2], "type", "") == "boolean"
            ):
                table_view.setItemDelegateForColumn(col, self._checkbox_delegate)

    def _on_table_data_changed(self, top_left, bottom_right, roles) -> None:
        """When a property cell is edited, persist and emit property_value_changed."""
        if top_left.column() < 2 or top_left.row() >= len(self._pages):
            return
        col = top_left.column()
        schema_idx = col - 2
        if schema_idx >= len(self._schema):
            return
        prop = self._schema[schema_idx]
        ptype = getattr(prop, "type", "boolean")
        row = top_left.row()
        page = self._pages[row]
        model = self._table.model()
        idx = model.index(row, col)
        value = model.data(idx, Qt.ItemDataRole.EditRole)
        if ptype == "boolean":
            if not isinstance(value, bool):
                return
        else:
            value = str(value) if value is not None else ""
        self.property_value_changed.emit(page, getattr(prop, "id", ""), value)

    def _on_row_activated(self, index: QModelIndex) -> None:
        """Emit page_activated only when double-clicking ID or Title; property columns open in-place editor."""
        row = index.row()
        col = index.column()
        if col >= 2 or row < 0 or row >= len(self._pages):
            return
        self.page_activated.emit(self._pages[row])

    def _on_header_context_menu_requested(self, pos) -> None:
        """Show Edit / Remove property when right-clicking a property column header."""
        header = self._table.view().horizontalHeader()
        section = header.logicalIndexAt(pos)
        if section < 2 or section - 2 >= len(self._schema):
            return
        prop = self._schema[section - 2]
        property_id = getattr(prop, "id", "")
        menu = QMenu(self)
        edit_action = menu.addAction("Edit property...")
        edit_action.triggered.connect(lambda: self.property_edit_requested.emit(prop))
        remove_action = menu.addAction("Remove property")
        remove_action.triggered.connect(
            lambda: self.property_remove_requested.emit(property_id)
        )
        menu.exec(header.mapToGlobal(pos))

    def _on_context_menu_requested(self, pos) -> None:
        """Show a context menu with Delete for the row under the cursor."""
        table_view = self._table.view()
        index = table_view.indexAt(pos)
        if not index.isValid() or index.row() >= len(self._pages):
            return
        page = self._pages[index.row()]
        menu = QMenu(self)
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(lambda: self.page_delete_requested.emit(page))
        menu.exec(table_view.viewport().mapToGlobal(pos))
