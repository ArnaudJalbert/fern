"""
Bottom-right toast notification for completed actions.

Use show_toast(parent, message) to display a short-lived message.
Shows a thin countdown bar for time remaining.
Multiple toasts stack vertically (newest at bottom).
"""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

_TOAST_BG = "#27272a"
_TOAST_SPACING = 4
_MARGIN_RIGHT = 8
_MARGIN_BOTTOM = 6

# Per-window list of active toasts (window id -> list of ToastWidget)
_active_toasts: dict[int, list[QWidget]] = {}

_TOAST_STYLE = f"""
    QFrame#fernToast {{
        background-color: {_TOAST_BG};
        border: 1px solid #3f3f46;
        border-radius: 4px;
        padding: 4px 8px 3px 8px;
    }}
    QFrame#fernToast QLabel {{
        background: none;
        border: none;
    }}
    #fernToastLabel {{
        color: #d4d4d8;
        font-size: 10px;
    }}
    #fernToastBar {{
        background-color: #71717a;
        border: none;
        border-radius: 1px;
        max-height: 1px;
        min-height: 1px;
    }}
"""

_DURATION_MS = 2500
_TICK_MS = 50


def _reposition_toasts(win: QWidget) -> None:
    """Position all active toasts for this window, stacked from bottom upward."""
    wid = id(win)
    if wid not in _active_toasts:
        return
    toasts = [t for t in _active_toasts[wid] if t.isVisible()]
    _active_toasts[wid] = toasts
    if not toasts:
        return
    br = win.rect().bottomRight()
    global_br = win.mapToGlobal(br)
    y = global_br.y() - _MARGIN_BOTTOM
    for toast in reversed(toasts):  # bottom toast first (last in list)
        if not toast.isVisible():
            continue
        h = toast.height()
        y -= h
        toast.move(global_br.x() - toast.width() - _MARGIN_RIGHT, y)
        y -= _TOAST_SPACING


class ToastWidget(QFrame):
    """A small notification that appears in the bottom-right and auto-dismisses."""

    def __init__(
        self,
        parent: QWidget,
        message: str,
        duration_ms: int = _DURATION_MS,
        on_dismiss: Callable[[ToastWidget], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self._on_dismiss = on_dismiss
        self.setObjectName("fernToast")
        self.setStyleSheet(_TOAST_STYLE)
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor(_TOAST_BG))
        pal.setColor(QPalette.ColorRole.Base, QColor(_TOAST_BG))
        self.setPalette(pal)

        self._duration_ms = duration_ms
        self._label = QLabel(message)
        self._label.setObjectName("fernToastLabel")
        self._label.setAutoFillBackground(False)
        self._label.setPalette(pal)

        self._bar_container = QWidget(self)
        self._bar_container.setAutoFillBackground(False)
        self._bar_container.setPalette(pal)
        self._bar_container.setFixedHeight(2)
        self._bar_container.setMinimumWidth(24)
        self._bar = QFrame(self._bar_container)
        self._bar.setObjectName("fernToastBar")
        self._bar.setFixedHeight(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 3)
        layout.setSpacing(2)
        layout.addWidget(self._label)
        layout.addWidget(self._bar_container)

        self._dismiss_timer = QTimer(self)
        self._dismiss_timer.setSingleShot(True)
        self._dismiss_timer.timeout.connect(self._dismiss)

        self._tick_timer = QTimer(self)
        self._tick_timer.timeout.connect(self._on_tick)
        self._elapsed_ms = 0

    def _on_tick(self) -> None:
        self._elapsed_ms += _TICK_MS
        if self._elapsed_ms >= self._duration_ms:
            self._tick_timer.stop()
            return
        self._update_bar_width()

    def _dismiss(self) -> None:
        self._tick_timer.stop()
        if self._on_dismiss is not None:
            self._on_dismiss(self)
        self.close()
        self.deleteLater()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.adjustSize()
        self._elapsed_ms = 0
        self._dismiss_timer.start(self._duration_ms)
        self._tick_timer.start(_TICK_MS)
        QTimer.singleShot(0, self._update_bar_width)
        win = self.parentWidget()
        if win is not None:
            QTimer.singleShot(10, lambda: _reposition_toasts(win))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_bar_width()

    def _update_bar_width(self) -> None:
        w = self._bar_container.width()
        if w > 0 and self._duration_ms > 0:
            ratio = 1.0 - (self._elapsed_ms / self._duration_ms)
            w_bar = max(0, int(w * ratio))
            self._bar.setGeometry(0, 0, w_bar, 1)


def show_toast(parent: QWidget, message: str, duration_ms: int = _DURATION_MS) -> None:
    """
    Show a short-lived toast in the bottom-right of parent's window.
    Multiple toasts stack vertically (newest at bottom).
    """
    window = parent.window() if parent else None
    if window is None:
        return
    wid = id(window)

    def on_dismiss(t: ToastWidget) -> None:
        if wid in _active_toasts:
            _active_toasts[wid] = [x for x in _active_toasts[wid] if x is not t]
            _reposition_toasts(window)

    if wid not in _active_toasts:
        _active_toasts[wid] = []
    toast = ToastWidget(window, message, duration_ms=duration_ms, on_dismiss=on_dismiss)
    _active_toasts[wid].append(toast)
    toast.show()
    toast.raise_()
    QTimer.singleShot(20, lambda: _reposition_toasts(window))
