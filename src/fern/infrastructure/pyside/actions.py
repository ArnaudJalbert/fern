"""
Central registry of actions by category, reusable across menu bar, command palette,
context menus (tree, pages, editor). Availability and execution depend on context.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from fern.infrastructure.pyside.utils import reveal_in_explorer_action_label


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
    color: str | None = (
        None  # for colored menu items, e.g. "#16a34a" green, "#dc2626" red
    )

    def resolve_label(self) -> str:
        if callable(self.label):
            return self.label()
        return self.label


# Edit menu / command palette actions (order and categories).
# Separators are entries with id "_separator" and no method_name.
GLOBAL_EDIT_ACTIONS: tuple[ActionSpec, ...] = (
    ActionSpec(
        "new_page",
        "New page",
        "",
        "create",
        "can_new_page",
        "menu_new_page",
        "#16a34a",
    ),
    ActionSpec(
        "new_database",
        "New database",
        "",
        "create",
        "can_new_database",
        "menu_new_database",
        None,
    ),
    ActionSpec(
        "new_folder",
        "New folder",
        "",
        "create",
        "can_new_folder",
        "menu_new_folder",
        None,
    ),
    ActionSpec(
        "reveal_in_explorer",
        reveal_in_explorer_action_label,
        "",
        "navigation",
        "can_reveal_in_explorer",
        "menu_reveal_in_explorer",
        None,
    ),
    ActionSpec("_separator", "", "", "separator", "", "", None),
    ActionSpec(
        "add_property",
        "Add property",
        "",
        "edit",
        "can_add_property",
        "menu_add_property",
        None,
    ),
    ActionSpec(
        "save_order",
        "Save column order",
        "",
        "edit",
        "can_save_order",
        "menu_save_order",
        None,
    ),
    ActionSpec("_separator", "", "", "separator", "", "", None),
    ActionSpec(
        "delete",
        "Delete",
        "",
        "destructive",
        "can_delete",
        "menu_delete",
        "#dc2626",
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
    """
    Return the list of edit actions with resolved labels and availability.
    Use for Edit menu, command palette, and any context that uses menu_context + runner.
    """
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
                is_separator=False,
            )
        )
    return result


def get_edit_actions_for_command_palette(
    menu_context: MenuContextProtocol | None,
    runner: ActionRunnerProtocol | None,
    *,
    extra_actions: list[tuple[str, str, Callable[[], None]]] | None = None,
) -> list[tuple[str, str, Callable[[], None]]]:
    """
    Return (label, shortcut, callback) for the command palette.
    Skips separators. Prepends extra_actions (e.g. Open..., See databases...) if given.
    """
    out: list[tuple[str, str, Callable[[], None]]] = []
    if extra_actions:
        out.extend(extra_actions)
    for ra in get_edit_actions(menu_context, runner):
        if ra.is_separator:
            continue
        out.append((ra.label, ra.spec.shortcut, ra.callback))
    return out


# ─── Tree context (vault sidebar right‑click) ─────────────────────────────────

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

# Order of action ids (and separators) per selection type for the tree context menu.
TREE_ACTION_ORDER_BY_TYPE: dict[TreeSelectionType, list[str]] = {
    "file": ["open", "reveal", "_separator", "delete"],
    "database": ["open", "open_new_window", "reveal", "_separator", "new_page"],
    "folder": ["reveal", "new_page", "new_database", "new_folder"],
    "empty": ["reveal", "new_page", "new_database", "new_folder"],
}


@dataclass(frozen=True)
class TreeActionItem:
    """One action item for the tree context menu: id, resolved label, optional color."""

    id: str
    label: str
    color: str | None
    is_separator: bool = False


def get_tree_actions(selection_type: TreeSelectionType) -> list[TreeActionItem]:
    """
    Return the list of tree context menu items (order and labels) for the given
    selection type. The view supplies callbacks when building the menu.
    """
    order = TREE_ACTION_ORDER_BY_TYPE.get(selection_type, [])
    result: list[TreeActionItem] = []
    for aid in order:
        if aid == "_separator":
            result.append(TreeActionItem("_separator", "", None, is_separator=True))
            continue
        label_src = _TREE_LABELS.get(aid, aid)
        label = label_src() if callable(label_src) else label_src
        result.append(
            TreeActionItem(
                id=aid,
                label=label,
                color=_TREE_COLORS.get(aid),
                is_separator=False,
            )
        )
    return result


# ─── Pages view (database table) options menu ─────────────────────────────────

PAGES_VIEW_ACTIONS: list[tuple[str, str, str | None]] = [
    # (id, label, color)
    ("new_page", "New page", "#16a34a"),
    ("_separator", "", None),
    ("add_property", "Add property", None),
    ("save_order", "Save column order", None),
]


@dataclass(frozen=True)
class PagesViewActionItem:
    """One action item for the pages view options menu."""

    id: str
    label: str
    color: str | None
    is_separator: bool = False


def get_pages_view_actions() -> list[PagesViewActionItem]:
    """Return the list of actions for the pages view options menu."""
    result: list[PagesViewActionItem] = []
    for aid, label, color in PAGES_VIEW_ACTIONS:
        if aid == "_separator":
            result.append(
                PagesViewActionItem("_separator", "", None, is_separator=True)
            )
        else:
            result.append(
                PagesViewActionItem(
                    id=aid, label=label, color=color, is_separator=False
                )
            )
    return result


# ─── Editor view options menu ─────────────────────────────────────────────────

EDITOR_VIEW_ACTIONS: list[tuple[str, str, str | None]] = [
    ("add_property", "Add property", "#16a34a"),
    ("_separator", "", None),
    ("delete", "Delete", "#dc2626"),
]


@dataclass(frozen=True)
class EditorViewActionItem:
    """One action item for the editor view options menu."""

    id: str
    label: str
    color: str | None
    is_separator: bool = False


def get_editor_view_actions() -> list[EditorViewActionItem]:
    """Return the list of actions for the editor view options menu."""
    result: list[EditorViewActionItem] = []
    for aid, label, color in EDITOR_VIEW_ACTIONS:
        if aid == "_separator":
            result.append(
                EditorViewActionItem("_separator", "", None, is_separator=True)
            )
        else:
            result.append(
                EditorViewActionItem(
                    id=aid, label=label, color=color, is_separator=False
                )
            )
    return result
