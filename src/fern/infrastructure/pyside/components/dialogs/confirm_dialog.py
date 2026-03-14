"""
Reusable confirmation and alert dialogs with a modern, minimal style.

Use confirm() for Yes/No flows (e.g. delete). Use alert() for OK-only (info, warning).
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

_BG = "#1f1f23"

_DIALOG_STYLE = """
    QDialog#fernConfirmDialog {
        background-color: #1f1f23;
        border: 1px solid #27272a;
        border-radius: 8px;
    }
    QDialog#fernConfirmDialog QLabel {
        background: none;
        border: none;
    }
    #fernConfirmTitle {
        color: #fafafa;
        font-size: 12px;
        font-weight: 600;
    }
    #fernConfirmMessage {
        color: #a1a1aa;
        font-size: 11px;
        line-height: 1.25;
        padding: 0;
        background: none;
        border: none;
    }
    #fernConfirmDialog QPushButton {
        min-height: 24px;
        padding: 0 10px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 500;
    }
    #fernConfirmDialog QPushButton[primary="false"] {
        background-color: #27272a;
        border: 1px solid #3f3f46;
        color: #a1a1aa;
    }
    #fernConfirmDialog QPushButton[primary="false"]:hover {
        background-color: #3f3f46;
        color: #d4d4d8;
    }
    #fernConfirmDialog QPushButton[primary="true"] {
        background-color: #fafafa;
        border: none;
        color: #18181b;
    }
    #fernConfirmDialog QPushButton[primary="true"]:hover {
        background-color: #d4d4d8;
    }
    #fernConfirmDialog QPushButton[destructive="true"] {
        background-color: #dc2626;
        border: none;
        color: #ffffff;
    }
    #fernConfirmDialog QPushButton[destructive="true"]:hover {
        background-color: #b91c1c;
    }
"""


class ConfirmDialog(QDialog):
    """
    Minimal confirmation dialog: title, message, and configurable buttons.

    Use the static run() or the module-level confirm() / alert() helpers.
    """

    def __init__(
        self,
        parent: QWidget | None,
        title: str,
        message: str,
        *,
        destructive: bool = False,
        confirm_label: str = "Yes",
        cancel_label: str = "Cancel",
        single_button: bool = False,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("fernConfirmDialog")
        self.setWindowTitle(title)
        self.setStyleSheet(_DIALOG_STYLE)
        self.setAutoFillBackground(True)
        self.setModal(True)
        self.setMinimumWidth(260)
        self.setMaximumWidth(360)

        # Match palette to dialog background so labels don't show a different bg color
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor(_BG))
        pal.setColor(QPalette.ColorRole.Base, QColor(_BG))
        self.setPalette(pal)

        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(12, 10, 12, 10)

        title_label = QLabel(title)
        title_label.setObjectName("fernConfirmTitle")
        title_label.setWordWrap(True)
        title_label.setAutoFillBackground(False)
        title_label.setPalette(pal)
        layout.addWidget(title_label)

        msg_label = QLabel(message)
        msg_label.setObjectName("fernConfirmMessage")
        msg_label.setWordWrap(True)
        msg_label.setAutoFillBackground(False)
        msg_label.setPalette(pal)
        msg_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(msg_label)

        button_box = QHBoxLayout()
        button_box.setSpacing(8)
        button_box.addStretch()

        if single_button:
            ok_btn = QPushButton("OK")
            ok_btn.setProperty("primary", True)
            ok_btn.setProperty("destructive", False)
            ok_btn.clicked.connect(self.accept)
            button_box.addWidget(ok_btn)
        else:
            cancel_btn = QPushButton(cancel_label)
            cancel_btn.setProperty("primary", False)
            cancel_btn.setProperty("destructive", False)
            cancel_btn.clicked.connect(self.reject)
            button_box.addWidget(cancel_btn)

            confirm_btn = QPushButton(confirm_label)
            confirm_btn.setProperty("primary", not destructive)
            confirm_btn.setProperty("destructive", destructive)
            confirm_btn.setDefault(True)
            confirm_btn.clicked.connect(self.accept)
            button_box.addWidget(confirm_btn)

        layout.addLayout(button_box)

    @staticmethod
    def run(
        parent: QWidget | None,
        title: str,
        message: str,
        *,
        destructive: bool = False,
        confirm_label: str = "Yes",
        cancel_label: str = "Cancel",
    ) -> bool:
        """Show the dialog and return True if the user confirmed, False otherwise."""
        d = ConfirmDialog(
            parent,
            title,
            message,
            destructive=destructive,
            confirm_label=confirm_label,
            cancel_label=cancel_label,
        )
        return d.exec() == QDialog.DialogCode.Accepted


def confirm(
    parent: QWidget | None,
    title: str,
    message: str,
    *,
    destructive: bool = False,
    confirm_label: str = "Yes",
    cancel_label: str = "Cancel",
) -> bool:
    """
    Show a modern confirmation dialog. Returns True if the user clicks the confirm button.
    Use destructive=True for actions like Delete (red primary button).
    """
    return ConfirmDialog.run(
        parent,
        title,
        message,
        destructive=destructive,
        confirm_label=confirm_label,
        cancel_label=cancel_label,
    )


def alert(
    parent: QWidget | None,
    title: str,
    message: str,
) -> None:
    """Show a modern alert dialog with a single OK button (info or warning)."""
    d = ConfirmDialog(
        parent,
        title,
        message,
        single_button=True,
    )
    d.exec()


def show_error(
    parent: QWidget | None,
    message: str,
    title: str = "Something went wrong",
) -> None:
    """Show a generic error window with the given message and optional title."""
    d = ConfirmDialog(
        parent,
        title,
        message,
        single_button=True,
    )
    d.exec()
