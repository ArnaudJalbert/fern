"""
Generic table model for use with QTableView.

Stores rows as a list of dicts; column headers determine the keys. All updates
(set_data, clear) must be done on the main thread.
"""

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


class TableModel(QAbstractTableModel):
    """
    Model that holds rows as a list of dicts keyed by column header.

    Each row is a dict mapping header names to values. Updates must be done
    on the main thread via set_data() or clear().
    """

    def __init__(self, headers: list[str] | None = None, parent=None) -> None:
        """
        Initialize the model with optional initial headers.

        Args:
            headers: Optional list of column header names.
            parent: Optional QObject parent.
        """
        super().__init__(parent)
        self._headers: list[str] = headers or []
        self._rows: list[dict] = []
        self._readonly_columns: set[int] = set()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of rows. For the root index, returns the length of _rows."""
        if parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of columns (header count)."""
        if parent.isValid():
            return 0
        return len(self._headers)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        """Return the display text or edit value for the cell at index."""
        if not index.isValid():
            return None
        row, col = index.row(), index.column()
        if row >= len(self._rows) or col >= len(self._headers):
            return None
        key = self._headers[col]
        value = self._rows[row].get(key)
        if role == Qt.ItemDataRole.EditRole:
            return value
        if role == Qt.ItemDataRole.CheckStateRole and isinstance(value, bool):
            return Qt.CheckState.Checked if value else Qt.CheckState.Unchecked
        if role == Qt.ItemDataRole.DisplayRole:
            if isinstance(value, bool):
                return ""
            return str(value) if value is not None else ""
        return None

    def setData(
        self, index: QModelIndex, value, role: int = Qt.ItemDataRole.EditRole
    ) -> bool:
        """Update the cell value and emit dataChanged."""
        if not index.isValid():
            return False
        row, col = index.row(), index.column()
        if row >= len(self._rows) or col >= len(self._headers):
            return False
        key = self._headers[col]
        if role == Qt.ItemDataRole.CheckStateRole:
            value = value == Qt.CheckState.Checked
        self._rows[row][key] = value
        roles = [role]
        if role == Qt.ItemDataRole.EditRole and isinstance(value, bool):
            roles.append(Qt.ItemDataRole.CheckStateRole)
        self.dataChanged.emit(index, index, roles)
        return True

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        """Return flags: all columns are editable unless in _readonly_columns."""
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        base = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        row, col = index.row(), index.column()
        if row < len(self._rows) and col < len(self._headers):
            if col in self._readonly_columns:
                return base
            val = self._rows[row].get(self._headers[col])
            flags = base | Qt.ItemFlag.ItemIsEditable
            if isinstance(val, bool):
                flags |= Qt.ItemFlag.ItemIsUserCheckable
            return flags
        return base

    def set_readonly_columns(self, columns: set[int]) -> None:
        """Mark column indices as read-only (not editable)."""
        self._readonly_columns = set(columns)

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ):
        """Return the horizontal header label for the given section (column index)."""
        if (
            role != Qt.ItemDataRole.DisplayRole
            or orientation != Qt.Orientation.Horizontal
        ):
            return None
        if section >= len(self._headers):
            return None
        return self._headers[section]

    def set_data(self, headers: list[str], rows: list[dict]) -> None:
        """Replace headers and rows. Must be called from the main thread only."""
        self.beginResetModel()
        self._headers = list(headers)
        self._rows = [dict(r) for r in rows]
        self.endResetModel()

    def clear(self) -> None:
        """Clear all data (headers and rows). Must be called from the main thread only."""
        self.set_data([], [])
