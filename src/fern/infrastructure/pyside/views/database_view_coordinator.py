"""Coordinator for database page/property CRUD shared across host views.

DatabaseWindow, DatabasesOverviewWindow, and VaultView all need the same
page CRUD, property CRUD, editor save/back, and refresh logic. This
coordinator encapsulates all of it so each host only wires signals and
delegates to `self._coordinator`.
"""

from __future__ import annotations

from PySide6.QtWidgets import QStackedWidget, QWidget

from fern.infrastructure.pyside.components import confirm, show_error, show_toast

from .database_page_manager import DatabasePageManager
from .editor_view import EditorView
from .page_data import PageData
from .pages_view import PagesView
from .property_manager import PropertyManager


class DatabaseViewCoordinator:
    """Shared page/property operations for any view hosting a PagesView + EditorView."""

    def __init__(
        self,
        *,
        database_page_manager: DatabasePageManager,
        property_manager: PropertyManager,
        pages_view: PagesView,
        editor_view: EditorView,
        stack: QStackedWidget,
        host: QWidget,
    ) -> None:
        """Initialize with the views and managers this coordinator operates on.

        Args:
            database_page_manager: Manages page CRUD on the current database.
            property_manager: Manages schema property CRUD.
            pages_view: The PagesView widget (table).
            editor_view: The EditorView widget (title + content + properties).
            stack: The QStackedWidget containing pages_view and editor_view.
            host: The parent widget for dialogs and toasts.
        """
        self._database_page_manager = database_page_manager
        self._property_manager = property_manager
        self._pages_view = pages_view
        self._editor_view = editor_view
        self._stack = stack
        self._host = host

    def wire_signals(self) -> None:
        """Connect PagesView and EditorView signals to coordinator methods."""
        self._pages_view.page_activated.connect(self.on_page_activated)
        self._pages_view.new_page_requested.connect(self.on_new_page)
        self._pages_view.page_delete_requested.connect(self.on_page_delete_from_table)
        self._pages_view.add_property_requested.connect(self.on_add_property)
        self._pages_view.property_value_changed.connect(self.on_property_value_changed)
        self._pages_view.property_edit_requested.connect(self.on_edit_property)
        self._pages_view.property_remove_requested.connect(self.on_remove_property)
        self._pages_view.save_order_requested.connect(self.on_save_order)

        self._editor_view.back_requested.connect(self.on_editor_back)
        self._editor_view.save_requested.connect(self.on_editor_save)
        self._editor_view.delete_requested.connect(self.on_editor_delete)
        self._editor_view.add_property_requested.connect(self.on_add_property)
        self._editor_view.property_value_changed.connect(self.on_property_value_changed)

    # ── Navigation ───────────────────────────────────────────────────────────

    def on_page_activated(self, page) -> None:
        """Open a page in the editor."""
        self._editor_view.set_page(
            page,
            property_order=self._database_page_manager.current_property_order,
            schema=self._database_page_manager.current_schema,
            in_database=True,
        )
        self._stack.setCurrentWidget(self._editor_view)

    def on_editor_back(self) -> None:
        """Save and go back to the pages table."""
        self.on_editor_save()
        self._stack.setCurrentWidget(self._pages_view)

    # ── Save ─────────────────────────────────────────────────────────────────

    def on_editor_save(self) -> None:
        """Save the current editor state to disk and update the pages list."""
        data = self._editor_view.get_edited_page_data()
        if data is None or not self._database_page_manager.current_database_name:
            return
        page_id, title, content = data
        page_properties = getattr(self._editor_view._page, "properties", None)
        self._database_page_manager.save_page(
            page_id,
            title,
            content,
            properties=page_properties,
        )
        current = self._pages_view.get_pages()
        updated = []
        for page in current:
            if getattr(page, "id", 0) == page_id:
                page = PageData.from_use_case_page(page)
                page.title = title
                page.content = content
                page.update_mandatory_props(page_id, title)
            updated.append(page)
        self._pages_view.set_pages(updated)
        show_toast(self._host, "Saved")

    # ── Delete ───────────────────────────────────────────────────────────────

    def on_page_delete_from_table(self, page) -> None:
        """Handle delete request from the table context menu."""
        if not self._database_page_manager.current_database_name:
            return
        self._delete_page(
            getattr(page, "id", None),
            getattr(page, "title", "this page"),
            clear_editor=False,
        )

    def on_editor_delete(self) -> None:
        """Handle delete request from the editor view."""
        data = self._editor_view.get_edited_page_data()
        if data is None or not self._database_page_manager.current_database_name:
            return
        self._delete_page(data[0], data[1], clear_editor=True)

    def _delete_page(self, page_id: int, title: str, *, clear_editor: bool) -> None:
        if not confirm(
            self._host,
            "Delete page",
            f'Delete page "{title}"? This cannot be undone.',
            destructive=True,
            confirm_label="Delete",
            cancel_label="Cancel",
        ):
            return
        if not self._database_page_manager.delete_page(page_id, parent=self._host):
            return
        show_toast(self._host, "Page deleted")
        current = self._pages_view.get_pages()
        self._pages_view.set_pages(
            [page for page in current if getattr(page, "id", None) != page_id]
        )
        if clear_editor:
            self._editor_view.set_page(None)
            self._stack.setCurrentWidget(self._pages_view)

    # ── New page ─────────────────────────────────────────────────────────────

    def on_new_page(self) -> None:
        """Create a new page, add it to the table, and open in editor."""
        if not self._database_page_manager.current_database_name:
            return
        new_page = self._database_page_manager.create_page(
            schema=self._pages_view.get_schema(),
        )
        current = self._pages_view.get_pages()
        self._pages_view.set_pages([*current, new_page])
        show_toast(self._host, "Page created")
        self._editor_view.set_page(
            new_page,
            property_order=self._database_page_manager.current_property_order,
            schema=self._database_page_manager.current_schema,
            in_database=True,
        )
        self._stack.setCurrentWidget(self._editor_view)

    # ── Property value change ────────────────────────────────────────────────

    def on_property_value_changed(self, page, property_id: str, value) -> None:
        """Persist a property value change from the table or editor."""
        page_id = getattr(page, "id", None)
        if page_id is None or not self._database_page_manager.current_database_name:
            return
        if not self._database_page_manager.update_page_property(
            page_id,
            property_id,
            value,
            parent=self._host,
        ):
            return
        for page_property in getattr(page, "properties", []):
            if getattr(page_property, "id", "") == property_id:
                page_property.value = value
                break
        self._pages_view._fill_table()

    # ── Property CRUD ────────────────────────────────────────────────────────

    def on_add_property(self) -> None:
        """Show the add-property dialog, persist, and refresh."""
        if not self._database_page_manager.current_database_name:
            return
        if not self._property_manager.add_property(
            self._database_page_manager.current_database_name,
            self._host,
        ):
            return
        self.refresh()
        if self._stack.currentWidget() is self._editor_view:
            self._refresh_editor_after_schema_change()
        show_toast(self._host, "Property added")

    def on_edit_property(self, prop) -> None:
        """Show the edit-property dialog, persist, and refresh."""
        if not self._database_page_manager.current_database_name:
            return
        if self._property_manager.edit_property(
            self._database_page_manager.current_database_name,
            prop,
            self._host,
        ):
            self.refresh()
            show_toast(self._host, "Property updated")

    def on_remove_property(self, property_id: str) -> None:
        """Confirm, remove the property from schema and pages, and refresh."""
        if not self._database_page_manager.current_database_name:
            return
        if self._property_manager.remove_property(
            self._database_page_manager.current_database_name,
            property_id,
            self._host,
        ):
            self.refresh()
            show_toast(self._host, "Property removed")

    def on_save_order(self) -> None:
        """Persist the current column order."""
        if not self._database_page_manager.current_database_name:
            show_error(
                self._host,
                "Open a database first.",
                title="Save column order",
            )
            return
        try:
            order = self._pages_view.get_property_order_for_save()
        except RuntimeError as exception:
            show_error(self._host, str(exception), title="Save column order")
            return
        if self._property_manager.save_order(
            self._database_page_manager.current_database_name,
            order,
            self._host,
        ):
            self.refresh()

    # ── Refresh ──────────────────────────────────────────────────────────────

    def refresh(self) -> None:
        """Reload the vault and refresh the pages table."""
        result = self._database_page_manager.refresh_pages_and_schema(
            parent=self._host,
        )
        if result is None:
            return
        pages, schema, property_order = result
        self._pages_view.set_pages(
            pages,
            title=self._database_page_manager.current_database_name,
            schema=schema,
            property_order=property_order,
        )

    def _refresh_editor_after_schema_change(self) -> None:
        """Re-set the current page in the editor with fresh schema data."""
        data = self._editor_view.get_edited_page_data()
        if data is None:
            return
        page_id = data[0]
        for page in self._pages_view.get_pages():
            if getattr(page, "id", None) == page_id:
                self._editor_view.set_page(
                    page,
                    property_order=self._database_page_manager.current_property_order,
                    schema=self._database_page_manager.current_schema,
                    in_database=True,
                )
                break
