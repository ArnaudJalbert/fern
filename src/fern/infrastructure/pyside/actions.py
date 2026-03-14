"""
Central registry of actions by category, reusable across menu bar, command palette,
context menus (tree, pages, editor). Availability and execution depend on context.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from fern.infrastructure.pyside.utils import reveal_in_explorer_action_label


# ─── Shared action item ───────────────────────────────────────────────────────


@dataclass(frozen=True)
class ActionItem:
    """One action item for any context menu or options menu: id, label, optional color."""

    id: str
    label: str
    color: str | None = None
    is_separator: bool = False


def action_items_from_specs(
    specs: list[tuple[str, str, str | None]],
) -> list[ActionItem]:
    """Build a list of ActionItems from a list of (id, label, color) tuples.

    Use ``("_separator", "", None)`` to insert a separator.
    """
    result: list[ActionItem] = []
    for action_id, label, color in specs:
        if action_id == "_separator":
            result.append(ActionItem("_separator", "", None, is_separator=True))
        else:
            result.append(ActionItem(id=action_id, label=label, color=color))
    return result


def build_options_menu(
    parent,
    actions: list[ActionItem],
    callbacks: dict[str, Callable[[], None]],
    *,
    skip_ids: set[str] | None = None,
):
    """Build a QMenu from a list of ActionItems and a callbacks dict.

    Each ActionItem whose id is in ``callbacks`` gets a menu entry; items with
    ``color`` get a colored label via ``add_colored_action``.  Items whose id
    is in ``skip_ids`` are silently omitted.
    """
    from PySide6.QtWidgets import QMenu

    from fern.infrastructure.pyside.utils import add_colored_action

    menu = QMenu(parent)
    menu.setObjectName("vaultContentOptionsMenu")
    for item in actions:
        if item.is_separator:
            menu.addSeparator()
            continue
        if skip_ids and item.id in skip_ids:
            continue
        callback = callbacks.get(item.id)
        if callback is None:
            continue
        if item.color:
            add_colored_action(menu, item.label, item.color, callback)
        else:
            action = menu.addAction(item.label)
            action.triggered.connect(callback)
    return menu


# ─── Global edit / menu bar actions ────────────────────────────────────────────


class MenuContextProtocol(Protocol):
    """Protocol for context that determines which actions are available."""

    can_new_page: bool
    can_new_database: bool
    can_new_folder: bool
    can_add_property: bool
    can_save_order: bool
    can_delete: bool
    can_reveal_in_explorer: bool


class ActionRunnerProtocol(Protocol):
    """Protocol for the object that executes actions (e.g. VaultView)."""

    def menu_new_page(self) -> None: ...
    def menu_new_database(self) -> None: ...
    def menu_new_folder(self) -> None: ...
    def menu_reveal_in_explorer(self) -> None: ...
    def menu_add_property(self) -> None: ...
    def menu_save_order(self) -> None: ...
    def menu_delete(self) -> None: ...


@dataclass(frozen=True)
class ActionSpec:
    """Definition of one action: id, label, category, and how to resolve availability/run."""

    id: str
    label: str | Callable[[], str]
    shortcut: str
    category: str  # "create" | "navigation" | "edit" | "destructive" | "separator"
    context_flag: str  # attribute name on MenuContext, e.g. "can_new_page"
    method_name: str  # method name on runner, e.g. "menu_new_page"
    color: str | None = None

    def resolve_label(self) -> str:
        if callable(self.label):
            return self.label()
        return self.label


GLOBAL_EDIT_ACTIONS: tuple[ActionSpec, ...] = (
    ActionSpec(
        "new_page", "New page", "", "create", "can_new_page", "menu_new_page", "#16a34a"
    ),
    ActionSpec(
        "new_database",
        "New database",
        "",
        "create",
        "can_new_database",
        "menu_new_database",
    ),
    ActionSpec(
        "new_folder", "New folder", "", "create", "can_new_folder", "menu_new_folder"
    ),
    ActionSpec(
        "reveal_in_explorer",
        reveal_in_explorer_action_label,
        "",
        "navigation",
        "can_reveal_in_explorer",
        "menu_reveal_in_explorer",
    ),
    ActionSpec("_separator", "", "", "separator", "", ""),
    ActionSpec(
        "add_property",
        "Add property",
        "",
        "edit",
        "can_add_property",
        "menu_add_property",
    ),
    ActionSpec(
        "save_order",
        "Save column order",
        "",
        "edit",
        "can_save_order",
        "menu_save_order",
    ),
    ActionSpec("_separator", "", "", "separator", "", ""),
    ActionSpec(
        "delete", "Delete", "", "destructive", "can_delete", "menu_delete", "#dc2626"
    ),
)


@dataclass
class ResolvedAction:
    """An action with resolved label, availability, and callback."""

    spec: ActionSpec
    label: str
    available: bool
    callback: Callable[[], None]
    is_separator: bool = False


def get_edit_actions(
    menu_context: MenuContextProtocol | None,
    runner: ActionRunnerProtocol | None,
) -> list[ResolvedAction]:
    """Return the list of edit actions with resolved labels and availability."""
    result: list[ResolvedAction] = []
    for spec in GLOBAL_EDIT_ACTIONS:
        if spec.id == "_separator":
            result.append(
                ResolvedAction(
                    spec=spec,
                    label="",
                    available=False,
                    callback=lambda: None,
                    is_separator=True,
                )
            )
            continue
        available = (
            getattr(menu_context, spec.context_flag, False)
            if menu_context is not None
            else False
        )
        method = getattr(runner, spec.method_name, None) if runner is not None else None

        def make_callback(meth: Callable[[], None] | None) -> Callable[[], None]:
            def _run() -> None:
                if meth is not None:
                    meth()

            return _run

        callback = make_callback(method)
        result.append(
            ResolvedAction(
                spec=spec,
                label=spec.resolve_label(),
                available=available,
                callback=callback,
            )
        )
    return result


def get_edit_actions_for_command_palette(
    menu_context: MenuContextProtocol | None,
    runner: ActionRunnerProtocol | None,
    *,
    extra_actions: list[tuple[str, str, Callable[[], None]]] | None = None,
) -> list[tuple[str, str, Callable[[], None]]]:
    """Return (label, shortcut, callback) for the command palette."""
    out: list[tuple[str, str, Callable[[], None]]] = []
    if extra_actions:
        out.extend(extra_actions)
    for resolved_action in get_edit_actions(menu_context, runner):
        if resolved_action.is_separator:
            continue
        out.append(
            (
                resolved_action.label,
                resolved_action.spec.shortcut,
                resolved_action.callback,
            )
        )
    return out


# ─── Tree context (vault sidebar right-click) ─────────────────────────────────

TreeSelectionType = str  # "file" | "folder" | "database" | "empty"

_TREE_LABELS: dict[str, str | Callable[[], str]] = {
    "open": "Open",
    "open_new_window": "Open in new window",
    "reveal": reveal_in_explorer_action_label,
    "new_page": "New page",
    "new_database": "New database",
    "new_folder": "New folder",
    "delete": "Delete",
}

_TREE_COLORS: dict[str, str | None] = {
    "open": None,
    "open_new_window": None,
    "reveal": None,
    "new_page": "#16a34a",
    "new_database": None,
    "new_folder": None,
    "delete": "#dc2626",
}

TREE_ACTION_ORDER_BY_TYPE: dict[TreeSelectionType, list[str]] = {
    "file": ["open", "reveal", "_separator", "delete"],
    "database": ["open", "open_new_window", "reveal", "_separator", "new_page"],
    "folder": ["reveal", "new_page", "new_database", "new_folder"],
    "empty": ["reveal", "new_page", "new_database", "new_folder"],
}


def get_tree_actions(selection_type: TreeSelectionType) -> list[ActionItem]:
    """Return tree context menu items for the given selection type."""
    order = TREE_ACTION_ORDER_BY_TYPE.get(selection_type, [])
    result: list[ActionItem] = []
    for action_id in order:
        if action_id == "_separator":
            result.append(ActionItem("_separator", "", None, is_separator=True))
            continue
        label_source = _TREE_LABELS.get(action_id, action_id)
        label = label_source() if callable(label_source) else label_source
        result.append(
            ActionItem(id=action_id, label=label, color=_TREE_COLORS.get(action_id))
        )
    return result


# ─── Pages view options menu ──────────────────────────────────────────────────

PAGES_VIEW_ACTIONS: list[ActionItem] = action_items_from_specs(
    [
        ("new_page", "New page", "#16a34a"),
        ("_separator", "", None),
        ("add_property", "Add property", None),
        ("save_order", "Save column order", None),
    ]
)


def get_pages_view_actions() -> list[ActionItem]:
    """Return the list of actions for the pages view options menu."""
    return list(PAGES_VIEW_ACTIONS)


# ─── Editor view options menu ────────────────────────────────────────────────

EDITOR_VIEW_ACTIONS: list[ActionItem] = action_items_from_specs(
    [
        ("add_property", "Add property", "#16a34a"),
        ("_separator", "", None),
        ("delete", "Delete", "#dc2626"),
    ]
)


def get_editor_view_actions() -> list[ActionItem]:
    """Return the list of actions for the editor view options menu."""
    return list(EDITOR_VIEW_ACTIONS)
