"""
Database list view: show databases as cards or a table with a View submenu.

Reusable view that displays a list of database-like objects (with .name and .pages).
Emits database_selected when the user opens one (click card or double-click row).
"""

from collections.abc import Sequence

from PySide6.QtCore import QEvent, QPoint, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QMenu,
    QScrollArea,
    QStackedWidget,
    QWidget,
)

from fern.infrastructure.pyside.components import Card, Table
from fern.infrastructure.pyside.utils import set_expanding

from .base import FernView

_CARD_MAX_WIDTH = 220
_CARD_MAX_HEIGHT = 100
_CARD_SPACING = 10
_CARDS_HORIZONTAL_PADDING = 64  # left + right padding (e.g. 32px each)


class DatabaseView(FernView):
    """
    Shows a list of databases as cards or a table. Reusable anywhere.

    Options menu provides a View submenu to switch between Cards and Table.
    Emits database_selected with the database object when one is opened.
    """

    view_id = "databases"
    database_selected = Signal(
        object
    )  # emitted with the database object (has .name, .pages)

    def __init__(
        self,
        databases: Sequence[object] = (),
        parent: QWidget | None = None,
    ) -> None:
        """
        Build the view and populate cards/table from the given databases.

        Args:
            databases: Sequence of objects with .name and .pages (e.g. OpenVaultUseCase.DatabaseOutput).
            parent: Optional parent widget.
        """
        self._databases = list(databases)
        super().__init__(parent)
        self.setObjectName("databaseView")
        self._build_content()

    def _build_content(self) -> None:
        """Create the cards/table stack and connect the options menu."""
        self.options_clicked.connect(self._on_options_clicked)
        self._content_stack = QStackedWidget()
        self._content_stack.setObjectName("vaultContentStack")
        scroll = QScrollArea()
        scroll.setObjectName("vaultContentScroll")
        scroll.setWidgetResizable(True)
        scroll.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        cards_widget = QWidget()
        cards_widget.setObjectName("vaultContentCards")
        self._cards_layout = QGridLayout(cards_widget)
        self._cards_layout.setSpacing(_CARD_SPACING)
        scroll.setWidget(cards_widget)
        self._cards_scroll = scroll
        scroll.viewport().installEventFilter(self)
        self._content_stack.addWidget(scroll)
        self._table_view = Table()
        self._table_view.view().doubleClicked.connect(self._on_table_double_clicked)
        self._content_stack.addWidget(self._table_view)
        self.content_layout().addWidget(self._content_stack)
        self._refresh_content()

    def set_databases(self, databases: Sequence[object]) -> None:
        """Update the list of databases. Each item must have .name and .pages (for count)."""
        self._databases = list(databases)
        self._refresh_content()

    def _refresh_content(self) -> None:
        """Rebuild cards and table from _databases."""
        self._fill_database_cards()
        self._fill_table_data()

    def _get_cards_column_count(self) -> int:
        """Number of card columns that fit in the current viewport width."""
        if not hasattr(self, "_cards_scroll") or self._cards_scroll is None:
            return 3
        w = self._cards_scroll.viewport().width() - _CARDS_HORIZONTAL_PADDING
        if w <= 0:
            return 1
        cell = _CARD_MAX_WIDTH + _CARD_SPACING
        return max(1, w // cell)

    def eventFilter(self, obj, event) -> bool:
        """Reflow cards when the scroll viewport is resized."""
        if (
            event.type() == QEvent.Type.Resize
            and hasattr(self, "_cards_scroll")
            and obj is self._cards_scroll.viewport()
        ):
            self._fill_database_cards()
        return super().eventFilter(obj, event)

    def _fill_database_cards(self) -> None:
        """Fill the card grid; column count depends on viewport width so cards stay visible."""
        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        cols = self._get_cards_column_count()
        for col in range(cols):
            self._cards_layout.setColumnStretch(col, 1)
        for i, db in enumerate(self._databases):
            name = getattr(db, "name", str(db))
            pages = getattr(db, "pages", ())
            page_count = len(pages)
            subtitle = f"{page_count} page{'s' if page_count != 1 else ''}"
            card = Card(title=name, subtitle=subtitle)
            set_expanding(card, horizontal=True, vertical=True)
            card.setMinimumWidth(120)
            card.setMinimumHeight(60)
            card.clicked.connect(
                lambda checked=False, idx=i: self._on_database_selected(idx)
            )
            row, col = divmod(i, cols)
            self._cards_layout.addWidget(card, row, col)
        # Push cards to the top: give extra vertical space to the row below the last cards
        num_rows = (len(self._databases) + cols - 1) // cols if cols else 0
        for r in range(num_rows + 1):
            self._cards_layout.setRowStretch(r, 1 if r == num_rows else 0)

    def _fill_table_data(self) -> None:
        """Fill the table with Name and Pages columns."""
        headers = ["Name", "Pages"]
        rows = []
        for db in self._databases:
            name = getattr(db, "name", str(db))
            pages = getattr(db, "pages", ())
            rows.append({"Name": name, "Pages": str(len(pages))})
        self._table_view.set_data(headers, rows)

    def _on_database_selected(self, index: int) -> None:
        """Emit database_selected for the database at the given index."""
        if index < 0 or index >= len(self._databases):
            return
        self.database_selected.emit(self._databases[index])

    def _on_table_double_clicked(self, index) -> None:
        """Handle double-click on a table row: emit database_selected for that row."""
        row = index.row()
        self._on_database_selected(row)

    def _on_options_clicked(self) -> None:
        """Show the options menu with View submenu (Cards / Table)."""
        menu = QMenu(self)
        menu.setObjectName("vaultContentOptionsMenu")
        view_submenu = menu.addMenu("View")
        cards_action = view_submenu.addAction("Cards")
        cards_action.setCheckable(True)
        cards_action.setChecked(self._content_stack.currentIndex() == 0)
        cards_action.triggered.connect(self._on_show_cards)
        table_action = view_submenu.addAction("Table")
        table_action.setCheckable(True)
        table_action.setChecked(self._content_stack.currentIndex() == 1)
        table_action.triggered.connect(self._on_show_table)
        btn = self._options_btn
        pos = btn.mapToGlobal(btn.rect().topLeft())
        menu_width = menu.sizeHint().width() or 160
        menu.exec(QPoint(pos.x() - menu_width, pos.y()))

    def _on_show_cards(self) -> None:
        """Switch the content stack to the cards view."""
        self._content_stack.setCurrentIndex(0)

    def _on_show_table(self) -> None:
        """Switch the content stack to the table view."""
        self._content_stack.setCurrentIndex(1)
