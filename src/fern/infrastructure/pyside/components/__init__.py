"""
Reusable PySide6 UI components.

Card and Table for data display; TableModel for table data; MarkdownHighlighter
for syntax highlighting; PropertyField for label + typed editor; PropertyCard
and PropertyCardsWidget for card-style property layout; CheckboxDelegate for boolean columns.
"""

from fern.infrastructure.pyside.components.card import Card
from fern.infrastructure.pyside.components.confirm_dialog import (
    alert,
    confirm,
    ConfirmDialog,
)
from fern.infrastructure.pyside.components.toast import show_toast
from fern.infrastructure.pyside.components.delegates import (
    CheckboxDelegate,
    TextEditDelegate,
    WrappingTextDelegate,
)
from fern.infrastructure.pyside.components.markdown_highlighter import (
    MarkdownHighlighter,
)
from fern.infrastructure.pyside.components.property_card import PropertyCard
from fern.infrastructure.pyside.components.property_cards_widget import (
    PropertyCardsWidget,
)
from fern.infrastructure.pyside.components.property_field import PropertyField
from fern.infrastructure.pyside.components.property_settings_widget import (
    PropertySettingsWidget,
)
from fern.infrastructure.pyside.components.command_palette import (
    CommandItem,
    CommandPalette,
)
from fern.infrastructure.pyside.components.table import Table
from fern.infrastructure.pyside.components.table_model import TableModel

__all__ = [
    "alert",
    "CommandItem",
    "CommandPalette",
    "Card",
    "confirm",
    "ConfirmDialog",
    "show_toast",
    "CheckboxDelegate",
    "TextEditDelegate",
    "WrappingTextDelegate",
    "MarkdownHighlighter",
    "PropertyCard",
    "PropertyCardsWidget",
    "PropertyField",
    "PropertySettingsWidget",
    "Table",
    "TableModel",
]
