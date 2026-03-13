"""
Base view for all stackable screens in the Fern UI.

Provides a common toolbar (back arrow, stretch, optional widgets, options icon),
a content area, and a currentView property for styling. Subclasses add their
content and can connect to back_requested and options_clicked.
"""

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from fern.infrastructure.pyside.utils import load_icon


class FernView(QWidget):
    """
    Base for stackable views: view_id (for styling), back button, options icon, toolbar, content area.

    Subclasses should override view_id, add widgets via content_layout(), and optionally
    add toolbar widgets with add_toolbar_widget(). Connect back_requested to pop the
    view stack; connect options_clicked to show a context menu or options.
    """

    back_requested = Signal()
    options_clicked = Signal()

    view_id: str = "base"

    def __init__(self, parent: QWidget | None = None) -> None:
        """Build the toolbar and content area, and set the currentView property."""
        super().__init__(parent)
        self._build_ui()
        self.set_current_view(self.get_view_id())

    def get_view_id(self) -> str:
        """Return the view identifier for QSS (e.g. [currentView="databases"]). Override in subclass."""
        return self.view_id

    def _build_ui(self) -> None:
        """Create the toolbar (back, stretch, options icon) and the content widget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._toolbar = QFrame()
        self._toolbar.setObjectName("vaultContentToolbar")
        toolbar_layout = QHBoxLayout(self._toolbar)
        toolbar_layout.setContentsMargins(12, 4, 12, 4)
        toolbar_layout.setSpacing(6)
        toolbar_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._back_btn = QPushButton("←")
        self._back_btn.setObjectName("vaultContentBackButton")
        self._back_btn.setFixedSize(24, 24)
        self._back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._back_btn.clicked.connect(self.back_requested.emit)
        self._back_btn.setVisible(False)
        toolbar_layout.addWidget(self._back_btn)
        toolbar_layout.addStretch(1)
        self._options_btn_index = toolbar_layout.count()
        options_icon = load_icon("options")
        self._options_btn = QPushButton(options_icon, "")
        self._options_btn.setObjectName("vaultContentOptionsButton")
        self._options_btn.setFixedSize(24, 24)
        self._options_btn.setIconSize(QSize(14, 14))
        self._options_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._options_btn.clicked.connect(self.options_clicked.emit)
        toolbar_layout.addWidget(self._options_btn)
        self._toolbar_layout = toolbar_layout

        layout.addWidget(self._toolbar)

        self._content = QWidget()
        self._content.setObjectName("vaultContentStack")
        self._content.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._content, 1)

    def content_layout(self) -> QVBoxLayout:
        """Return the layout of the content area. Add your main content here."""
        return self._content_layout

    def add_toolbar_widget(self, widget: QWidget) -> None:
        """Add a widget to the toolbar before the options icon (so the options icon stays rightmost)."""
        # Keep toolbar items aligned: same row height as back/options (32px)
        if hasattr(widget, "setFixedHeight"):
            widget.setFixedHeight(24)
        policy = widget.sizePolicy()
        policy.setVerticalPolicy(QSizePolicy.Policy.Fixed)
        widget.setSizePolicy(policy)
        self._toolbar_layout.insertWidget(self._options_btn_index, widget)
        self._options_btn_index += 1

    def set_back_visible(self, visible: bool) -> None:
        """Show or hide the back button."""
        self._back_btn.setVisible(visible)

    def set_current_view(self, view_id: str) -> None:
        """Set the currentView property on toolbar and content for QSS. Call when context changes."""
        self._toolbar.setProperty("currentView", view_id)
        self._content.setProperty("currentView", view_id)
        style = self._toolbar.style()
        style.unpolish(self._toolbar)
        style.polish(self._toolbar)
        style.unpolish(self._content)
        style.polish(self._content)
