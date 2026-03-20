"""
Welcome screen: recent vaults list and Open / Create vault actions.

Shown when no vault is open. User can open an existing folder as a vault,
create a new vault, or double-click a recent vault to open it. Right-click
on a recent vault offers Open or Remove from list.
"""

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QShowEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from fern.infrastructure.controller import RecentVaultsController
from fern.infrastructure.pyside.components import show_error, show_toast


def _get_version() -> str:
    """Return package version from metadata, or a fallback when not installed."""
    try:
        from importlib.metadata import version

        return version("fern")
    except Exception:
        return "-"


class WelcomePage(QWidget):
    """
    Welcome screen with recent vaults on the left and Open / Create actions in the center.

    Emits open_vault_requested when the user opens or creates a vault (or double-clicks
    a recent entry). The parent (e.g. MainWindow) should add the path to recent and show
    the vault view.
    """

    open_vault_requested = Signal(Path)

    def __init__(self, recent_controller: RecentVaultsController) -> None:
        """
        Build the layout and load the recent vaults list.

        Args:
            controller: Application controller for recent vaults and create_vault.
        """
        super().__init__()
        self._recent_controller = recent_controller
        self.setObjectName("welcomePage")
        self._build_ui()
        self.refresh_recent()

    def _build_ui(self) -> None:
        """Create the splitter: left = recent vaults list, right = title and buttons."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Resizable splitter: left = recent vaults (top to bottom), right = welcome actions
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: recent vaults — full height, resizable width
        left = QFrame()
        left.setObjectName("welcomeSidebar")
        left.setMinimumWidth(200)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(10)

        recent_label = QLabel("Recent vaults")
        recent_label.setObjectName("welcomeSidebarTitle")
        recent_font = QFont()
        recent_font.setPointSize(11)
        recent_font.setWeight(QFont.Weight.DemiBold)
        recent_label.setFont(recent_font)
        left_layout.addWidget(recent_label)

        self._recent_list = QListWidget()
        self._recent_list.setObjectName("welcomeRecentList")
        self._recent_list.setSpacing(2)
        self._recent_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._recent_list.customContextMenuRequested.connect(
            self._on_recent_context_menu
        )
        self._recent_list.itemDoubleClicked.connect(self._on_recent_double_clicked)
        self._recent_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        left_layout.addWidget(self._recent_list, 1)

        splitter.addWidget(left)

        # Right: welcome text + Open / Create
        right = QWidget()
        right.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(48, 48, 48, 48)
        right_layout.setSpacing(24)

        right_layout.addStretch(1)

        title = QLabel("Fern")
        title.setObjectName("welcomeTitle")
        title_font = QFont()
        title_font.setPointSize(28)
        title_font.setWeight(QFont.Weight.Bold)
        title.setFont(title_font)
        right_layout.addWidget(title, 0, Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Your notes and pages, in one place.")
        subtitle.setObjectName("welcomeSubtitle")
        right_layout.addWidget(subtitle, 0, Qt.AlignmentFlag.AlignCenter)

        version_label = QLabel(f"v{_get_version()}")
        version_label.setObjectName("welcomeVersion")
        right_layout.addWidget(version_label, 0, Qt.AlignmentFlag.AlignCenter)

        right_layout.addSpacing(32)

        btn_open = QPushButton("Open folder as vault")
        btn_open.setObjectName("welcomePrimaryButton")
        btn_open.setMinimumHeight(36)
        btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_open.clicked.connect(self._on_open_vault)
        right_layout.addWidget(btn_open, 0, Qt.AlignmentFlag.AlignCenter)

        btn_create = QPushButton("Create new vault")
        btn_create.setObjectName("welcomeSecondaryButton")
        btn_create.setMinimumHeight(36)
        btn_create.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_create.clicked.connect(self._on_create_vault)
        right_layout.addWidget(btn_create, 0, Qt.AlignmentFlag.AlignCenter)

        right_layout.addStretch(1)

        splitter.addWidget(right)

        # Initial sizes: left 280px, right takes the rest
        splitter.setSizes([280, 640])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        content_layout.addWidget(splitter, 1)
        layout.addWidget(content)

    def showEvent(self, event: QShowEvent) -> None:
        """Refresh the recent vaults list when the welcome page is shown."""
        super().showEvent(event)
        self.refresh_recent()

    def refresh_recent(self) -> None:
        """Reload the recent vaults list from the controller (storage)."""
        self._recent_list.clear()
        for path in self._recent_controller.get_recent_vaults():
            if path.exists():
                item = QListWidgetItem(path.name)
                item.setData(Qt.ItemDataRole.UserRole, str(path))
                item.setToolTip(str(path))
                self._recent_list.addItem(item)

    def _on_recent_context_menu(self, position: object) -> None:
        """Show Open / Remove from list on right-click over a recent vault item."""
        viewport = self._recent_list.viewport()
        item = self._recent_list.itemAt(viewport.mapToParent(position))
        if not item:
            return
        path_str = item.data(Qt.ItemDataRole.UserRole)
        if not path_str:
            return
        path = Path(path_str)
        menu = QMenu(self)
        open_action = menu.addAction("Open")
        remove_action = menu.addAction("Remove from list")
        action = menu.exec(viewport.mapToGlobal(position))
        if action is open_action:
            self.open_vault_requested.emit(path)
        elif action is remove_action:
            self._recent_controller.remove_recent_vault(path)
            show_toast(self, "Removed from list")
            self.refresh_recent()

    def _on_recent_double_clicked(self, item: QListWidgetItem) -> None:
        """Open the vault when the user double-clicks a recent vault entry."""
        path_str = item.data(Qt.ItemDataRole.UserRole)
        if path_str:
            self.open_vault_requested.emit(Path(path_str))

    def _on_open_vault(self) -> None:
        """Show folder dialog and emit open_vault_requested with the selected path."""
        path = QFileDialog.getExistingDirectory(self, "Select folder to open as vault")
        if not path:
            return
        path = Path(path.strip().removeprefix("file://"))
        if not path.is_dir():
            show_error(self, "Please select a valid folder.", title="Invalid folder")
            return
        self.open_vault_requested.emit(path)

    def _on_create_vault(self) -> None:
        """Show folder dialog, create a new vault, and emit open_vault_requested with its path."""
        path = QFileDialog.getExistingDirectory(
            self, "Choose parent folder for new vault"
        )
        if not path:
            return
        path = Path(path.strip().removeprefix("file://"))
        if not path.is_dir():
            show_error(self, "Please select a valid folder.", title="Invalid folder")
            return
        vault_name = "New Vault"
        vault_path = self._recent_controller.create_vault(path, vault_name)
        if vault_path is None:
            show_error(
                self,
                f'"{vault_name}" already exists in that location. Choose another folder or rename.',
                title="Folder exists",
            )
            return
        self.open_vault_requested.emit(vault_path)
