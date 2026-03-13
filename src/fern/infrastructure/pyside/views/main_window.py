"""
Main application window: welcome page and vault view stack.

Owns the menu bar (e.g. Vault > Open...) and switches between the welcome
screen and the vault view when a vault is opened. Opens the most recently
used vault on startup if available.
"""

from pathlib import Path

from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
)

from fern.infrastructure.controller import AppController

from .vault_view import VaultView
from .welcome_page import WelcomePage


class MainWindow(QMainWindow):
    """
    Top-level window for the Fern application.

    Shows the welcome page by default. The Vault menu allows opening a folder
    as a vault. When a vault is opened, the vault view (sidebar + content stack)
    is shown. Only one vault view is kept in the stack at a time.
    """

    def __init__(self, controller: AppController) -> None:
        """
        Build the window, menu bar, and welcome page; optionally open the most recent vault.

        Args:
            controller: Application controller for opening vaults and managing recent list.
        """
        super().__init__()
        self._controller = controller
        self.setWindowTitle("Fern")
        self.setMinimumSize(720, 480)
        self.resize(920, 640)

        self._build_menu_bar()

        self._stack = QStackedWidget()
        self._welcome = WelcomePage(controller)
        self._welcome.open_vault_requested.connect(self._on_open_vault_requested)
        self._stack.addWidget(self._welcome)
        self.setCentralWidget(self._stack)

        # Open most recently used vault by default if any
        recent = self._controller.get_recent_vaults()
        if recent:
            path = recent[0]
            if path.is_dir():
                self._show_vault(path)

    def _build_menu_bar(self) -> None:
        """Add the Vault menu with Open... action."""
        menu_bar = self.menuBar()
        vault_menu = menu_bar.addMenu("Vault")
        open_action = vault_menu.addAction("Open...")
        open_action.triggered.connect(self._on_vault_open)

    def _on_vault_open(self) -> None:
        """Handle Vault > Open...: show folder dialog, add to recent, show vault view."""
        path = QFileDialog.getExistingDirectory(self, "Open folder as vault")
        if not path:
            return
        path = Path(path.strip().removeprefix("file://"))
        if not path.is_dir():
            QMessageBox.warning(self, "Invalid folder", "Please select a valid folder.")
            return
        self._controller.add_recent_vault(path)
        self._welcome.refresh_recent()
        self._show_vault(path)

    def _on_open_vault_requested(self, vault_path: Path) -> None:
        """Handle open from welcome page: add to recent and show vault view."""
        self._controller.add_recent_vault(vault_path)
        self._welcome.refresh_recent()
        self._show_vault(vault_path)

    def _show_vault(self, vault_path: Path) -> None:
        """
        Load the vault and show the vault view.

        Replaces any existing vault view in the stack so only one vault is shown.
        """
        output = self._controller.open_vault(vault_path)
        if not output.success:
            return
        # Replace existing vault view if any (keep only one vault view in the stack)
        current = self._stack.currentWidget()
        if isinstance(current, VaultView):
            current.save_pending_state()
            self._stack.removeWidget(current)
        self.setWindowTitle(f"Fern — {output.vault_name}")
        vault_view = VaultView(self._controller, vault_path, output)
        self._stack.addWidget(vault_view)
        self._stack.setCurrentWidget(vault_view)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Save any pending state (editor, property order) before closing."""
        current = self._stack.currentWidget()
        if isinstance(current, VaultView):
            current.save_pending_state()
        event.accept()

    def open_vault(self, vault_path: Path) -> None:
        """
        Programmatically open a vault (e.g. for tests).

        Adds the path to recent, refreshes the welcome list, and shows the vault view.
        """
        self._controller.add_recent_vault(vault_path)
        self._welcome.refresh_recent()
        self._show_vault(vault_path)
