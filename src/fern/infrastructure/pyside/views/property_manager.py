"""Manages database property CRUD: add, edit, remove, reorder.

Owns the property-settings dialog and all controller calls related to
schema properties so VaultView doesn't need to know about any of it.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QWidget

from fern.infrastructure.controller import (
    AppController,
    PageNotFoundError,
    PropertyAlreadyExistsError,
    PropertyAlreadyExistsOnPageError,
    PropertyNotFoundError,
    default_value_for_type,
)
from fern.infrastructure.pyside.components import (
    PropertySettingsWidget,
    confirm,
    run_simple_property_editor,
    run_status_choices_editor,
    show_error,
    show_toast,
)
from fern.infrastructure.pyside.utils import property_type_key

from .page_data import PropertyData


class PropertyManager:
    """Handles property add / edit / remove / reorder through the controller."""

    def __init__(self, controller: AppController, vault_path: Path) -> None:
        self._controller = controller
        self._vault_path = vault_path

    # -- dialog ----------------------------------------------------------------

    @staticmethod
    def run_add_property_dialog(
        title: str,
        form: PropertySettingsWidget,
        parent: QWidget,
    ) -> tuple[str, str] | None:
        """Show the generic Add-property dialog (name + type only). Returns (name, type_key) or None."""
        dialog = QDialog(parent)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout(dialog)
        layout.addWidget(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        result: list[tuple[str, str] | None] = [None]

        def on_accept() -> None:
            result[0] = (form.get_name(), form.get_type_key())
            dialog.accept()

        buttons.accepted.connect(on_accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.exec()
        return result[0]

    # -- add -------------------------------------------------------------------

    def add_property(
        self,
        database_name: str,
        parent: QWidget,
    ) -> bool:
        """Show the Add-property dialog, update schema, and apply to all pages.

        Returns True if the property was added successfully.
        """
        form = PropertySettingsWidget(name="Done", type_key="boolean", parent=parent)
        parsed = self.run_add_property_dialog("Add property", form, parent)
        if parsed is None:
            return False
        name, type_key = parsed
        if not name:
            return False
        if type_key == "status":
            status_result = run_status_choices_editor(
                choices=[], parent=parent, name=name
            )
            if status_result is None:
                return False
            choices, name = status_result
        else:
            choices = None
        slug = (
            "".join(c if c.isalnum() or c == "_" else "_" for c in name.strip()).lower()
            or "prop"
        )
        slug = slug.strip("_") or "prop"
        if slug in ("id", "title"):
            slug = f"{slug}_prop"
        try:
            self._controller.add_property(
                self._vault_path,
                database_name,
                slug,
                name,
                type_key,
                choices=choices if type_key == "status" else None,
            )
        except PropertyAlreadyExistsError as e:
            show_error(parent, e.message, title="Add property")
            return False
        return True

    def add_page_property(
        self, database_name: str, page_id: int, parent: QWidget
    ) -> PropertyData | None:
        """Add a property to a single page only. Returns the new PropertyData on success, else None."""
        form = PropertySettingsWidget(name="", type_key="string", parent=parent)
        parsed = self.run_add_property_dialog("Add property to this page", form, parent)
        if parsed is None:
            return None
        name, type_key = parsed
        if not name:
            return None
        slug = (
            "".join(c if c.isalnum() or c == "_" else "_" for c in name.strip()).lower()
            or "prop"
        )
        slug = slug.strip("_") or "prop"
        if slug in ("id", "title"):
            slug = f"{slug}_prop"
        try:
            self._controller.add_page_property(
                self._vault_path,
                database_name,
                page_id,
                slug,
                name,
                type_key,
            )
        except (PageNotFoundError, PropertyAlreadyExistsOnPageError) as e:
            show_error(parent, e.message, title="Add property to page")
            return None
        default = default_value_for_type(type_key)
        return PropertyData(
            id=slug, name=name, type=type_key, value=default, mandatory=False
        )

    # -- edit ------------------------------------------------------------------

    def edit_property(self, database_name: str, prop, parent: QWidget) -> bool:
        """Show the type-specific Edit-property dialog and persist. Returns True if updated."""
        property_id = getattr(prop, "id", "")
        current_name = getattr(prop, "name", property_id)
        type_key = property_type_key(getattr(prop, "type", "string"))

        try:
            if type_key == "status":
                choices_attr = list(getattr(prop, "choices", None) or [])
                result = run_status_choices_editor(
                    choices=choices_attr, parent=parent, name=current_name
                )
                if result is None:
                    return False
                choices, name = result
                self._controller.update_property(
                    self._vault_path,
                    database_name,
                    property_id,
                    new_name=name,
                    new_type=None,
                    new_choices=choices,
                )
            else:
                name = run_simple_property_editor(
                    type_key,
                    name=current_name,
                    parent=parent,
                )
                if name is None:
                    return False
                self._controller.update_property(
                    self._vault_path,
                    database_name,
                    property_id,
                    new_name=name,
                    new_type=None,
                    new_choices=None,
                )
            return True
        except PropertyNotFoundError as e:
            show_error(parent, e.message, title="Edit property")
            return False

    # -- remove ----------------------------------------------------------------

    def remove_property(
        self, database_name: str, property_id: str, parent: QWidget
    ) -> bool:
        """Confirm and remove. Returns True if removed."""
        if not confirm(
            parent,
            "Remove property",
            "Remove this property from the database? It will be removed from all pages.",
            destructive=True,
            confirm_label="Remove",
            cancel_label="Cancel",
        ):
            return False
        try:
            self._controller.remove_property(
                self._vault_path, database_name, property_id
            )
        except PropertyNotFoundError as e:
            show_error(parent, e.message, title="Remove property")
            return False
        return True

    # -- reorder ---------------------------------------------------------------

    def save_order(
        self, database_name: str, order: tuple[str, ...], parent: QWidget
    ) -> bool:
        """Persist column order. Returns True on success."""
        vault_path = Path(self._vault_path).resolve()
        try:
            self._controller.update_property_order(vault_path, database_name, order)
        except Exception as e:
            show_error(parent, str(e), title="Save column order")
            return False
        show_toast(parent, "Column order saved")
        return True
