"""
Pages list view: table of pages with columns driven entirely by the schema.

All columns (including id and title) come from the schema. Mandatory properties
cannot be hidden or removed. Connect page_activated when a row is double-clicked,
new_page_requested for the New page button, page_delete_requested when the user
chooses Delete, and add_property_requested for Add property.
"""

from collections.abc import Sequence
from typing import Any, Protocol

from PySide6.QtCore import QEvent, QModelIndex, QPoint, QRect, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QApplication, QHeaderView, QMenu, QPushButton, QWidget

from fern.infrastructure.pyside.components import (
    CheckboxDelegate,
    Table,
    TextEditDelegate,
)

from .base import FernView

_MANDATORY_TYPES = {"id", "title"}
_DROP_INDICATOR_COLOR = QColor("#4ade80")
_DROP_INDICATOR_WIDTH = 3


class PageLike(Protocol):
    """Protocol for items passed to PagesView. Any object with these attributes works."""

    id: Any
    title: str
    content: str


class _HeaderDropIndicator(QWidget):
    """Thin vertical line painted over the header to show where a dragged column will land."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setFixedWidth(_DROP_INDICATOR_WIDTH)
        self.hide()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(_DROP_INDICATOR_COLOR, _DROP_INDICATOR_WIDTH)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        mid = self.width() // 2
        p.drawLine(mid, 2, mid, self.height() - 2)
        p.end()


class PagesView(FernView):
    """
    Table of pages with columns driven entirely by the schema (including id/title).

    Schema is a sequence of property definitions (.id, .name, .type, .mandatory).
    Mandatory properties cannot be hidden or removed. Connect add_property_requested
    to add a new property to the database.
    """

    view_id = "pages"
    page_activated = Signal(object)
    new_page_requested = Signal()
    page_delete_requested = Signal(object)
    add_property_requested = Signal()
    property_value_changed = Signal(object, str, object)  # page, property_id, value
    property_edit_requested = Signal(object)  # schema property
    property_remove_requested = Signal(str)  # property_id
    property_order_changed = Signal(object)  # tuple[str, ...] new display order
    save_order_requested = Signal()

    def __init__(
        self,
        pages: Sequence[object] = (),
        title: str = "Pages",
        parent=None,
    ) -> None:
        self._pages: list[object] = list(pages)
        self._title = title
        self._schema: list[object] = []
        self._hidden_property_ids: set[str] = set()
        self._property_order: list[str] = []
        self._drag_from_visual: int | None = None
        self._drag_to_visual: int | None = None
        super().__init__(parent)
        self.setObjectName("pagesView")
        self._build_content()
        self.set_back_visible(True)

    # -- helpers --

    def _is_mandatory(self, prop: object) -> bool:
        return getattr(prop, "mandatory", False) or getattr(prop, "type", "") in _MANDATORY_TYPES

    def _prop_id(self, prop: object) -> str:
        return getattr(prop, "id", "")

    def _prop_name(self, prop: object) -> str:
        return getattr(prop, "name", self._prop_id(prop))

    def _prop_type(self, prop: object) -> str:
        return getattr(prop, "type", "string")

    # -- build --

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

        header.setSectionsMovable(False)
        header.viewport().setMouseTracking(True)

        table_view.doubleClicked.connect(self._on_row_activated)
        table_view.setEditTriggers(
            table_view.editTriggers()
            | table_view.EditTrigger.DoubleClicked
            | table_view.EditTrigger.EditKeyPressed
            | table_view.EditTrigger.SelectedClicked
        )
        self._table.model().dataChanged.connect(self._on_table_data_changed)
        self._checkbox_delegate = CheckboxDelegate(self)
        self._text_edit_delegate = TextEditDelegate(self)
        table_view.installEventFilter(self)
        self._header_viewport = header.viewport()
        self._header_viewport.installEventFilter(self)
        self._drop_indicator = _HeaderDropIndicator(self._header_viewport)
        self.content_layout().addWidget(self._table)
        self.options_clicked.connect(self._on_options_clicked)
        self._fill_table()

    def _on_options_clicked(self) -> None:
        menu = QMenu(self)
        menu.setObjectName("vaultContentOptionsMenu")
        add_prop = menu.addAction("Add property")
        add_prop.triggered.connect(self.add_property_requested.emit)
        menu.addSeparator()
        save_order = menu.addAction("Save column order")
        save_order.triggered.connect(self.save_order_requested.emit)
        btn = self._options_btn
        pos = btn.mapToGlobal(btn.rect().topLeft())
        menu.exec(pos)

    def _update_editing_state(self) -> None:
        view = self._table.view()
        f = QApplication.focusWidget()
        editing = f is not None and f != view and view.isAncestorOf(f)
        view.setProperty("editing", editing)
        view.style().unpolish(view)
        view.style().polish(view)

    def eventFilter(self, obj: object, event: QEvent) -> bool:
        if obj is self._table.view() and event.type() in (QEvent.Type.FocusIn, QEvent.Type.FocusOut):
            QTimer.singleShot(0, self._update_editing_state)

        if obj is self._header_viewport:
            header = self._table.view().horizontalHeader()
            etype = event.type()

            if etype == QEvent.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
                    section = header.logicalIndexAt(pos)
                    if section >= 0:
                        self._drag_from_visual = section
                        self._drag_to_visual = None

            elif etype == QEvent.Type.MouseMove and self._drag_from_visual is not None:
                pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
                target = self._drop_target_for_pos(header, pos)
                if target is not None and target != self._drag_from_visual:
                    self._drag_to_visual = target
                    self._show_drop_indicator(header, target)
                else:
                    self._drag_to_visual = None
                    self._drop_indicator.hide()

            elif etype == QEvent.Type.MouseButtonRelease:
                self._drop_indicator.hide()
                if (
                    self._drag_from_visual is not None
                    and self._drag_to_visual is not None
                    and self._drag_from_visual != self._drag_to_visual
                ):
                    self._apply_column_move(self._drag_from_visual, self._drag_to_visual)
                self._drag_from_visual = None
                self._drag_to_visual = None

        return super().eventFilter(obj, event)

    def _drop_target_for_pos(self, header: QHeaderView, pos: QPoint) -> int | None:
        """Return the column index where a drop at pos would insert, or None."""
        visible = self._visible_schema()
        if not visible:
            return None
        x = pos.x()
        for col in range(len(visible)):
            left = header.sectionPosition(col)
            width = header.sectionSize(col)
            mid = left + width // 2
            if x < mid:
                return col
        return len(visible) - 1

    def _show_drop_indicator(self, header: QHeaderView, target_col: int) -> None:
        """Position and show the drop indicator line at the left edge of target_col."""
        visible = self._visible_schema()
        if not visible or target_col < 0 or target_col >= len(visible):
            self._drop_indicator.hide()
            return
        from_col = self._drag_from_visual
        if from_col is not None and target_col > from_col:
            x = header.sectionPosition(target_col) + header.sectionSize(target_col)
        else:
            x = header.sectionPosition(target_col)
        x -= _DROP_INDICATOR_WIDTH // 2
        self._drop_indicator.setFixedHeight(header.viewport().height())
        self._drop_indicator.move(x, 0)
        self._drop_indicator.show()
        self._drop_indicator.raise_()

    def _apply_column_move(self, from_col: int, to_col: int) -> None:
        """Move a column in _property_order based on visible indices and refresh."""
        visible = self._visible_schema()
        if from_col < 0 or from_col >= len(visible) or to_col < 0 or to_col >= len(visible):
            return
        visible_ids = [self._prop_id(p) for p in visible]
        moved_id = visible_ids.pop(from_col)
        visible_ids.insert(to_col, moved_id)
        hidden = [i for i in self._property_order if i in self._hidden_property_ids]
        self._property_order = visible_ids + hidden
        self._fill_table()
        self.property_order_changed.emit(tuple(self._property_order))

    # -- data --

    def set_pages(
        self,
        pages: Sequence[object],
        title: str | None = None,
        schema: Sequence[object] | None = None,
        property_order: Sequence[str] | None = None,
    ) -> None:
        """Update the list of pages; schema and property_order optional."""
        self._pages = list(pages)
        if title is not None:
            self._title = title
        if schema is not None:
            self._schema = list(schema)
            schema_ids = {self._prop_id(p) for p in self._schema}
            self._hidden_property_ids &= schema_ids
            if property_order is not None:
                self._property_order = [i for i in property_order if i in schema_ids]
                for p in self._schema:
                    pid = self._prop_id(p)
                    if pid not in self._property_order:
                        self._property_order.append(pid)
            else:
                self._property_order = [i for i in self._property_order if i in schema_ids]
                for p in self._schema:
                    pid = self._prop_id(p)
                    if pid not in self._property_order:
                        self._property_order.append(pid)
        self._fill_table()

    def get_pages(self) -> list[object]:
        return list(self._pages)

    def get_schema(self) -> list[object]:
        return list(self._schema)

    def get_property_order(self) -> tuple[str, ...]:
        return tuple(self._property_order)

    def get_property_order_for_save(self) -> tuple[str, ...]:
        """Return the current property order for persistence. Raises if empty."""
        if not self._schema:
            raise RuntimeError("No schema loaded — nothing to save.")
        if not self._property_order:
            raise RuntimeError("No property order — no properties in the database.")
        return tuple(self._property_order)

    # -- visible schema --

    def _visible_schema(self) -> list[object]:
        """Schema with hidden properties filtered out, in display order."""
        visible_ids = [
            self._prop_id(p) for p in self._schema
            if self._prop_id(p) not in self._hidden_property_ids
        ]
        order_set = set(self._property_order)
        ordered = [i for i in self._property_order if i in visible_ids]
        ordered += [i for i in visible_ids if i not in order_set]
        schema_by_id = {self._prop_id(p): p for p in self._schema}
        return [schema_by_id[i] for i in ordered if i in schema_by_id]

    # -- fill table --

    def _fill_table(self) -> None:
        visible = self._visible_schema()
        headers = [self._prop_name(p) for p in visible]
        rows = []
        for page in self._pages:
            page_props = getattr(page, "properties", [])
            value_by_id = {
                getattr(p, "id", ""): getattr(p, "value", None) for p in page_props
            }
            row: dict[str, Any] = {}
            for prop in visible:
                pid = self._prop_id(prop)
                ptype = self._prop_type(prop)
                val = value_by_id.get(pid)
                if ptype == "boolean":
                    row[self._prop_name(prop)] = bool(val) if val is not None else False
                elif ptype == "id":
                    row[self._prop_name(prop)] = str(val) if val is not None else ""
                else:
                    row[self._prop_name(prop)] = str(val) if val is not None else ""
            rows.append(row)
        self._table.set_data(headers, rows)
        readonly = {
            col for col, prop in enumerate(visible)
            if self._prop_type(prop) in _MANDATORY_TYPES
        }
        self._table.model().set_readonly_columns(readonly)
        table_view = self._table.view()
        for col, prop in enumerate(visible):
            ptype = self._prop_type(prop)
            if ptype == "boolean":
                table_view.setItemDelegateForColumn(col, self._checkbox_delegate)
            else:
                table_view.setItemDelegateForColumn(col, self._text_edit_delegate)

    # -- data changed --

    def _on_table_data_changed(self, top_left, bottom_right, roles) -> None:
        visible = self._visible_schema()
        col = top_left.column()
        row = top_left.row()
        if col < 0 or col >= len(visible) or row < 0 or row >= len(self._pages):
            return
        prop = visible[col]
        pid = self._prop_id(prop)
        ptype = self._prop_type(prop)
        if ptype in _MANDATORY_TYPES:
            return
        page = self._pages[row]
        model = self._table.model()
        idx = model.index(row, col)
        value = model.data(idx, Qt.ItemDataRole.EditRole)
        if ptype == "boolean":
            if not isinstance(value, bool):
                return
        else:
            value = str(value) if value is not None else ""
        self.property_value_changed.emit(page, pid, value)

    # -- row activation --

    def _on_row_activated(self, index: QModelIndex) -> None:
        """Emit page_activated when double-clicking id or title columns."""
        row = index.row()
        col = index.column()
        if row < 0 or row >= len(self._pages):
            return
        visible = self._visible_schema()
        if col < 0 or col >= len(visible):
            return
        ptype = self._prop_type(visible[col])
        if ptype in _MANDATORY_TYPES:
            self.page_activated.emit(self._pages[row])

    # -- header context menu --

    def _on_header_context_menu_requested(self, pos) -> None:
        header = self._table.view().horizontalHeader()
        section = header.logicalIndexAt(pos)
        visible = self._visible_schema()
        menu = QMenu(self)

        add_action = menu.addAction("Add property")
        add_action.triggered.connect(self.add_property_requested.emit)

        hidden = [
            p for p in self._schema
            if self._prop_id(p) in self._hidden_property_ids
        ]
        if hidden:
            show_sub = menu.addMenu("Show property")
            for prop in hidden:
                name = self._prop_name(prop)
                pid = self._prop_id(prop)
                act = show_sub.addAction(name)
                act.triggered.connect(
                    lambda checked=False, pid=pid: self._show_property(pid)
                )

        if 0 <= section < len(visible):
            prop = visible[section]
            pid = self._prop_id(prop)
            mandatory = self._is_mandatory(prop)

            visible_ids = [self._prop_id(p) for p in visible]
            vis_idx = visible_ids.index(pid) if pid in visible_ids else -1

            menu.addSeparator()
            move_left = menu.addAction("Move left")
            move_left.triggered.connect(lambda: self._move_column(vis_idx, vis_idx - 1))
            move_left.setEnabled(vis_idx > 0)
            move_right = menu.addAction("Move right")
            move_right.triggered.connect(lambda: self._move_column(vis_idx, vis_idx + 1))
            move_right.setEnabled(0 <= vis_idx < len(visible_ids) - 1)

            if not mandatory:
                hide_action = menu.addAction("Hide property")
                hide_action.triggered.connect(lambda: self._hide_property(pid))
                edit_action = menu.addAction("Edit property...")
                edit_action.triggered.connect(lambda: self.property_edit_requested.emit(prop))
                remove_action = menu.addAction("Remove property")
                remove_action.triggered.connect(lambda: self.property_remove_requested.emit(pid))

        menu.exec(header.mapToGlobal(pos))

    # -- hide/show --

    def _hide_property(self, property_id: str) -> None:
        self._hidden_property_ids.add(property_id)
        self._fill_table()

    def _show_property(self, property_id: str) -> None:
        self._hidden_property_ids.discard(property_id)
        self._fill_table()

    # -- move --

    def _move_column(self, from_vis: int, to_vis: int) -> None:
        """Move a column from one visible index to another."""
        visible = self._visible_schema()
        if from_vis < 0 or from_vis >= len(visible) or to_vis < 0 or to_vis >= len(visible):
            return
        if from_vis == to_vis:
            return
        visible_ids = [self._prop_id(p) for p in visible]
        moved_id = visible_ids.pop(from_vis)
        visible_ids.insert(to_vis, moved_id)
        hidden = [i for i in self._property_order if i in self._hidden_property_ids]
        self._property_order = visible_ids + hidden
        self._fill_table()
        self.property_order_changed.emit(tuple(self._property_order))

    # -- row context menu --

    def _on_context_menu_requested(self, pos) -> None:
        table_view = self._table.view()
        index = table_view.indexAt(pos)
        if not index.isValid() or index.row() >= len(self._pages):
            return
        page = self._pages[index.row()]
        menu = QMenu(self)
        add_action = menu.addAction("Add property")
        add_action.triggered.connect(self.add_property_requested.emit)
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(lambda: self.page_delete_requested.emit(page))
        menu.exec(table_view.viewport().mapToGlobal(pos))
