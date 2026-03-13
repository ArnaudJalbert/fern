"""
Reusable Qt delegates for table/list views.

CheckboxDelegate paints a checkbox and toggles on click by calling model.setData.
Use with QTableView for boolean columns.

TextEditDelegate gives the editor a slightly inset rect so inline text is not clipped.

WrappingTextDelegate paints and sizes cell text with word wrap.
"""

from PySide6.QtCore import QEvent, Qt, QSize, QRectF
from PySide6.QtGui import QPalette, QTextCharFormat, QTextCursor, QTextDocument
from PySide6.QtWidgets import (
    QApplication,
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
    """Delegate that paints a checkbox and toggles on click by calling setData."""

    def editorEvent(self, event: QEvent, model, option, index) -> bool:
        if event.type() == QEvent.Type.MouseButtonRelease:
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
