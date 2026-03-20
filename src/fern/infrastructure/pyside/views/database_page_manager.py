"""Manages database-page operations: select DB, save, create, delete, refresh.

Keeps all the controller calls and page-list bookkeeping out of VaultView.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from fern.infrastructure.controller import VaultController, VaultOutput

from .page_data import PageData, PropertyData

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


class DatabasePageManager:
    """Orchestrates database page CRUD through the VaultController."""

    def __init__(self, vault_controller: VaultController, vault_path: Path) -> None:
        self._vault_controller = vault_controller
        self._vault_path = vault_path
        self.current_database_name: str = ""
        self.current_property_order: tuple[str, ...] = ()
        self.current_schema: tuple = ()

    # -- helpers ---------------------------------------------------------------

    @staticmethod
    def pages_from_output(db) -> list[PageData]:
        """Convert a DatabaseOutput's pages to a list of PageData."""
        return [PageData.from_use_case_page(p) for p in getattr(db, "pages", ())]

    def find_database(self, output: VaultOutput, name: str):
        """Return the DatabaseOutput with the given name, or None."""
        for d in output.databases:
            if getattr(d, "name", "") == name:
                return d
        return None

    # -- select ----------------------------------------------------------------

    def select_database(
        self, database
    ) -> tuple[list[PageData], object, tuple[str, ...]] | None:
        """Refresh the vault, select a database, and return (pages, schema, property_order).

        Returns None if the database is not found after refresh.
        """
        name = getattr(database, "name", str(database))
        fresh = self._vault_controller.open_vault_refresh()
        db = self.find_database(fresh, name)
        if db is None:
            return None
        self.current_database_name = name
        self.current_property_order = getattr(db, "property_order", ()) or ()
        self.current_schema = getattr(db, "schema", ()) or ()
        pages = self.pages_from_output(db)
        return pages, self.current_schema, self.current_property_order

    # -- save ------------------------------------------------------------------

    def save_page(
        self, page_id: int, title: str, content: str, properties: list | None = None
    ) -> None:
        """Persist page changes to disk via the controller."""
        if not self.current_database_name:
            return
        self._vault_controller.save_page(
            self.current_database_name,
            page_id,
            title,
            content,
            properties,
        )

    # -- create ----------------------------------------------------------------

    def create_page(
        self,
        title: str = "Untitled",
        content: str = "",
        schema: list | None = None,
    ) -> PageData:
        """Create a new page in the current database and return a PageData.

        If schema is provided, the page's properties will include all schema
        properties (with default values) so the editor shows every field.
        """
        out = self._vault_controller.create_page(
            self.current_database_name,
            title=title,
            content=content,
        )
        mandatory = PageData.make_mandatory_props(out.page_id, out.title)
        if not schema:
            return PageData(
                id=out.page_id,
                title=out.title,
                content=out.content,
                properties=mandatory,
            )
        # Build full properties from schema so the editor shows all fields
        order_ids = [i for i in self.current_property_order if i not in ("id", "title")]
        by_id = {getattr(p, "id", ""): p for p in mandatory}
        for prop in schema:
            pid = getattr(prop, "id", "")
            if pid in ("id", "title"):
                continue
            property_type = getattr(prop, "type", "string")
            if property_type == "boolean":
                default = False
            elif property_type == "status":
                default = ""
            else:
                default = None
            by_id[pid] = PropertyData(
                id=pid,
                name=getattr(prop, "name", pid),
                type=property_type,
                value=default,
                mandatory=False,
            )
        ordered = [by_id[i] for i in order_ids if i in by_id]
        rest = [
            by_id[i] for i in by_id if i not in ("id", "title") and i not in order_ids
        ]
        properties = list(mandatory) + ordered + rest
        return PageData(
            id=out.page_id,
            title=out.title,
            content=out.content,
            properties=properties,
        )

    # -- delete ----------------------------------------------------------------

    def delete_page(self, page_id: int, parent: QWidget | None = None) -> bool:
        """Delete a page and return True if deleted. Shows error dialog if parent given."""
        if not self.current_database_name:
            return False
        try:
            self._vault_controller.delete_page(
                self.current_database_name,
                page_id,
            )
            return True
        except Exception as e:
            if parent is not None:
                from fern.infrastructure.pyside.components import show_error

                show_error(parent, str(e), title="Delete page")
            return False

    # -- refresh ---------------------------------------------------------------

    def refresh_pages_and_schema(
        self,
        parent: QWidget | None = None,
    ) -> tuple[list[PageData], object, tuple[str, ...]] | None:
        """Reload the vault and return fresh (pages, schema, property_order) for the current DB."""
        if not self.current_database_name:
            return None
        try:
            fresh = self._vault_controller.open_vault_refresh()
        except Exception as e:
            if parent is not None:
                from fern.infrastructure.pyside.components import show_error

                show_error(parent, str(e))
            return None
        db = self.find_database(fresh, self.current_database_name)
        if db is None:
            return None
        self.current_property_order = getattr(db, "property_order", ()) or ()
        self.current_schema = getattr(db, "schema", ()) or ()
        pages = self.pages_from_output(db)
        return pages, self.current_schema, self.current_property_order

    # -- property value --------------------------------------------------------

    def update_page_property(
        self,
        page_id: int,
        property_id: str,
        value,
        parent: QWidget | None = None,
    ) -> bool:
        """Persist a single property value change. Returns True on success. Shows error if parent given."""
        if not self.current_database_name:
            return False
        try:
            self._vault_controller.update_page_property(
                self.current_database_name,
                page_id,
                property_id,
                value,
            )
            return True
        except Exception as e:
            if parent is not None:
                from fern.infrastructure.pyside.components import show_error

                show_error(parent, str(e), title="Update property")
            return False
