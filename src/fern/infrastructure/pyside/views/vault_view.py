"""
Vault view: sidebar (Databases) and main content stack (databases / pages / editor).

When a vault is open, this view shows the sidebar and manages the stack of
DatabaseView, PagesView, and EditorView. Handles navigation, save, create,
and delete page flows via the controller.
"""

from pathlib import Path
from types import SimpleNamespace

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from fern.application.use_cases.open_vault import OpenVaultUseCase
from fern.infrastructure.controller import AppController
from fern.infrastructure.pyside.components import PropertySettingsWidget
from fern.infrastructure.pyside.utils import load_icon, property_type_key

from .database_view import DatabaseView
from .editor_view import EditorView
from .pages_view import PagesView


class VaultView(QWidget):
    """
    Main view when a vault is open: sidebar with "Databases" and content stack.

    Content stack shows: database list (cards/table) -> pages table -> page editor.
    Coordinates saving, creating, and deleting pages through the controller and
    updates the pages list when the editor content or title changes.
    """

    def __init__(
        self,
        controller: AppController,
        vault_path: Path,
        vault_output: OpenVaultUseCase.Output,
    ) -> None:
        """
        Build the sidebar and content stack and wire navigation/save/delete.

        Args:
            controller: Application controller for save_page, create_page, delete_page.
            vault_path: Path to the vault root on disk.
            vault_output: Result of open_vault (vault_name, databases with pages).
        """
        super().__init__()
        self.setObjectName("vaultView")
        self._controller = controller
        self._vault_path = vault_path
        self._vault_output = vault_output
        self._current_database_name: str = ""
        self._current_property_order: tuple = ()
        self._build_ui()

    def _build_ui(self) -> None:
        """Create the splitter (sidebar + content stack) and all child views."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(0)
        splitter.setObjectName("vaultSplitter")

        # Left: sidebar with single "Databases" item
        sidebar = QFrame()
        sidebar.setObjectName("vaultSidebar")
        sidebar.setMinimumWidth(220)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 20, 20, 20)
        sidebar_layout.setSpacing(10)

        self._nav_list = QListWidget()
        self._nav_list.setObjectName("vaultSidebarNav")
        self._nav_list.setSpacing(2)
        self._nav_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        db_item = QListWidgetItem("Databases")
        db_icon = load_icon("databases")
        if not db_icon.isNull():
            db_item.setIcon(db_icon)
        self._nav_list.addItem(db_item)
        self._nav_list.setCurrentItem(db_item)
        self._nav_list.itemSelectionChanged.connect(self._on_sidebar_selection_changed)
        sidebar_layout.addWidget(self._nav_list, 1)

        splitter.addWidget(sidebar)

        # Right: stack of views (databases list | pages list | editor)
        self._view_stack = QStackedWidget()
        self._database_view = DatabaseView(databases=self._vault_output.databases)
        self._database_view.database_selected.connect(self._on_database_selected)
        self._view_stack.addWidget(self._database_view)
        self._pages_view = PagesView()
        self._pages_view.back_requested.connect(self._on_pages_back_requested)
        self._pages_view.page_activated.connect(self._on_page_activated)
        self._pages_view.new_page_requested.connect(self._on_new_page_requested)
        self._pages_view.page_delete_requested.connect(self._on_page_delete_requested)
        self._pages_view.add_property_requested.connect(self._on_add_property_requested)
        self._pages_view.property_value_changed.connect(
            self._on_page_property_value_changed
        )
        self._pages_view.property_edit_requested.connect(
            self._on_property_edit_requested
        )
        self._pages_view.property_remove_requested.connect(
            self._on_property_remove_requested
        )
        self._pages_view.save_order_requested.connect(
            self._on_save_order_requested
        )
        self._view_stack.addWidget(self._pages_view)
        self._editor_view = EditorView()
        self._editor_view.back_requested.connect(self._on_editor_back_requested)
        self._editor_view.save_requested.connect(self._on_editor_save_requested)
        self._editor_view.delete_requested.connect(self._on_editor_delete_requested)
        self._editor_view.property_value_changed.connect(
            self._on_page_property_value_changed
        )
        self._view_stack.addWidget(self._editor_view)
        content = QFrame()
        content.setObjectName("vaultContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(self._view_stack, 1)
        splitter.addWidget(content)

        splitter.setSizes([260, 640])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter, 1)

    def _on_sidebar_selection_changed(self) -> None:
        """Called when sidebar selection changes; content is already the databases view."""
        pass

    @staticmethod
    def _update_mandatory_props(props: list, page_id: int, title: str) -> list:
        """Update id/title property values in a page's property list."""
        updated = []
        has_id = False
        has_title = False
        for p in props:
            pid = getattr(p, "id", "")
            if pid == "id":
                updated.append(SimpleNamespace(
                    id="id", name="ID", type="id", value=page_id, mandatory=True,
                ))
                has_id = True
            elif pid == "title":
                updated.append(SimpleNamespace(
                    id="title", name="Title", type="title", value=title, mandatory=True,
                ))
                has_title = True
            else:
                updated.append(p)
        if not has_id:
            updated.insert(0, SimpleNamespace(
                id="id", name="ID", type="id", value=page_id, mandatory=True,
            ))
        if not has_title:
            updated.insert(1 if has_id else 0, SimpleNamespace(
                id="title", name="Title", type="title", value=title, mandatory=True,
            ))
        return updated

    def _on_database_selected(self, database) -> None:
        """Switch to the pages view and show pages for the selected database."""
        name = getattr(database, "name", str(database))
        # Refresh vault so we get latest data (including saved property order)
        fresh = self._controller.open_vault_refresh(self._vault_path)
        self._vault_output = fresh
        self._database_view.set_databases(fresh.databases)
        db = None
        for d in fresh.databases:
            if getattr(d, "name", "") == name:
                db = d
                break
        if db is None:
            return
        raw_pages = getattr(db, "pages", ())
        schema = getattr(db, "schema", ())
        pages = [
            SimpleNamespace(
                id=p.id,
                title=p.title,
                content=p.content,
                properties=[
                    SimpleNamespace(
                        id=prop.id, name=prop.name, type=prop.type,
                        value=prop.value,
                        mandatory=getattr(prop, "mandatory", False),
                    )
                    for prop in getattr(p, "properties", ())
                ],
            )
            for p in raw_pages
        ]
        self._current_database_name = name
        self._current_property_order = getattr(db, "property_order", ()) or ()
        self._pages_view.set_pages(
            pages, title=name, schema=schema, property_order=self._current_property_order
        )
        self._view_stack.setCurrentWidget(self._pages_view)

    def save_pending_state(self) -> None:
        """Persist editor content if the editor is visible (e.g. before closing)."""
        current = self._view_stack.currentWidget()
        if current is self._editor_view:
            self._on_editor_save_requested()

    def _on_pages_back_requested(self) -> None:
        """Switch back from pages view to the database list."""
        self._view_stack.setCurrentWidget(self._database_view)

    def _on_page_activated(self, page) -> None:
        """Load the selected page into the editor and switch to the editor view."""
        self._editor_view.set_page(page, property_order=self._current_property_order)
        self._view_stack.setCurrentWidget(self._editor_view)

    def _on_editor_back_requested(self) -> None:
        """Save any pending editor changes, then switch back to the pages list."""
        self._on_editor_save_requested()
        self._view_stack.setCurrentWidget(self._pages_view)

    def _on_editor_save_requested(self) -> None:
        """Persist current editor content via controller and refresh the pages table."""
        data = self._editor_view.get_edited_page_data()
        if data is None or not self._current_database_name:
            return
        page_id, title, content = data
        self._controller.save_page(
            self._vault_path,
            self._current_database_name,
            page_id,
            title,
            content,
        )
        # Update the pages list so the table shows the new title
        current = self._pages_view.get_pages()
        updated = []
        for p in current:
            props = list(getattr(p, "properties", []))
            pid = getattr(p, "id", 0)
            ptitle = getattr(p, "title", "")
            pcontent = getattr(p, "content", "")
            if pid == page_id:
                ptitle = title
                pcontent = content
                props = self._update_mandatory_props(props, page_id, title)
            updated.append(
                SimpleNamespace(id=pid, title=ptitle, content=pcontent, properties=props)
            )
        self._pages_view.set_pages(updated)

    def _on_editor_delete_requested(self) -> None:
        """Delete the current page after confirmation, then return to pages list."""
        data = self._editor_view.get_edited_page_data()
        if data is None or not self._current_database_name:
            return
        self._delete_page_by_id_and_title(data[0], data[1], clear_editor=True)

    def _on_page_delete_requested(self, page) -> None:
        """Delete the given page (from table right-click) after confirmation."""
        if not self._current_database_name:
            return
        page_id = getattr(page, "id", None)
        title = getattr(page, "title", "this page")
        self._delete_page_by_id_and_title(page_id, title, clear_editor=False)

    def _delete_page_by_id_and_title(
        self, page_id: int, title: str, *, clear_editor: bool = False
    ) -> None:
        """
        Confirm with the user, delete the page via controller, update the list, optionally clear editor.

        Args:
            page_id: ID of the page to delete.
            title: Title used in the confirmation dialog.
            clear_editor: If True, clear the editor and switch to pages view (used when deleting from editor).
        """
        reply = QMessageBox.question(
            self,
            "Delete page",
            f'Delete page "{title}"? This cannot be undone.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        out = self._controller.delete_page(
            self._vault_path,
            self._current_database_name,
            page_id,
        )
        if not out.deleted:
            return
        current = self._pages_view.get_pages()
        updated = [
            SimpleNamespace(
                id=getattr(p, "id", 0),
                title=getattr(p, "title", ""),
                content=getattr(p, "content", ""),
                properties=list(getattr(p, "properties", [])),
            )
            for p in current
            if getattr(p, "id", None) != page_id
        ]
        self._pages_view.set_pages(updated)
        if clear_editor:
            self._editor_view.set_page(None)
            self._view_stack.setCurrentWidget(self._pages_view)

    def _on_page_property_value_changed(
        self, page, property_id: str, value: bool | str
    ) -> None:
        """Persist the property change and update the page in memory."""
        if not self._current_database_name:
            return
        page_id = getattr(page, "id", None)
        if page_id is None:
            return
        out = self._controller.update_page_property(
            self._vault_path,
            self._current_database_name,
            page_id,
            property_id,
            value,
        )
        if not out.success:
            return
        props = getattr(page, "properties", [])
        new_props = []
        found = False
        for p in props:
            if getattr(p, "id", "") == property_id:
                new_props.append(
                    SimpleNamespace(
                        id=p.id,
                        name=getattr(p, "name", p.id),
                        type=getattr(p, "type", "boolean"),
                        value=value,
                        mandatory=getattr(p, "mandatory", False),
                    )
                )
                found = True
            else:
                new_props.append(p)
        if not found:
            new_props.append(
                SimpleNamespace(
                    id=property_id, name=property_id, type="boolean",
                    value=value, mandatory=False,
                )
            )
        updated_page = SimpleNamespace(
            id=page_id,
            title=getattr(page, "title", ""),
            content=getattr(page, "content", ""),
            properties=new_props,
        )
        current = self._pages_view.get_pages()
        self._pages_view._pages = [
            updated_page if getattr(p, "id", None) == page_id else p for p in current
        ]
        self._pages_view._fill_table()

    def _on_add_property_requested(self) -> None:
        """Show property settings dialog (name + type), add property via controller, refresh."""
        if not self._current_database_name:
            return
        form = PropertySettingsWidget(name="Done", type_key="boolean", parent=self)
        parsed = self._run_property_settings_dialog("Add property", form)
        if parsed is None:
            return
        name, type_key = parsed
        if not name:
            return
        slug = (
            "".join(c if c.isalnum() or c == "_" else "_" for c in name.strip()).lower()
            or "prop"
        )
        slug = slug.strip("_") or "prop"
        if slug in ("id", "title"):
            slug = f"{slug}_prop"
        out = self._controller.add_property(
            self._vault_path,
            self._current_database_name,
            slug,
            name,
            type_key,
        )
        if not out.success:
            QMessageBox.warning(
                self, "Add property", "A property with that id already exists."
            )
            return
        self._refresh_current_pages_and_schema()

    def _run_property_settings_dialog(
        self, title: str, form: PropertySettingsWidget
    ) -> tuple[str, str] | None:
        """Show a modal dialog with the property settings widget. Returns (name, type_key) if OK, None if Cancel."""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout(dialog)
        layout.addWidget(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        result: list[tuple[str, str] | None] = [None]

        def on_accept() -> None:
            result[0] = (form.get_name(), form.get_type_key())
            dialog.accept()

        buttons.accepted.connect(on_accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.exec()
        return result[0]

    def _refresh_current_pages_and_schema(self) -> None:
        """Reload vault and update pages view for the current database."""
        fresh = self._controller.open_vault_refresh(self._vault_path)
        for db in fresh.databases:
            if db.name == self._current_database_name:
                raw_pages = db.pages
                schema = db.schema
                pages = [
                    SimpleNamespace(
                        id=p.id,
                        title=p.title,
                        content=p.content,
                        properties=[
                            SimpleNamespace(
                                id=prop.id,
                                name=prop.name,
                                type=prop.type,
                                value=prop.value,
                                mandatory=getattr(prop, "mandatory", False),
                            )
                            for prop in getattr(p, "properties", ())
                        ],
                    )
                    for p in raw_pages
                ]
                self._current_property_order = getattr(db, "property_order", ()) or ()
                self._pages_view.set_pages(
                    pages,
                    title=db.name,
                    schema=schema,
                    property_order=self._current_property_order,
                )
                break

    def _on_property_edit_requested(self, prop) -> None:
        """Show property settings dialog (name + type), update and refresh."""
        if not self._current_database_name:
            return
        property_id = getattr(prop, "id", "")
        current_name = getattr(prop, "name", property_id)
        type_key = property_type_key(getattr(prop, "type", "string"))
        form = PropertySettingsWidget(
            name=current_name, type_key=type_key, parent=self
        )
        parsed = self._run_property_settings_dialog("Edit property", form)
        if parsed is None:
            return
        name, new_type_key = parsed
        name = name or current_name
        out = self._controller.update_property(
            self._vault_path,
            self._current_database_name,
            property_id,
            new_name=name,
            new_type=new_type_key,
        )
        if not out.success:
            QMessageBox.warning(
                self, "Edit property", "Could not update the property."
            )
            return
        self._refresh_current_pages_and_schema()

    def _on_save_order_requested(self) -> None:
        """Save the current column order to the database (user clicked Save column order)."""
        if not self._current_database_name:
            QMessageBox.warning(
                self,
                "Save column order",
                "Open a database first.",
            )
            return
        try:
            order = self._pages_view.get_property_order_for_save()
        except RuntimeError as e:
            QMessageBox.warning(
                self,
                "Save column order",
                f"Could not read column order:\n\n{e!s}",
            )
            return
        vault_path = Path(self._vault_path).resolve()
        try:
            out = self._controller.update_property_order(
                vault_path,
                self._current_database_name,
                order,
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Save column order",
                f"Save failed: {e!s}",
            )
            return
        if not out.success:
            QMessageBox.warning(
                self,
                "Save column order",
                "Save failed (success=False).",
            )
            return
        self._refresh_current_pages_and_schema()
        QMessageBox.information(
            self,
            "Save column order",
            "Column order saved.",
        )

    def _on_property_remove_requested(self, property_id: str) -> None:
        """Confirm and remove the property, then refresh."""
        if not self._current_database_name:
            return
        reply = QMessageBox.question(
            self,
            "Remove property",
            "Remove this property from the database? It will be removed from all pages.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        out = self._controller.remove_property(
            self._vault_path, self._current_database_name, property_id
        )
        if not out.success:
            QMessageBox.warning(
                self, "Remove property", "Could not remove the property."
            )
            return
        self._refresh_current_pages_and_schema()

    def _on_new_page_requested(self) -> None:
        """Create a new page in the current database and open it in the editor."""
        if not self._current_database_name:
            return
        out = self._controller.create_page(
            self._vault_path,
            self._current_database_name,
            title="Untitled",
            content="",
        )
        new_page = SimpleNamespace(
            id=out.page_id,
            title=out.title,
            content=out.content,
            properties=[
                SimpleNamespace(id="id", name="ID", type="id", value=out.page_id, mandatory=True),
                SimpleNamespace(id="title", name="Title", type="title", value=out.title, mandatory=True),
            ],
        )
        current = self._pages_view.get_pages()
        self._pages_view.set_pages([*current, new_page])
        self._editor_view.set_page(
            new_page, property_order=self._current_property_order
        )
        self._view_stack.setCurrentWidget(self._editor_view)
