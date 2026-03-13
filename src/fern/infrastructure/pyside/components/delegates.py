"""
Reusable Qt delegates for table/list views.

CheckboxDelegate paints a checkbox and toggles on click by calling model.setData.
Use with QTableView for boolean columns.

TextEditDelegate gives the editor a slightly inset rect so inline text is not clipped.
"""

from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem


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
        editor.setGeometry(
            rect.adjusted(h_margin, 0, -h_margin, 0)
        )


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
