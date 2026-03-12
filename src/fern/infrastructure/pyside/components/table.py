"""
Generic table widget with QAbstractTableModel and optional async data loading.

Supports synchronous set_data() for immediate updates and load_async() for
background loading. Styled via #fernTable in QSS.
"""

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import Qt, QObject, QThread, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHeaderView,
    QLabel,
    QStackedWidget,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from fern.infrastructure.pyside.components.table_model import TableModel


class _LoadWorker(QObject):
    """
    Worker that runs a fetch callable in its thread and emits the result on the main thread.

    Used by Table.load_async() to keep the UI responsive while loading data.
    """

    finished = Signal(list, list)  # headers, rows
    error = Signal(str)

    def __init__(
        self, fetch_fn: Callable[[], tuple[list[str], list[dict[str, Any]]]]
    ) -> None:
        super().__init__()
        self._fetch_fn = fetch_fn

    def run(self) -> None:
        """Execute the fetch callable and emit finished(headers, rows) or error(message)."""
        try:
            headers, rows = self._fetch_fn()
            self.finished.emit(headers, rows)
        except Exception as e:
            self.error.emit(str(e))


class Table(QFrame):
    """
    Reusable table with QAbstractTableModel. Styled via #fernTable.

    Use set_data() for synchronous updates (main thread) or load_async() to load
    data in a background thread and update when done.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Build the table view, model, and loading placeholder stack."""
        super().__init__(parent)
        self.setObjectName("fernTable")
        self._model = TableModel()
        self._thread: QThread | None = None
        self._worker: _LoadWorker | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._stack = QStackedWidget()
        self._stack.setObjectName("fernTableStack")

        self._view = QTableView()
        self._view.setObjectName("fernTableView")
        self._view.setModel(self._model)
        self._view.setAlternatingRowColors(True)
        self._view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._view.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)
        header = self._view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        self._view.verticalHeader().setVisible(False)
        self._stack.addWidget(self._view)

        loading = QFrame()
        loading.setObjectName("fernTableLoading")
        loading_layout = QVBoxLayout(loading)
        loading_label = QLabel("Loading…")
        loading_label.setObjectName("fernTableLoadingLabel")
        loading_layout.addWidget(loading_label, 0, Qt.AlignmentFlag.AlignCenter)
        self._stack.addWidget(loading)

        self._stack.setCurrentWidget(self._view)
        layout.addWidget(self._stack)

    def model(self) -> TableModel:
        """Return the table model for direct updates on the main thread."""
        return self._model

    def view(self) -> QTableView:
        """Return the QTableView for column sizing, selection, etc."""
        return self._view

    def set_data(self, headers: list[str], rows: list[dict]) -> None:
        """Set table data synchronously. Must be called from the main thread only."""
        self._model.set_data(headers, rows)
        self._stack.setCurrentWidget(self._view)

    def load_async(
        self,
        fetch_fn: Callable[[], tuple[list[str], list[dict[str, Any]]]],
    ) -> None:
        """
        Run fetch_fn in a background thread; update the model and hide loading when done.

        Shows a loading placeholder until the fetch completes. Keeps the UI responsive.
        """
        self._stack.setCurrentWidget(self._stack.widget(1))  # loading page
        self._thread = QThread()
        self._worker = _LoadWorker(fetch_fn)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_loaded)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._on_load_error)
        self._worker.error.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _on_loaded(self, headers: list[str], rows: list[dict]) -> None:
        """Handle successful async load: update model and show table."""
        self._model.set_data(headers, rows)
        self._stack.setCurrentWidget(self._view)
        self._thread = None
        self._worker = None

    def _on_load_error(self, message: str) -> None:
        """Handle async load error: show table and display a warning dialog."""
        self._stack.setCurrentWidget(self._view)
        self._thread = None
        self._worker = None
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.warning(self, "Load failed", message)

    def clear(self) -> None:
        """Clear the table."""
        self._model.clear()
