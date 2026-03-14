"""
Reusable Qt delegates for table/list views.

CheckboxDelegate paints a checkbox and toggles on click by calling model.setData.
Use with QTableView for boolean columns.

TextEditDelegate gives the editor a slightly inset rect so inline text is not clipped.

WrappingTextDelegate paints and sizes cell text with word wrap.

StatusComboDelegate uses a QComboBox editor with choice names (and optional color);
pass a sequence of objects with .name (and optionally .color) for status columns.
"""

from PySide6.QtCore import QEvent, Qt, QRectF, QSize, QTimer
from PySide6.QtGui import (
    QColor,
    QPainter,
    QPalette,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
)
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
)


class TextEditDelegate(QStyledItemDelegate):
    """Delegate that gives the cell editor full height and a small horizontal margin so text is not cut off."""

    def updateEditorGeometry(
        self,
        editor,
        option: QStyleOptionViewItem,
        index,
    ) -> None:
        rect = option.rect
        h_margin = 2
        editor.setGeometry(rect.adjusted(h_margin, 0, -h_margin, 0))


class CheckboxDelegate(QStyledItemDelegate):
    """Delegate that paints a checkbox and toggles on double-click by calling setData."""

    def editorEvent(self, event: QEvent, model, option, index) -> bool:
        if event.type() == QEvent.Type.MouseButtonDblClick:
            val = model.data(index, Qt.ItemDataRole.CheckStateRole)
            if val is not None:
                new_state = (
                    Qt.CheckState.Unchecked
                    if val == Qt.CheckState.Checked
                    else Qt.CheckState.Checked
                )
                if model.setData(index, new_state, Qt.ItemDataRole.CheckStateRole):
                    return True
        return super().editorEvent(event, model, option, index)


class WrappingTextDelegate(QStyledItemDelegate):
    """Delegate that paints and sizes cell text with word wrap."""

    def _doc_for_cell(
        self, option: QStyleOptionViewItem, index, width: int
    ) -> QTextDocument:
        doc = QTextDocument()
        doc.setDefaultFont(option.font)
        doc.setTextWidth(width)
        text = index.data(Qt.ItemDataRole.DisplayRole)
        if text is not None:
            doc.setPlainText(str(text))
        return doc

    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:
        width = option.rect.width()
        if width <= 0:
            width = 200
        doc = self._doc_for_cell(option, index, width)
        return QSize(int(doc.idealWidth()), int(doc.size().height()))

    def paint(self, painter, option: QStyleOptionViewItem, index) -> None:
        option_copy = QStyleOptionViewItem(option)
        option_copy.features |= QStyleOptionViewItem.ViewItemFeature.WrapText

        # Let the style draw background and focus
        option_copy.text = ""
        QApplication.style().drawControl(
            QStyle.ControlElement.CE_ItemViewItem,
            option_copy,
            painter,
            option_copy.widget,
        )

        text = index.data(Qt.ItemDataRole.DisplayRole)
        if text is None or text == "":
            return

        role = (
            QPalette.ColorRole.HighlightedText
            if (option.state & QStyle.StateFlag.State_Selected)
            else QPalette.ColorRole.Text
        )
        doc = self._doc_for_cell(option, index, option.rect.width())
        fmt = QTextCharFormat()
        fmt.setForeground(option.palette.color(QPalette.ColorGroup.Normal, role))
        cursor = QTextCursor(doc)
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.mergeCharFormat(fmt)
        rect = option.rect.adjusted(2, 1, -2, -1)
        painter.save()
        painter.translate(rect.topLeft())
        doc.drawContents(painter, QRectF(0, 0, rect.width(), rect.height()))
        painter.restore()

    def updateEditorGeometry(self, editor, option: QStyleOptionViewItem, index) -> None:
        rect = option.rect
        editor.setGeometry(rect.adjusted(2, 0, -2, 0))


def _luminance(c: QColor) -> float:
    """Relative luminance (0 dark, 1 light); use to pick contrasting text color."""
    r, g, b = c.redF(), c.greenF(), c.blueF()
    return 0.299 * r + 0.587 * g + 0.114 * b


def _parse_hex(hex_str: str) -> QColor | None:
    s = (hex_str or "").strip()
    if not s:
        return None
    if not s.startswith("#"):
        s = "#" + s
    c = QColor(s)
    return c if c.isValid() else None


class StatusComboDelegate(QStyledItemDelegate):
    """Delegate that uses a QComboBox for status columns; choices are objects with .name (and optionally .color)."""

    def __init__(self, choices: list, parent=None):
        super().__init__(parent)
        self._choices = list(choices)
        self._value_to_color: dict[str, str] = {}
        for c in self._choices:
            name = getattr(c, "name", str(c))
            color = getattr(c, "color", None)
            if name is not None and color:
                self._value_to_color[str(name).strip()] = str(color).strip()

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        value = index.data(Qt.ItemDataRole.EditRole)
        text = str(value).strip() if value is not None else ""
        hex_str = self._value_to_color.get(text)
        bg_color = _parse_hex(hex_str) if hex_str else None

        content = option.rect.adjusted(2, 1, -2, -1)
        if bg_color is not None and bg_color.isValid():
            option_copy = QStyleOptionViewItem(option)
            option_copy.text = ""
            QApplication.style().drawControl(
                QStyle.ControlElement.CE_ItemViewItem,
                option_copy,
                painter,
                option.widget,
            )
            painter.fillRect(content, bg_color)
            text_color = (
                QColor(255, 255, 255) if _luminance(bg_color) < 0.5 else QColor(0, 0, 0)
            )
            if option.state & QStyle.StateFlag.State_Selected:
                text_color = option.palette.color(
                    QPalette.ColorGroup.Normal, QPalette.ColorRole.HighlightedText
                )
            painter.setPen(text_color)
            painter.setFont(option.font)
            painter.drawText(
                content,
                Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextSingleLine,
                text or "",
            )
        else:
            option_copy = QStyleOptionViewItem(option)
            option_copy.text = text or ""
            QApplication.style().drawControl(
                QStyle.ControlElement.CE_ItemViewItem,
                option_copy,
                painter,
                option.widget,
            )

    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.setEditable(False)
        for c in self._choices:
            name = getattr(c, "name", str(c))
            editor.addItem(name, name)
        editor.addItem("", "")  # allow clear
        return editor

    def setEditorData(self, editor: QComboBox, index) -> None:
        value = index.data(Qt.ItemDataRole.EditRole)
        text = str(value) if value is not None else ""
        idx = editor.findText(text)
        if idx >= 0:
            editor.setCurrentIndex(idx)
        else:
            editor.setCurrentIndex(editor.count() - 1)  # empty
        # Open the dropdown immediately so the user can pick without another click
        QTimer.singleShot(0, editor.showPopup)

    def setModelData(self, editor: QComboBox, model, index) -> None:
        text = editor.currentText().strip()
        model.setData(index, text, Qt.ItemDataRole.EditRole)

    def updateEditorGeometry(self, editor, option: QStyleOptionViewItem, index) -> None:
        rect = option.rect
        editor.setGeometry(rect.adjusted(2, 0, -2, 0))
