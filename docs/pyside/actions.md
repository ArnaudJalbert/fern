# Actions & Menus

The action system in `pyside/actions.py` provides a centralized registry of user actions used across menu bars, context menus, and options menus.

## Unified ActionItem

All simple menu items share a single frozen dataclass:

```python
@dataclass(frozen=True)
class ActionItem:
    id: str
    label: str
    color: str | None = None
    is_separator: bool = False
```

Create lists of `ActionItem`s from specs:

```python
PAGES_VIEW_ACTIONS = action_items_from_specs([
    ("new_page", "New page", "#16a34a"),
    ("_separator", "", None),
    ("add_property", "Add property", None),
])
```

## Action Contexts

### Global Edit Actions (Menu Bar + Command Palette)

The most complex action context. Uses `ActionSpec` (richer than `ActionItem`) with:

- `context_flag` — attribute on `MenuContextProtocol` for availability
- `method_name` — method on `ActionRunnerProtocol` for execution

```python
actions = get_edit_actions(menu_context, runner)
for action in actions:
    if action.available:
        menu.addAction(action.label).triggered.connect(action.callback)
```

### Tree Context Menu (Sidebar Right-Click)

Actions vary by selection type (`"file"`, `"folder"`, `"database"`, `"empty"`):

```python
items = get_tree_actions("database")
# → [Open, Open in new window, Reveal, ─, New page]
```

### Pages View Options Menu

```python
from fern.infrastructure.pyside.actions import PAGES_VIEW_ACTIONS, build_options_menu

menu = build_options_menu(self, PAGES_VIEW_ACTIONS, callbacks)
```

### Editor View Options Menu

```python
from fern.infrastructure.pyside.actions import EDITOR_VIEW_ACTIONS, build_options_menu

skip = {"add_property"} if not self._in_database else None
menu = build_options_menu(self, EDITOR_VIEW_ACTIONS, callbacks, skip_ids=skip)
```

## build_options_menu()

Eliminates the repetitive loop that every options menu handler used to have:

```python
def build_options_menu(parent, actions, callbacks, *, skip_ids=None):
```

- Iterates `actions`, inserts separators, skips items in `skip_ids`
- Looks up each action's callback in `callbacks` dict by `id`
- Colored items use `add_colored_action()`; others get a plain `menu.addAction()`
- Returns the ready-to-exec `QMenu`
