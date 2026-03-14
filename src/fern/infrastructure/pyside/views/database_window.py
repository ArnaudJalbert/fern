"""Standalone window for viewing a single database.

Opened from the menu bar's Databases submenu. Contains a PagesView (table)
and an EditorView, with full CRUD support for pages and properties.
All shared logic lives in DatabaseViewCoordinator.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QMainWindow, QStackedWidget

from fern.infrastructure.controller import AppController

from .database_page_manager import DatabasePageManager
from .database_view_coordinator import DatabaseViewCoordinator
from .editor_view import EditorView
from .pages_view import PagesView
from .property_manager import PropertyManager


class DatabaseWindow(QMainWindow):
    """A separate window showing a single database's pages and editor."""

    def __init__(
        self,
        controller: AppController,
        vault_path: Path,
        database_name: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._controller = controller
        self._vault_path = vault_path

        database_page_manager = DatabasePageManager(controller, vault_path)
        property_manager = PropertyManager(controller, vault_path)

        self.setWindowTitle(f"Fern — {database_name}")
        self.setMinimumSize(640, 420)
        self.resize(860, 580)

        save_shortcut = QShortcut(QKeySequence.StandardKey.Save, self)
        save_shortcut.activated.connect(self._on_save_shortcut)
        undo_shortcut = QShortcut(QKeySequence.StandardKey.Undo, self)
        undo_shortcut.activated.connect(self._on_undo_shortcut)

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._pages_view = PagesView()
        self._pages_view.back_requested.connect(self.close)
        self._stack.addWidget(self._pages_view)

        self._editor_view = EditorView()
        self._stack.addWidget(self._editor_view)

        self._coordinator = DatabaseViewCoordinator(
            database_page_manager=database_page_manager,
            property_manager=property_manager,
            pages_view=self._pages_view,
            editor_view=self._editor_view,
            stack=self._stack,
            host=self,
        )
        self._coordinator.wire_signals()

        self._load_database(database_name, database_page_manager)

    def _load_database(
        self,
        database_name: str,
        database_page_manager: DatabasePageManager,
    ) -> None:
        fresh = self._controller.open_vault_refresh(self._vault_path)
        database = database_page_manager.find_database(fresh, database_name)
        if database is None:
            return
        database_page_manager.current_database_name = database_name
        database_page_manager.current_property_order = (
            getattr(database, "property_order", ()) or ()
        )
        database_page_manager.current_schema = getattr(database, "schema", ()) or ()
        pages = database_page_manager.pages_from_output(database)
        self._pages_view.set_pages(
            pages,
            title=database_name,
            schema=getattr(database, "schema", ()),
            property_order=database_page_manager.current_property_order,
        )

    def _on_save_shortcut(self) -> None:
        self._coordinator.on_editor_save()

    def _on_undo_shortcut(self) -> None:
        widget = self.focusWidget()
        if (
            widget is not None
            and hasattr(widget, "undo")
            and callable(getattr(widget, "undo"))
        ):
            widget.undo()

    def closeEvent(self, event) -> None:
        if self._stack.currentWidget() is self._editor_view:
            self._coordinator.on_editor_save()
        event.accept()
