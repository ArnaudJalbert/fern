# Components

Reusable widgets in `pyside/components/`, organized into sub-packages by domain.

## Sub-packages

### `components/dialogs/`

Confirmation, error display, and property edit dialogs.

| Module | Description |
|--------|-------------|
| `confirm_dialog.py` | `ConfirmDialog`, `confirm()`, `alert()`, `show_error()` |
| `base_property_edit_dialog.py` | Abstract base for type-specific property edit dialogs |
| `simple_property_edit_dialog.py` | Name-only editor for boolean, string, and other simple property types |
| `status_choices_editor_dialog.py` | Full editor for status properties: name + choices + color picker |

**Key design**: `SimplePropertyEditDialog` replaces the former `BooleanPropertyEditDialog` and `StringPropertyEditDialog` (which were identical except for type key strings). Any new simple property type can reuse it:

```python
name = run_simple_property_editor("my_type", name=current_name, parent=parent)
```

### `components/properties/`

Widgets for displaying and editing property values.

| Module | Description |
|--------|-------------|
| `property_field.py` | Label + typed editor widget. Uses a registry pattern to select the right editor per property type. |
| `property_card.py` | `QFrame` wrapper around a single `PropertyField` |
| `property_cards_widget.py` | Vertical stack of `PropertyCard`s |
| `property_settings_widget.py` | Name + type combo for the add-property flow |

### `components/table/`

Table view, data model, and cell delegates.

| Module | Description |
|--------|-------------|
| `table.py` | Generic `QTableView` wrapper with sync `set_data()` and async `load_async()` |
| `table_model.py` | `QAbstractTableModel` for dict-based rows with named columns |
| `delegates.py` | `CheckboxDelegate`, `TextEditDelegate`, `WrappingTextDelegate`, `StatusComboDelegate` |

### Standalone Components

| Module | Description |
|--------|-------------|
| `card.py` | Clickable card with title, subtitle, optional icon |
| `command_palette.py` | Cmd+P fuzzy command palette |
| `markdown_highlighter.py` | `QSyntaxHighlighter` for markdown in `QPlainTextEdit` |
| `toast.py` | Bottom-right toast notifications with countdown bar |

## Import Convention

Everything is re-exported from `components/__init__.py`, so consumers use:

```python
from fern.infrastructure.pyside.components import Table, confirm, PropertyField
```

For sub-package-scoped imports:

```python
from fern.infrastructure.pyside.components.table import Table, TableModel
from fern.infrastructure.pyside.components.dialogs import confirm, show_error
from fern.infrastructure.pyside.components.properties import PropertyField
```
