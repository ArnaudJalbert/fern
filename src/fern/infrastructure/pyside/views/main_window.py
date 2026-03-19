"""
Main application window: welcome page and vault view stack.

Owns the menu bar (Vault > Open..., Databases > ...) and switches between the
welcome screen and the vault view when a vault is opened. Opens the most
recently used vault on startup if available.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Protocol

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent, QKeyEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFrame,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from fern.infrastructure.controller import RecentVaultsController, VaultController
from fern.infrastructure.controller.factories.controller_factory import (
    ControllerFactory,
)
from fern.infrastructure.pyside.actions import (
    get_edit_actions,
    get_edit_actions_for_command_palette,
)
from fern.infrastructure.pyside.components import (
    CommandItem,
    CommandPalette,
    show_toast,
)
from fern.infrastructure.pyside.utils import add_colored_action

from .database_window import DatabaseWindow
from .databases_overview_window import DatabasesOverviewWindow
from .vault_view import VaultView
from .welcome_page import WelcomePage


class Undoable(Protocol):
    """Protocol for widgets that support undo operation."""

    def undo(self) -> None: ...


class MainWindow(QMainWindow):
    """
    Top-level window for the Fern application.

    Shows the welcome page by default. The Vault menu allows opening a folder
    as a vault. The Databases menu lists all databases in the current vault and
    opens them in separate windows.
    """

    def __init__(
        self,
        recent_controller: RecentVaultsController,
        controller_factory: ControllerFactory,
    ) -> None:
        super().__init__()
        self._controller_factory = controller_factory
        self._recent_controller = recent_controller
        self._vault_controller: VaultController | None = None
        self._vault_path: Path | None = None
        self._child_windows: list[QMainWindow] = []
        self.setWindowTitle("Fern")
        self.setMinimumSize(900, 600)
        self.resize(1280, 840)

        self._build_menu_bar()
        self._build_shortcuts()

        self._stack = QStackedWidget()
        self._palette_page = self._build_palette_page()
        self._stack.addWidget(self._palette_page)
        self._welcome = WelcomePage(recent_controller)
        self._welcome.open_vault_requested.connect(self._on_open_vault_requested)
        self._stack.addWidget(self._welcome)
        self.setCentralWidget(self._stack)
        self._stack.setCurrentWidget(self._welcome)
        self._index_before_palette = 1

        recent = self._recent_controller.get_recent_vaults()
        if recent:
            path = recent[0]
            if path.is_dir():
                self._show_vault(path)

    def _build_menu_bar(self) -> None:
        menu_bar = self.menuBar()

        vault_menu = menu_bar.addMenu("Vault")
        open_action = vault_menu.addAction("Open...")
        open_action.triggered.connect(self._on_vault_open)

        self._databases_menu = menu_bar.addMenu("Databases")
        self._databases_menu.addAction("See databases...").triggered.connect(
            self._on_see_databases
        )
        self._databases_menu.aboutToShow.connect(self._update_databases_menu)

        self._edit_menu = menu_bar.addMenu("Edit")
        self._edit_menu.aboutToShow.connect(self._update_edit_menu)

        self._view_menu = menu_bar.addMenu("View")
        cmd_palette_action = self._view_menu.addAction("Command Palette...")
        shortcut_str = "Meta+P" if sys.platform == "darwin" else "Ctrl+P"
        cmd_palette_action.setShortcut(QKeySequence(shortcut_str))
        cmd_palette_action.triggered.connect(self._on_command_palette)

    def _build_shortcuts(self) -> None:
        save_shortcut = QShortcut(QKeySequence.StandardKey.Save, self)
        save_shortcut.activated.connect(self._on_save_shortcut)
        undo_shortcut = QShortcut(QKeySequence.StandardKey.Undo, self)
        undo_shortcut.activated.connect(self._on_undo_shortcut)
        # Cmd+P on macOS, Ctrl+P on Windows/Linux
        shortcut_str = "Meta+P" if sys.platform == "darwin" else "Ctrl+P"
        palette_shortcut = QShortcut(QKeySequence(shortcut_str), self)
        palette_shortcut.activated.connect(self._on_command_palette)

    def _build_palette_page(self) -> QWidget:
        """Full-size overlay page with command palette centered in the middle."""
        page = QFrame()
        page.setObjectName("commandPalettePage")
        page.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        page.setStyleSheet(
            """
            QFrame#commandPalettePage {
                background-color: rgba(24, 24, 27, 0.85);
            }
            """
        )
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        palette = CommandPalette(page)
        palette.closed.connect(self._on_palette_closed)
        layout.addWidget(palette, 0, Qt.AlignmentFlag.AlignCenter)
        self._palette = palette

        def keyPressEvent(event: QKeyEvent) -> None:
            if event.key() == Qt.Key.Key_Escape:
                self._on_palette_closed()
                return
            super(QFrame, page).keyPressEvent(event)

        page.keyPressEvent = keyPressEvent
        return page

    def _on_palette_closed(self) -> None:
        self._stack.setCurrentIndex(self._index_before_palette)

    def _on_save_shortcut(self) -> None:
        w = self._stack.currentWidget()
        if isinstance(w, VaultView):
            w.save_pending_state()

    def _on_undo_shortcut(self) -> None:
        w = self.focusWidget()
        if w is not None and hasattr(w, "undo") and callable(getattr(w, "undo")):
            from typing import cast

            undoable = cast(Undoable, w)
            undoable.undo()

    def _on_vault_open(self) -> None:
        """Handle Vault > Open...: show the welcome page."""
        self.setWindowTitle("Fern")
        self._welcome.refresh_recent()
        self._stack.setCurrentWidget(self._welcome)

    def _on_open_vault_requested(self, vault_path: Path) -> None:
        """Handle open from welcome page: add to recent and show vault view."""
        self._recent_controller.add_recent_vault(vault_path)
        self._welcome.refresh_recent()
        self._show_vault(vault_path)

    def _show_vault(self, vault_path: Path) -> None:
        from fern.infrastructure.controller import VaultNotFoundError
        from fern.infrastructure.pyside.components import show_error

        # Create a new vault controller for this vault
        vault_controller = self._controller_factory.create_vault_controller(vault_path)
        try:
            output = vault_controller.open_vault()
        except VaultNotFoundError as e:
            detail = f"{e.message}\n\nPath: {vault_path}" if vault_path else e.message
            show_error(self, detail, title="Open vault")
            return
        current = self._stack.currentWidget()
        if isinstance(current, VaultView):
            current.save_pending_state()
            self._stack.removeWidget(current)
        self._vault_controller = vault_controller
        self._vault_path = vault_path
        self.setWindowTitle(f"Fern — {output.vault_name}")
        vault_view = VaultView(vault_controller, vault_path, output)
        self._stack.addWidget(vault_view)
        self._stack.setCurrentWidget(vault_view)
        show_toast(self, "Vault opened")

    # ── Edit menu ────────────────────────────────────────────────────────────

    def _vault_view(self) -> VaultView | None:
        """Return the current vault view if the stack is showing one."""
        w = self._stack.currentWidget()
        return w if isinstance(w, VaultView) else None

    def _update_edit_menu(self) -> None:
        """Rebuild Edit menu from the shared action registry (context-sensitive)."""
        self._edit_menu.clear()
        v = self._vault_view()
        ctx = v.get_menu_context() if v is not None else None
        runner = v
        for ra in get_edit_actions(ctx, runner):
            if ra.is_separator:
                self._edit_menu.addSeparator()
                continue
            if ra.spec.color:
                action = add_colored_action(
                    self._edit_menu, ra.label, ra.spec.color, ra.callback
                )
            else:
                action = self._edit_menu.addAction(ra.label)
                action.triggered.connect(ra.callback)
            action.setEnabled(ra.available)

    def _build_command_palette_actions(self) -> list[CommandItem]:
        """Build command palette items from the shared action registry + app-level actions."""
        v = self._vault_view()
        ctx = v.get_menu_context() if v is not None else None
        runner = v
        extra = [
            ("Open...", "", self._on_vault_open),
            ("See databases...", "", self._on_see_databases),
        ]
        items = get_edit_actions_for_command_palette(ctx, runner, extra_actions=extra)
        return [CommandItem(label, shortcut, cb) for label, shortcut, cb in items]

    def _on_command_palette(self) -> None:
        """Open the command palette as a centered page in the middle of the window."""
        self._index_before_palette = self._stack.currentIndex()
        self._palette.set_actions(self._build_command_palette_actions())
        self._stack.setCurrentWidget(self._palette_page)

    # ── Databases menu ───────────────────────────────────────────────────────

    def _update_databases_menu(self) -> None:
        """Update Databases menu: enable/disable See databases... and refresh database list."""
        self._databases_menu.clear()
        see_action = self._databases_menu.addAction("See databases...")
        see_action.triggered.connect(self._on_see_databases)

        if self._vault_path is None:
            see_action.setEnabled(False)
            return

        see_action.setEnabled(True)
        try:
            output = self._vault_controller.open_vault_refresh()  # type: ignore
        except Exception as e:
            from fern.infrastructure.pyside.components import show_error

            show_error(self, str(e))
            return
        if output.databases:
            self._databases_menu.addSeparator()
            for db in output.databases:
                name = getattr(db, "name", str(db))
                action = self._databases_menu.addAction(name)
                action.triggered.connect(
                    lambda checked=False, n=name: self._open_database_window(n)
                )

    def _on_see_databases(self) -> None:
        """Open the databases overview in a new window (like Vault > Open... opens welcome)."""
        if self._vault_path is None:
            return
        self._cleanup_child_windows()
        win = DatabasesOverviewWindow(self._vault_controller, self._vault_path)  # type: ignore
        win.show()
        win.raise_()
        win.activateWindow()
        self._child_windows.append(win)

    def _open_database_window(self, database_name: str) -> None:
        """Open a single database in a new window."""
        if self._vault_path is None:
            return
        self._cleanup_child_windows()
        win = DatabaseWindow(self._vault_controller, self._vault_path, database_name)  # type: ignore
        win.show()
        win.raise_()
        self._child_windows.append(win)

    def _cleanup_child_windows(self) -> None:
        self._child_windows = [w for w in self._child_windows if w.isVisible()]

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def closeEvent(self, event: QCloseEvent) -> None:
        """Save any pending state before closing."""
        current = self._stack.currentWidget()
        if isinstance(current, VaultView):
            current.save_pending_state()
        for win in self._child_windows:
            if win.isVisible():
                win.close()
        event.accept()

    def open_vault(self, vault_path: Path) -> None:
        """Programmatically open a vault (e.g. for tests)."""
        self._recent_controller.add_recent_vault(vault_path)
        self._welcome.refresh_recent()
        self._show_vault(vault_path)
