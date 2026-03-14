"""Reusable PySide6 UI components.

Organized into sub-packages:

- **dialogs/** — Confirmation, error, and property-edit dialogs
- **properties/** — PropertyField, PropertyCard, PropertyCardsWidget, PropertySettingsWidget
- **table/** — Table, TableModel, and cell delegates

Plus standalone components: Card, MarkdownHighlighter, CommandPalette, Toast.
"""

from fern.infrastructure.pyside.components.card import Card
from fern.infrastructure.pyside.components.command_palette import (
    CommandItem,
    CommandPalette,
)
from fern.infrastructure.pyside.components.dialogs import (
    ConfirmDialog,
    alert,
    confirm,
    run_boolean_property_editor,
    run_simple_property_editor,
    run_status_choices_editor,
    run_string_property_editor,
    show_error,
)
from fern.infrastructure.pyside.components.markdown_highlighter import (
    MarkdownHighlighter,
)
from fern.infrastructure.pyside.components.properties import (
    PropertyCard,
    PropertyCardsWidget,
    PropertyField,
    PropertySettingsWidget,
)
from fern.infrastructure.pyside.components.table import (
    CheckboxDelegate,
    StatusComboDelegate,
    Table,
    TableModel,
    TextEditDelegate,
    WrappingTextDelegate,
)
from fern.infrastructure.pyside.components.toast import show_toast

__all__ = [
    "Card",
    "CheckboxDelegate",
    "CommandItem",
    "CommandPalette",
    "ConfirmDialog",
    "MarkdownHighlighter",
    "PropertyCard",
    "PropertyCardsWidget",
    "PropertyField",
    "PropertySettingsWidget",
    "StatusComboDelegate",
    "Table",
    "TableModel",
    "TextEditDelegate",
    "WrappingTextDelegate",
    "alert",
    "confirm",
    "run_boolean_property_editor",
    "run_simple_property_editor",
    "run_status_choices_editor",
    "run_string_property_editor",
    "show_error",
    "show_toast",
]
