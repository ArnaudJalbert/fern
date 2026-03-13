"""Manages database property CRUD: add, edit, remove, reorder.

Owns the property-settings dialog and all controller calls related to
schema properties so VaultView doesn't need to know about any of it.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QWidget

from fern.domain.entities import PropertyType
from fern.infrastructure.controller import AppController
from fern.infrastructure.pyside.components import (
    PropertySettingsWidget,
    alert,
    confirm,
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
    def run_settings_dialog(
        title: str,
        form: PropertySettingsWidget,
        parent: QWidget,
    ) -> tuple[str, str] | None:
        """Show a modal property-settings dialog. Returns (name, type_key) or None."""
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
        parsed = self.run_settings_dialog("Add property", form, parent)
        if parsed is None:
            return False
        name, type_key = parsed
        if not name:
            return False
        slug = (
            "".join(c if c.isalnum() or c == "_" else "_" for c in name.strip()).lower()
            or "prop"
        )
        slug = slug.strip("_") or "prop"
        if slug in ("id", "title"):
            slug = f"{slug}_prop"
        out = self._controller.add_property(
            self._vault_path,
            database_name,
            slug,
            name,
            type_key,
        )
        if not out.success:
            alert(parent, "Add property", "A property with that id already exists.")
            return False
        return True

    def add_page_property(
        self, database_name: str, page_id: int, parent: QWidget
    ) -> PropertyData | None:
        """Add a property to a single page only. Returns the new PropertyData on success, else None."""
        form = PropertySettingsWidget(name="", type_key="string", parent=parent)
        parsed = self.run_settings_dialog("Add property to this page", form, parent)
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
        out = self._controller.add_page_property(
            self._vault_path,
            database_name,
            page_id,
            slug,
            name,
            type_key,
        )
        if not out.success:
            alert(
                parent,
                "Add property to page",
                "A property with that id already exists on this page.",
            )
            return None
        ptype = PropertyType.from_key(type_key)
        default = ptype.value.default_value()
        return PropertyData(
            id=slug, name=name, type=type_key, value=default, mandatory=False
        )

    # -- edit ------------------------------------------------------------------

    def edit_property(self, database_name: str, prop, parent: QWidget) -> bool:
        """Show the Edit-property dialog and persist. Returns True if updated."""
        property_id = getattr(prop, "id", "")
        current_name = getattr(prop, "name", property_id)
        type_key = property_type_key(getattr(prop, "type", "string"))
        form = PropertySettingsWidget(
            name=current_name, type_key=type_key, parent=parent
        )
        parsed = self.run_settings_dialog("Edit property", form, parent)
        if parsed is None:
            return False
        name, new_type_key = parsed
        name = name or current_name
        out = self._controller.update_property(
            self._vault_path,
            database_name,
            property_id,
            new_name=name,
            new_type=new_type_key,
        )
        if not out.success:
            alert(parent, "Edit property", "Could not update the property.")
            return False
        return True

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
        out = self._controller.remove_property(
            self._vault_path, database_name, property_id
        )
        if not out.success:
            alert(parent, "Remove property", "Could not remove the property.")
            return False
        return True

    # -- reorder ---------------------------------------------------------------

    def save_order(
        self, database_name: str, order: tuple[str, ...], parent: QWidget
    ) -> bool:
        """Persist column order. Returns True on success."""
        vault_path = Path(self._vault_path).resolve()
        try:
            out = self._controller.update_property_order(
                vault_path, database_name, order
            )
        except Exception as e:
            alert(parent, "Save column order", f"Save failed: {e!s}")
            return False
        if not out.success:
            alert(parent, "Save column order", "Save failed (success=False).")
            return False
        show_toast(parent, "Column order saved")
        return True
