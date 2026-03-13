"""Splash screen shown while the application is loading."""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsDropShadowEffect,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)


class SplashScreen(QWidget):
    """Frameless centered splash with app name, tagline, and a progress bar."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.SplashScreen
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(420, 260)
        self._build_ui()
        self._center_on_screen()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QWidget()
        card.setObjectName("splashCard")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 120))
        card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(40, 44, 40, 36)
        layout.setSpacing(0)

        title = QLabel("Fern")
        title.setObjectName("splashTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(6)

        subtitle = QLabel("Loading workspace…")
        subtitle.setObjectName("splashSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._subtitle = subtitle
        layout.addWidget(subtitle)

        layout.addSpacing(28)

        bar = QProgressBar()
        bar.setObjectName("splashProgress")
        bar.setRange(0, 100)
        bar.setValue(0)
        bar.setTextVisible(False)
        bar.setFixedHeight(6)
        self._bar = bar
        layout.addWidget(bar)

        outer.addWidget(card)

    def _center_on_screen(self) -> None:
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.x() + (geo.width() - self.width()) // 2
            y = geo.y() + (geo.height() - self.height()) // 2
            self.move(x, y)

    def set_progress(self, value: int, message: str | None = None) -> None:
        """Update the progress bar and optionally the subtitle text."""
        self._bar.setValue(value)
        if message is not None:
            self._subtitle.setText(message)
        QApplication.processEvents()

    def finish(self, main_window: QWidget, delay_ms: int = 200) -> None:
        """Fill the bar to 100% then close after a short delay, showing main_window."""
        self.set_progress(100, "Ready")
        QTimer.singleShot(delay_ms, lambda: self._close_and_show(main_window))

    def _close_and_show(self, main_window: QWidget) -> None:
        self.close()
        main_window.show()
