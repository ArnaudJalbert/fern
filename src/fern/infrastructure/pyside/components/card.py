"""
Generic reusable card widget for displaying a title, optional subtitle, and optional icon.

Styled via the #fernCard object name in QSS. Emits clicked when the user clicks the card.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class Card(QFrame):
    """
    Reusable card with title, optional subtitle, and optional icon. Styled via #fernCard.

    Emits clicked when the user releases the left mouse button over the card.
    """

    clicked = Signal()

    def __init__(
        self,
        title: str,
        subtitle: str | None = None,
        icon: QIcon | None = None,
        *,
        max_width: int | None = None,
        max_height: int | None = None,
    ) -> None:
        """
        Build the card layout with title, optional subtitle and icon.

        Args:
            title: Main text shown on the card.
            subtitle: Optional secondary text below the title.
            icon: Optional icon shown above the title.
            max_width: Optional maximum width in pixels.
            max_height: Optional maximum height in pixels.
        """
        super().__init__()
        self.setObjectName("fernCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if max_width is not None:
            self.setMaximumWidth(max_width)
        if max_height is not None:
            self.setMaximumHeight(max_height)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(4)

        if icon is not None and not icon.isNull():
            icon_label = QLabel()
            icon_label.setObjectName("fernCardIcon")
            icon_label.setFixedSize(24, 24)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            icon_label.setPixmap(icon.pixmap(24, 24))
            layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignLeft)

        self._title_label = QLabel(title)
        self._title_label.setObjectName("fernCardTitle")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setWeight(QFont.Weight.DemiBold)
        self._title_label.setFont(title_font)
        layout.addWidget(self._title_label)

        self._subtitle_label = QLabel(subtitle or "")
        self._subtitle_label.setObjectName("fernCardSubtitle")
        self._subtitle_label.setVisible(bool(subtitle))
        layout.addWidget(self._subtitle_label)

    def set_title(self, title: str) -> None:
        """Update the card title text."""
        self._title_label.setText(title)

    def set_subtitle(self, subtitle: str | None) -> None:
        """Update the card subtitle text; hides the label if subtitle is empty."""
        self._subtitle_label.setText(subtitle or "")
        self._subtitle_label.setVisible(bool(subtitle))

    def mouseReleaseEvent(self, event) -> None:
        """Emit clicked when the user releases the left button within the card bounds."""
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(
            event.position().toPoint()
        ):
            self.clicked.emit()
        super().mouseReleaseEvent(event)
