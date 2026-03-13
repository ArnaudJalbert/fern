"""Vault view: file-tree sidebar + content stack orchestrator.

The sidebar shows the vault's file system as a tree. Folders containing a
database.json marker are treated as databases (opened in DatabaseView →
PagesView). Regular .md files are opened in the editor. A context menu on
folders lets the user create a new database.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QEvent, QModelIndex, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMenu,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from fern.application.use_cases.open_vault import OpenVaultUseCase
from fern.infrastructure.controller import AppController

from .database_page_manager import DatabasePageManager
from .database_window import DatabaseWindow
from .editor_view import EditorView
from .page_data import PageData
from .pages_view import PagesView
from .property_manager import PropertyManager
from .root_page_manager import RootPageManager
from .vault_tree_model import FILE_PATH_ROLE, IS_DATABASE_ROLE, VaultTreeModel
from fern.infrastructure.pyside.actions import get_tree_actions
from fern.infrastructure.pyside.components import alert, confirm, show_toast
from fern.infrastructure.pyside.utils import (
    add_colored_action,
    load_icon,
    reveal_in_file_explorer,
)


@dataclass
class MenuContext:
    """What menu bar actions are currently available in the vault view."""

    can_new_page: bool = False
    can_new_database: bool = False
    can_new_folder: bool = False
    can_add_property: bool = False
    can_save_order: bool = False
    can_delete: bool = False
    can_reveal_in_explorer: bool = False


class VaultView(QWidget):
    """File-tree sidebar + content stack. Delegates to managers for business logic."""

    def __init__(
        self,
        controller: AppController,
        vault_path: Path,
        vault_output: OpenVaultUseCase.Output,
    ) -> None:
        super().__init__()
        self.setObjectName("vaultView")
        self._controller = controller
        self._vault_path = vault_path
        self._vault_output = vault_output

        self._root_mgr = RootPageManager(controller, vault_path)
        self._db_mgr = DatabasePageManager(controller, vault_path)
        self._prop_mgr = PropertyManager(controller, vault_path)

        self._current_root_page: PageData | None = None

        self._build_ui()

    # ── UI construction ──────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(0)
        splitter.setObjectName("vaultSplitter")

        splitter.addWidget(self._build_sidebar())
        splitter.addWidget(self._build_content_stack())
        splitter.setSizes([220, 680])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter, 1)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("vaultSidebar")
        sidebar.setMinimumWidth(180)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        self._tree_model = VaultTreeModel(
            self._vault_path,
            is_database_folder=self._controller.is_database_folder,
            database_marker_name=self._controller.database_marker_name,
            parent=self,
        )
        root_index = self._tree_model.setRootPath(str(self._vault_path))

        self._tree_view = QTreeView()
        self._tree_view.setObjectName("vaultSidebarTree")
        self._tree_view.setModel(self._tree_model)
        self._tree_view.setRootIndex(root_index)
        self._tree_view.setHeaderHidden(True)
        self._tree_view.setAnimated(True)
        self._tree_view.setIndentation(10)
        self._tree_view.setExpandsOnDoubleClick(True)

        for col in range(1, self._tree_model.columnCount()):
            self._tree_view.setColumnHidden(col, True)

        self._tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree_view.customContextMenuRequested.connect(self._on_tree_context_menu)
        self._tree_view.clicked.connect(self._on_tree_clicked)
        self._tree_view.doubleClicked.connect(self._on_tree_double_clicked)
        self._tree_view.installEventFilter(self)

        sidebar_layout.addWidget(self._tree_view, 1)

        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(6, 2, 6, 6)
        bottom_bar.setSpacing(0)

        self._add_btn = QPushButton()
        self._add_btn.setObjectName("vaultSidebarAddButton")
        self._add_btn.setIcon(load_icon("plus"))
        self._add_btn.setFixedSize(22, 22)
        from PySide6.QtCore import QSize

        self._add_btn.setIconSize(QSize(14, 14))
        self._add_btn.setToolTip("New...")
        self._add_btn.clicked.connect(self._on_add_button_clicked)
        bottom_bar.addWidget(self._add_btn)
        bottom_bar.addStretch()

        sidebar_layout.addLayout(bottom_bar)

        return sidebar

    def _build_content_stack(self) -> QFrame:
        self._view_stack = QStackedWidget()

        self._empty_view = QWidget()
        empty_layout = QVBoxLayout(self._empty_view)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label = QLabel("Select an item from the sidebar")
        label.setObjectName("vaultEmptyPlaceholder")
        label.setStyleSheet("color: #71717a; font-size: 14px;")
        empty_layout.addWidget(label)
        self._view_stack.addWidget(self._empty_view)

        self._pages_view = PagesView()
        self._pages_view.back_requested.connect(self._on_pages_back)
        self._pages_view.page_activated.connect(self._on_page_activated)
        self._pages_view.new_page_requested.connect(self._on_new_db_page)
        self._pages_view.page_delete_requested.connect(
            self._on_db_page_delete_from_table
        )
        self._pages_view.add_property_requested.connect(self._on_add_property)
        self._pages_view.property_value_changed.connect(self._on_property_value_changed)
        self._pages_view.property_edit_requested.connect(self._on_edit_property)
        self._pages_view.property_remove_requested.connect(self._on_remove_property)
        self._pages_view.save_order_requested.connect(self._on_save_order)
        self._view_stack.addWidget(self._pages_view)

        self._editor_view = EditorView()
        self._editor_view.back_requested.connect(self._on_editor_back)
        self._editor_view.save_requested.connect(self._on_editor_save)
        self._editor_view.delete_requested.connect(self._on_editor_delete)
        self._editor_view.add_property_requested.connect(self._on_add_property)
        self._editor_view.property_value_changed.connect(
            self._on_property_value_changed
        )
        self._view_stack.addWidget(self._editor_view)

        content = QFrame()
        content.setObjectName("vaultContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(self._view_stack, 1)
        return content

    # ── Tree sidebar ─────────────────────────────────────────────────────────

    def _path_from_index(self, index: QModelIndex) -> Path | None:
        raw = self._tree_model.data(index, FILE_PATH_ROLE)
        if raw is None:
            return None
        return Path(raw)

    def _is_database(self, index: QModelIndex) -> bool:
        return bool(self._tree_model.data(index, IS_DATABASE_ROLE))

    def _on_tree_clicked(self, index: QModelIndex) -> None:
        path = self._path_from_index(index)
        if path is None:
            return

        if self._is_database(index):
            self._open_database_by_path(path)
            return

        if path.is_file() and path.suffix == ".md":
            self._open_root_page(path)

    def _on_tree_double_clicked(self, index: QModelIndex) -> None:
        path = self._path_from_index(index)
        if path is None:
            return
        if self._is_database(index):
            self._open_database_by_path(path)

    def eventFilter(self, obj, event) -> bool:
        """Handle Enter key: open databases and .md files; expand/collapse folders."""
        if obj is self._tree_view and event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                index = self._tree_view.currentIndex()
                if index.isValid():
                    path = self._path_from_index(index)
                    if path is not None:
                        if self._is_database(index):
                            self._open_database_by_path(path)
                            return True
                        if path.is_file() and path.suffix == ".md":
                            self._open_root_page(path)
                            return True
                        if path.is_dir():
                            self._tree_view.setExpanded(
                                index, not self._tree_view.isExpanded(index)
                            )
                            return True
                return True
        return super().eventFilter(obj, event)

    def _on_tree_context_menu(self, pos) -> None:
        index = self._tree_view.indexAt(pos)
        path = self._path_from_index(index) if index.isValid() else None
        clicked_is_db = index.isValid() and self._is_database(index)

        if path is not None and path.is_file() and path.suffix == ".md":
            selection_type = "file"
        elif clicked_is_db and path is not None:
            selection_type = "database"
        elif path is not None and path.is_dir():
            selection_type = "folder"
        else:
            selection_type = "empty"

        folder = (
            (path if path is not None and path.is_dir() else path.parent)
            if path is not None
            else self._vault_path
        )
        reveal_path = path if path is not None else self._vault_path

        menu = QMenu(self)
        for item in get_tree_actions(selection_type):
            if item.is_separator:
                menu.addSeparator()
                continue
            cb = self._get_tree_action_callback(
                item.id, path, folder, reveal_path, selection_type
            )
            if cb is None:
                continue
            if item.color:
                add_colored_action(menu, item.label, item.color, cb)
            else:
                action = menu.addAction(item.label)
                action.triggered.connect(cb)

        if not menu.isEmpty():
            menu.exec(self._tree_view.viewport().mapToGlobal(pos))

    def _get_tree_action_callback(
        self,
        action_id: str,
        path: Path | None,
        folder: Path,
        reveal_path: Path,
        selection_type: str,
    ) -> Callable[[], None] | None:
        """Return the callback for a tree context menu action (used by the shared action registry)."""
        if action_id == "open":
            if selection_type == "file" and path is not None:
                return lambda: self._open_root_page(path)
            if selection_type == "database" and path is not None:
                return lambda: self._open_database_by_path(path)
            return None
        if action_id == "open_new_window" and path is not None:
            return lambda: self._open_database_in_window(path)
        if action_id == "reveal":
            return lambda: reveal_in_file_explorer(reveal_path)
        if action_id == "new_page":
            if selection_type == "empty":
                return self._on_new_root_page
            return lambda: self._create_page_in(folder)
        if action_id == "new_database":
            return lambda: self._create_database_in(folder)
        if action_id == "new_folder":
            return lambda: self._create_folder_in(folder)
        if action_id == "delete" and path is not None:
            return lambda: self._delete_file(path)
        return None

    def _open_database_by_path(self, db_path: Path) -> None:
        """Open a database folder by its absolute path."""
        try:
            rel = str(db_path.relative_to(self._vault_path))
        except ValueError:
            return

        fresh = self._controller.open_vault_refresh(self._vault_path)
        self._vault_output = fresh

        db = self._db_mgr.find_database(fresh, rel)
        if db is None:
            return

        self._current_root_page = None
        self._db_mgr.current_database_name = rel
        self._db_mgr.current_property_order = getattr(db, "property_order", ()) or ()
        pages = self._db_mgr.pages_from_output(db)
        self._pages_view.set_pages(
            pages,
            title=rel,
            schema=getattr(db, "schema", ()),
            property_order=self._db_mgr.current_property_order,
        )
        self._view_stack.setCurrentWidget(self._pages_view)

    def _open_root_page(self, path: Path) -> None:
        """Open a .md file in the editor."""
        page = self._root_mgr.load(path)
        if page is None:
            return
        self._current_root_page = page
        self._db_mgr.current_database_name = ""
        self._editor_view.set_page(page)
        self._view_stack.setCurrentWidget(self._editor_view)

    def _create_database_in(self, folder: Path) -> None:
        """Create a database.json in the given folder."""
        try:
            rel = str(folder.relative_to(self._vault_path))
        except ValueError:
            return
        if rel == ".":
            rel = ""

        name, ok = QInputDialog.getText(
            self, "New database", "Database folder name:", text="New Database"
        )
        if not ok or not name.strip():
            return

        target_rel = f"{rel}/{name.strip()}" if rel else name.strip()
        created = self._controller.create_database(self._vault_path, target_rel)
        if not created:
            alert(self, "New database", "A database already exists there.")
            return
        show_toast(self, "Database created")
        fresh = self._controller.open_vault_refresh(self._vault_path)
        self._vault_output = fresh

    def _create_page_in(self, folder: Path) -> None:
        """Create a new .md page in the given folder."""
        name, ok = QInputDialog.getText(
            self, "New page", "Page title:", text="Untitled"
        )
        if not ok or not name.strip():
            return

        safe_name = name.strip().replace("/", "-")
        target = folder / f"{safe_name}.md"
        if target.exists():
            alert(self, "New page", f'"{safe_name}.md" already exists.')
            return

        import frontmatter

        post = frontmatter.Post("", id=1, properties=[])
        target.write_text(frontmatter.dumps(post), encoding="utf-8")
        show_toast(self, "Page created")
        self._open_root_page(target)

    def _create_folder_in(self, parent: Path) -> None:
        """Create a new subfolder."""
        name, ok = QInputDialog.getText(
            self, "New folder", "Folder name:", text="New Folder"
        )
        if not ok or not name.strip():
            return

        target = parent / name.strip()
        if target.exists():
            alert(self, "New folder", f'"{name.strip()}" already exists.')
            return
        target.mkdir(parents=True, exist_ok=True)
        show_toast(self, "Folder created")

    def _delete_file(self, path: Path) -> None:
        """Delete a .md file after confirmation."""
        if not confirm(
            self,
            "Delete file",
            f'Delete "{path.name}"? This cannot be undone.',
            destructive=True,
            confirm_label="Delete",
            cancel_label="Cancel",
        ):
            return
        try:
            path.unlink()
        except OSError:
            return
        show_toast(self, "File deleted")
        if self._current_root_page and self._current_root_page.path == path:
            self._current_root_page = None
            self._editor_view.set_page(None)
            self._view_stack.setCurrentWidget(self._empty_view)

    def _open_database_in_window(self, db_path: Path) -> None:
        """Open a database in a separate window."""
        try:
            rel = str(db_path.relative_to(self._vault_path))
        except ValueError:
            return
        win = DatabaseWindow(self._controller, self._vault_path, rel)
        win.show()
        win.raise_()
        if not hasattr(self, "_db_windows"):
            self._db_windows: list[DatabaseWindow] = []
        self._db_windows = [w for w in self._db_windows if w.isVisible()]
        self._db_windows.append(win)

    # ── Sidebar add button ──────────────────────────────────────────────────

    def _on_add_button_clicked(self) -> None:
        """Show add menu: same create actions as tree context for empty (no reveal)."""
        menu = QMenu(self)
        folder = self._vault_path
        for item in get_tree_actions("empty"):
            if item.is_separator or item.id == "reveal":
                continue
            cb = self._get_tree_action_callback(item.id, None, folder, folder, "empty")
            if cb is None:
                continue
            if item.color:
                add_colored_action(menu, item.label, item.color, cb)
            else:
                action = menu.addAction(item.label)
                action.triggered.connect(cb)
        pos = self._add_btn.mapToGlobal(self._add_btn.rect().topLeft())
        menu.exec(pos)

    def _on_new_root_page(self) -> None:
        page = self._root_mgr.create()
        show_toast(self, "Page created")
        self._current_root_page = page
        self._db_mgr.current_database_name = ""
        self._editor_view.set_page(page)
        self._view_stack.setCurrentWidget(self._editor_view)

    # ── Navigation ───────────────────────────────────────────────────────────

    def _on_pages_back(self) -> None:
        self._view_stack.setCurrentWidget(self._empty_view)

    def _on_page_activated(self, page) -> None:
        self._editor_view.set_page(
            page, property_order=self._db_mgr.current_property_order, in_database=True
        )
        self._view_stack.setCurrentWidget(self._editor_view)

    # ── Editor: back / save / delete ─────────────────────────────────────────

    def _on_editor_back(self) -> None:
        self._on_editor_save()
        if self._current_root_page is not None:
            self._current_root_page = None
            self._editor_view.set_page(None)
            self._view_stack.setCurrentWidget(self._empty_view)
        else:
            self._view_stack.setCurrentWidget(self._pages_view)

    def _on_editor_save(self) -> None:
        data = self._editor_view.get_edited_page_data()
        if data is None:
            return
        page_id, title, content = data

        if self._current_root_page is not None:
            try:
                updated = self._root_mgr.save(self._current_root_page, title, content)
                self._current_root_page = updated
                self._editor_view._page = updated
                show_toast(self, "Saved")
            except OSError:
                pass
            return

        if not self._db_mgr.current_database_name:
            return
        page_props = getattr(self._editor_view._page, "properties", None)
        self._db_mgr.save_page(page_id, title, content, properties=page_props)
        current = self._pages_view.get_pages()
        updated_pages = []
        for p in current:
            if getattr(p, "id", 0) == page_id:
                p = PageData.from_use_case_page(p)
                p.title = title
                p.content = content
                p.update_mandatory_props(page_id, title)
            updated_pages.append(p)
        self._pages_view.set_pages(updated_pages)
        show_toast(self, "Saved")

    def _on_editor_delete(self) -> None:
        if self._current_root_page is not None and self._current_root_page.path:
            if not confirm(
                self,
                "Delete file",
                f'Delete "{self._current_root_page.path.name}"? This cannot be undone.',
                destructive=True,
                confirm_label="Delete",
                cancel_label="Cancel",
            ):
                return
            self._root_mgr.delete(self._current_root_page.path)
            show_toast(self, "File deleted")
            self._current_root_page = None
            self._editor_view.set_page(None)
            self._view_stack.setCurrentWidget(self._empty_view)
            return

        data = self._editor_view.get_edited_page_data()
        if data is None or not self._db_mgr.current_database_name:
            return
        self._delete_db_page(data[0], data[1], clear_editor=True)

    # ── Database page delete (shared by editor and table) ────────────────────

    def _on_db_page_delete_from_table(self, page) -> None:
        if not self._db_mgr.current_database_name:
            return
        self._delete_db_page(
            getattr(page, "id", None),
            getattr(page, "title", "this page"),
            clear_editor=False,
        )

    def _delete_db_page(self, page_id: int, title: str, *, clear_editor: bool) -> None:
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
            self._view_stack.setCurrentWidget(self._pages_view)

    # ── New database page ────────────────────────────────────────────────────

    def _on_new_db_page(self) -> None:
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
        self._view_stack.setCurrentWidget(self._editor_view)

    # ── Property value change (from editor or table) ─────────────────────────

    def _on_property_value_changed(self, page, property_id: str, value) -> None:
        page_id = getattr(page, "id", None)
        for p in getattr(page, "properties", []):
            if getattr(p, "id", "") == property_id:
                p.value = value
                break
        if self._db_mgr.current_database_name and page_id is not None:
            if not self._db_mgr.update_page_property(page_id, property_id, value):
                return
            self._pages_view._fill_table()
        # Root page: no schema persist; value is in memory and saved on editor save

    # ── Property CRUD (delegated to PropertyManager) ─────────────────────────

    def _on_add_property(self) -> None:
        if not self._db_mgr.current_database_name:
            return
        if not self._prop_mgr.add_property(self._db_mgr.current_database_name, self):
            return
        self._refresh_db_pages()
        if self._view_stack.currentWidget() is self._editor_view:
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
            self._refresh_db_pages()
            show_toast(self, "Property updated")

    def _on_remove_property(self, property_id: str) -> None:
        if not self._db_mgr.current_database_name:
            return
        if self._prop_mgr.remove_property(
            self._db_mgr.current_database_name, property_id, self
        ):
            self._refresh_db_pages()
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
            self._refresh_db_pages()

    # ── Refresh helper ───────────────────────────────────────────────────────

    def _refresh_db_pages(self) -> None:
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

    # ── Public API (used by MainWindow) ──────────────────────────────────────

    def get_menu_context(self) -> MenuContext:
        """Return which menu bar actions are currently available."""
        ctx = MenuContext(
            can_new_page=True,
            can_new_database=True,
            can_new_folder=True,
            can_add_property=bool(self._db_mgr.current_database_name),
            can_save_order=bool(self._db_mgr.current_database_name),
            can_delete=False,
            can_reveal_in_explorer=False,
        )
        index = self._tree_view.currentIndex()
        if index.isValid():
            path = self._path_from_index(index)
            if path is not None and path.exists():
                ctx.can_reveal_in_explorer = True
            if path is not None and path.is_file() and path.suffix == ".md":
                ctx.can_delete = True
        if not ctx.can_delete and self._view_stack.currentWidget() is self._editor_view:
            if self._current_root_page is not None or (
                self._db_mgr.current_database_name
                and self._editor_view.get_edited_page_data()
            ):
                ctx.can_delete = True
        if not ctx.can_delete and self._view_stack.currentWidget() is self._pages_view:
            if self._pages_view.get_selected_page() is not None:
                ctx.can_delete = True
        return ctx

    def menu_new_page(self) -> None:
        """Create a new page (at vault root or in current database)."""
        if (
            self._db_mgr.current_database_name
            and self._view_stack.currentWidget() is self._pages_view
        ):
            self._on_new_db_page()
        else:
            self._on_new_root_page()

    def menu_new_database(self) -> None:
        """Create a new database in the vault."""
        self._create_database_in(self._vault_path)

    def menu_new_folder(self) -> None:
        """Create a new folder (at vault root or under selected tree item)."""
        index = self._tree_view.currentIndex()
        folder = self._vault_path
        if index.isValid():
            path = self._path_from_index(index)
            if path is not None:
                folder = path if path.is_dir() else path.parent
        self._create_folder_in(folder)

    def menu_add_property(self) -> None:
        """Add a property to the current database."""
        self._on_add_property()

    def menu_save_order(self) -> None:
        """Save column order for the current database."""
        self._on_save_order()

    def menu_reveal_in_explorer(self) -> None:
        """Reveal the selected tree item (or vault root) in the system file manager."""
        index = self._tree_view.currentIndex()
        path = self._path_from_index(index) if index.isValid() else None
        target = path if path is not None and path.exists() else self._vault_path
        reveal_in_file_explorer(target)

    def menu_delete(self) -> None:
        """Delete the selected file or page."""
        index = self._tree_view.currentIndex()
        if index.isValid():
            path = self._path_from_index(index)
            if path is not None and path.is_file() and path.suffix == ".md":
                self._delete_file(path)
                return
        if self._view_stack.currentWidget() is self._editor_view:
            self._on_editor_delete()
            return
        if self._view_stack.currentWidget() is self._pages_view:
            page = self._pages_view.get_selected_page()
            if page is not None:
                self._on_db_page_delete_from_table(page)

    def save_pending_state(self) -> None:
        """Persist editor content if the editor is visible (e.g. before closing)."""
        if self._view_stack.currentWidget() is self._editor_view:
            self._on_editor_save()
