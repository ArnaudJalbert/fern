"""Custom QFileSystemModel subclass that marks database folders.

Folders containing a database marker are displayed with a special icon and role
so the tree view can distinguish them from regular folders.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFileSystemModel

from fern.infrastructure.pyside.utils import load_icon

IS_DATABASE_ROLE = Qt.ItemDataRole.UserRole + 100
FILE_PATH_ROLE = Qt.ItemDataRole.UserRole + 101


class VaultTreeModel(QFileSystemModel):
    """File system model that annotates database folders with custom roles."""

    def __init__(
        self,
        vault_path: Path,
        is_database_folder: Callable[[Path], bool],
        database_marker_name: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._vault_path = vault_path
        self._is_database_folder = is_database_folder
        self._database_marker_name = database_marker_name
        self._db_icon: QIcon | None = None

        self.setReadOnly(True)
        self.setFilter(
            self.filter()
            | self.filter().Dirs
            | self.filter().Files
            | self.filter().NoDotAndDotDot
        )
        name_filters = ["*.md"]
        self.setNameFilters(name_filters)
        self.setNameFilterDisables(False)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        path = Path(self.filePath(index))

        if role == IS_DATABASE_ROLE:
            return path.is_dir() and self._is_database_folder(path)

        if role == FILE_PATH_ROLE:
            return str(path)

        if role == Qt.ItemDataRole.DecorationRole and index.column() == 0:
            if path.is_dir() and self._is_database_folder(path):
                if self._db_icon is None:
                    self._db_icon = load_icon("databases")
                if not self._db_icon.isNull():
                    return self._db_icon

        if role == Qt.ItemDataRole.DisplayRole and index.column() == 0:
            if path.is_dir() and self._is_database_folder(path):
                return f"{path.name}"

        return super().data(index, role)

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        base = super().flags(index)
        path = Path(self.filePath(index))
        if path.name == self._database_marker_name:
            return Qt.ItemFlag.NoItemFlags
        return base
