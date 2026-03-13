"""Standalone window for viewing a single database.

Opened from the menu bar's Databases submenu. Contains a PagesView (table)
and an EditorView, with full CRUD support for pages and properties.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QMainWindow, QStackedWidget

from fern.infrastructure.controller import AppController
from fern.infrastructure.pyside.components import alert, confirm, show_toast

from .database_page_manager import DatabasePageManager
from .editor_view import EditorView
from .page_data import PageData
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

        self._db_mgr = DatabasePageManager(controller, vault_path)
        self._prop_mgr = PropertyManager(controller, vault_path)

        self.setWindowTitle(f"Fern — {database_name}")
        self.setMinimumSize(640, 420)
        self.resize(860, 580)

        save_shortcut = QShortcut(QKeySequence.StandardKey.Save, self)
        save_shortcut.activated.connect(self._on_editor_save)
        undo_shortcut = QShortcut(QKeySequence.StandardKey.Undo, self)
        undo_shortcut.activated.connect(self._on_undo_shortcut)

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._pages_view = PagesView()
        self._pages_view.back_requested.connect(self.close)
        self._pages_view.page_activated.connect(self._on_page_activated)
        self._pages_view.new_page_requested.connect(self._on_new_page)
        self._pages_view.page_delete_requested.connect(self._on_page_delete_from_table)
        self._pages_view.add_property_requested.connect(self._on_add_property)
        self._pages_view.property_value_changed.connect(self._on_property_value_changed)
        self._pages_view.property_edit_requested.connect(self._on_edit_property)
        self._pages_view.property_remove_requested.connect(self._on_remove_property)
        self._pages_view.save_order_requested.connect(self._on_save_order)
        self._stack.addWidget(self._pages_view)

        self._editor_view = EditorView()
        self._editor_view.back_requested.connect(self._on_editor_back)
        self._editor_view.save_requested.connect(self._on_editor_save)
        self._editor_view.delete_requested.connect(self._on_editor_delete)
        self._editor_view.add_property_requested.connect(self._on_add_property)
        self._editor_view.property_value_changed.connect(
            self._on_property_value_changed
        )
        self._stack.addWidget(self._editor_view)

        self._load_database(database_name)

    def _load_database(self, database_name: str) -> None:
        fresh = self._controller.open_vault_refresh(self._vault_path)
        db = self._db_mgr.find_database(fresh, database_name)
        if db is None:
            return

        self._db_mgr.current_database_name = database_name
        self._db_mgr.current_property_order = getattr(db, "property_order", ()) or ()
        pages = self._db_mgr.pages_from_output(db)
        self._pages_view.set_pages(
            pages,
            title=database_name,
            schema=getattr(db, "schema", ()),
            property_order=self._db_mgr.current_property_order,
        )

    # ── Navigation ───────────────────────────────────────────────────────────

    def _on_page_activated(self, page) -> None:
        self._editor_view.set_page(
            page, property_order=self._db_mgr.current_property_order, in_database=True
        )
        self._stack.setCurrentWidget(self._editor_view)

    def _on_editor_back(self) -> None:
        self._on_editor_save()
        self._stack.setCurrentWidget(self._pages_view)

    # ── Save ─────────────────────────────────────────────────────────────────

    def _on_editor_save(self) -> None:
        data = self._editor_view.get_edited_page_data()
        if data is None or not self._db_mgr.current_database_name:
            return
        page_id, title, content = data
        page_props = getattr(self._editor_view._page, "properties", None)
        self._db_mgr.save_page(page_id, title, content, properties=page_props)
        current = self._pages_view.get_pages()
        updated = []
        for p in current:
            if getattr(p, "id", 0) == page_id:
                p = PageData.from_use_case_page(p)
                p.title = title
                p.content = content
                p.update_mandatory_props(page_id, title)
            updated.append(p)
        self._pages_view.set_pages(updated)
        show_toast(self, "Saved")

    def _on_undo_shortcut(self) -> None:
        w = self.focusWidget()
        if w is not None and hasattr(w, "undo") and callable(getattr(w, "undo")):
            w.undo()

    # ── Delete ───────────────────────────────────────────────────────────────

    def _on_page_delete_from_table(self, page) -> None:
        if not self._db_mgr.current_database_name:
            return
        self._delete_page(
            getattr(page, "id", None),
            getattr(page, "title", "this page"),
            clear_editor=False,
        )

    def _on_editor_delete(self) -> None:
        data = self._editor_view.get_edited_page_data()
        if data is None or not self._db_mgr.current_database_name:
            return
        self._delete_page(data[0], data[1], clear_editor=True)

    def _delete_page(self, page_id: int, title: str, *, clear_editor: bool) -> None:
        if not confirm(
            self,
            "Delete page",
            f'Delete page "{title}"? This cannot be undone.',
            destructive=True,
            confirm_label="Delete",
            cancel_label="Cancel",
        ):
            return
        if not self._db_mgr.delete_page(page_id):
            return
        show_toast(self, "Page deleted")
        current = self._pages_view.get_pages()
        self._pages_view.set_pages(
            [p for p in current if getattr(p, "id", None) != page_id]
        )
        if clear_editor:
            self._editor_view.set_page(None)
            self._stack.setCurrentWidget(self._pages_view)

    # ── New page ─────────────────────────────────────────────────────────────

    def _on_new_page(self) -> None:
        if not self._db_mgr.current_database_name:
            return
        new_page = self._db_mgr.create_page(schema=self._pages_view.get_schema())
        current = self._pages_view.get_pages()
        self._pages_view.set_pages([*current, new_page])
        show_toast(self, "Page created")
        self._editor_view.set_page(
            new_page,
            property_order=self._db_mgr.current_property_order,
            in_database=True,
        )
        self._stack.setCurrentWidget(self._editor_view)

    # ── Property value change ────────────────────────────────────────────────

    def _on_property_value_changed(self, page, property_id: str, value) -> None:
        page_id = getattr(page, "id", None)
        if page_id is None or not self._db_mgr.current_database_name:
            return
        if not self._db_mgr.update_page_property(page_id, property_id, value):
            return
        for p in getattr(page, "properties", []):
            if getattr(p, "id", "") == property_id:
                p.value = value
                break
        self._pages_view._fill_table()

    # ── Property CRUD ────────────────────────────────────────────────────────

    def _on_add_property(self) -> None:
        if not self._db_mgr.current_database_name:
            return
        if not self._prop_mgr.add_property(self._db_mgr.current_database_name, self):
            return
        self._refresh()
        if self._stack.currentWidget() is self._editor_view:
            data = self._editor_view.get_edited_page_data()
            if data is not None:
                page_id = data[0]
                for p in self._pages_view.get_pages():
                    if getattr(p, "id", None) == page_id:
                        self._editor_view.set_page(
                            p,
                            property_order=self._db_mgr.current_property_order,
                            in_database=True,
                        )
                        break
        show_toast(self, "Property added")

    def _on_edit_property(self, prop) -> None:
        if not self._db_mgr.current_database_name:
            return
        if self._prop_mgr.edit_property(self._db_mgr.current_database_name, prop, self):
            self._refresh()
            show_toast(self, "Property updated")

    def _on_remove_property(self, property_id: str) -> None:
        if not self._db_mgr.current_database_name:
            return
        if self._prop_mgr.remove_property(
            self._db_mgr.current_database_name, property_id, self
        ):
            self._refresh()
            show_toast(self, "Property removed")

    def _on_save_order(self) -> None:
        if not self._db_mgr.current_database_name:
            alert(self, "Save column order", "Open a database first.")
            return
        try:
            order = self._pages_view.get_property_order_for_save()
        except RuntimeError as e:
            alert(self, "Save column order", f"Could not read column order:\n\n{e!s}")
            return
        if self._prop_mgr.save_order(self._db_mgr.current_database_name, order, self):
            self._refresh()

    # ── Refresh ──────────────────────────────────────────────────────────────

    def _refresh(self) -> None:
        result = self._db_mgr.refresh_pages_and_schema()
        if result is None:
            return
        pages, schema, prop_order = result
        self._pages_view.set_pages(
            pages,
            title=self._db_mgr.current_database_name,
            schema=schema,
            property_order=prop_order,
        )

    def closeEvent(self, event) -> None:
        if self._stack.currentWidget() is self._editor_view:
            self._on_editor_save()
        event.accept()
