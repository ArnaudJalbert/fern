"""Standalone window showing all databases; selecting one shows its pages in the same window."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QMainWindow, QStackedWidget, QVBoxLayout, QWidget

from fern.infrastructure.controller import AppController
from fern.infrastructure.pyside.components import show_error

from .database_view import DatabaseView
from .database_page_manager import DatabasePageManager
from .database_view_coordinator import DatabaseViewCoordinator
from .editor_view import EditorView
from .pages_view import PagesView
from .property_manager import PropertyManager


class DatabasesOverviewWindow(QMainWindow):
    """Window listing all databases; selecting one shows pages/editor in the same window."""

    def __init__(
        self,
        controller: AppController,
        vault_path: Path,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._controller = controller
        self._vault_path = vault_path

        self._database_page_manager = DatabasePageManager(controller, vault_path)
        self._property_manager = PropertyManager(controller, vault_path)

        self.setWindowTitle("Fern — Databases")
        self.setMinimumSize(640, 420)
        self.resize(800, 540)

        save_shortcut = QShortcut(QKeySequence.StandardKey.Save, self)
        save_shortcut.activated.connect(self._on_save_shortcut)
        undo_shortcut = QShortcut(QKeySequence.StandardKey.Undo, self)
        undo_shortcut.activated.connect(self._on_undo_shortcut)

        try:
            output = self._controller.open_vault_refresh(self._vault_path)
            databases = output.databases
        except Exception as exception:
            show_error(self, str(exception))
            databases = ()

        # Database list (first screen)
        self._main_stack = QStackedWidget()
        self.setCentralWidget(self._main_stack)

        self._database_view = DatabaseView(databases=databases)
        self._database_view.database_selected.connect(self._on_database_selected)
        self._main_stack.addWidget(self._database_view)

        # Content area (pages + editor, second screen)
        self._content_widget = QWidget()
        content_layout = QVBoxLayout(self._content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)

        self._content_stack = QStackedWidget()
        self._pages_view = PagesView()
        self._pages_view.back_requested.connect(self._on_pages_back)
        self._content_stack.addWidget(self._pages_view)

        self._editor_view = EditorView()
        self._content_stack.addWidget(self._editor_view)

        content_layout.addWidget(self._content_stack)
        self._main_stack.addWidget(self._content_widget)

        self._coordinator = DatabaseViewCoordinator(
            database_page_manager=self._database_page_manager,
            property_manager=self._property_manager,
            pages_view=self._pages_view,
            editor_view=self._editor_view,
            stack=self._content_stack,
            host=self,
        )
        self._coordinator.wire_signals()

    # ── Database selection ───────────────────────────────────────────────────

    def _on_database_selected(self, database) -> None:
        name = getattr(database, "name", str(database))
        self._load_database(name)
        self._main_stack.setCurrentWidget(self._content_widget)

    def _on_pages_back(self) -> None:
        self._main_stack.setCurrentWidget(self._database_view)

    def _load_database(self, database_name: str) -> None:
        fresh = self._controller.open_vault_refresh(self._vault_path)
        database = self._database_page_manager.find_database(fresh, database_name)
        if database is None:
            return
        self._database_page_manager.current_database_name = database_name
        self._database_page_manager.current_property_order = (
            getattr(database, "property_order", ()) or ()
        )
        self._database_page_manager.current_schema = (
            getattr(database, "schema", ()) or ()
        )
        pages = self._database_page_manager.pages_from_output(database)
        self._pages_view.set_pages(
            pages,
            title=database_name,
            schema=getattr(database, "schema", ()),
            property_order=self._database_page_manager.current_property_order,
        )
        self._content_stack.setCurrentWidget(self._pages_view)

    # ── Shortcuts ────────────────────────────────────────────────────────────

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
        if self._content_stack.currentWidget() is self._editor_view:
            self._coordinator.on_editor_save()
        event.accept()
