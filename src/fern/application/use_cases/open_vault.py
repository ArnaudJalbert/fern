"""Use case: open a vault using the repository's configured path."""

from __future__ import annotations

from dataclasses import dataclass

from fern.domain.entities import Page
from fern.domain.repositories.vault_repository import VaultRepository


class OpenVaultUseCase:
    """Open a vault; path is configured on the repository. Returns output DTO only."""

    @dataclass(frozen=True)
    class Input:
        """No input (path is on the repository)."""

        pass

    @dataclass(frozen=True)
    class PropertyOutput:
        id: str
        name: str
        type: str
        mandatory: bool = False

    @dataclass(frozen=True)
    class PagePropertyOutput:
        id: str
        name: str
        type: str
        value: object
        mandatory: bool = False

    @dataclass(frozen=True)
    class PageOutput:
        id: int
        title: str
        content: str
        properties: tuple[OpenVaultUseCase.PagePropertyOutput, ...]

    @dataclass(frozen=True)
    class DatabaseOutput:
        name: str
        pages: tuple[OpenVaultUseCase.PageOutput, ...]
        schema: tuple[OpenVaultUseCase.PropertyOutput, ...]
        property_order: tuple[str, ...]

    @dataclass(frozen=True)
    class Output:
        success: bool
        vault_name: str = ""
        databases: tuple[OpenVaultUseCase.DatabaseOutput, ...] = ()

    def __init__(self, vault_repository: VaultRepository) -> None:
        self._vault_repository = vault_repository

    def execute(self, input_data: Input) -> Output:
        """Return output DTO for the vault at the repository's path, or success=False if invalid."""
        vault = self._vault_repository.get()
        if vault is None:
            return self.Output(success=False)
        databases = tuple(
            self._database_to_output(db) for db in vault.databases
        )
        return self.Output(
            success=True,
            vault_name=vault.name,
            databases=databases,
        )

    def _ordered_schema(self, properties: list, property_order: list):
        """Return property outputs in display order (property_order, then rest)."""
        order = list(property_order) or []
        by_id = {p.id: p for p in properties}
        ordered = [by_id[i] for i in order if i in by_id]
        ordered += [p for p in properties if p.id not in order]
        return tuple(
            self.PropertyOutput(
                id=p.id, name=p.name, type=p.type.key(), mandatory=p.mandatory
            )
            for p in ordered
        )

    def _database_to_output(self, db) -> DatabaseOutput:
        schema = self._ordered_schema(db.properties, db.property_order)
        order = tuple(db.property_order) if db.property_order else tuple(p.id for p in db.properties)
        return self.DatabaseOutput(
            name=db.name,
            pages=tuple(self._page_to_output(p, db.properties) for p in db.pages),
            schema=schema,
            property_order=order,
        )

    def _page_to_output(self, page: Page, db_properties: list) -> PageOutput:
        id_prop = self.PagePropertyOutput(id="id", name="ID", type="id", value=page.id, mandatory=True)
        title_prop = self.PagePropertyOutput(id="title", name="Title", type="title", value=page.title, mandatory=True)
        user_props = tuple(
            self.PagePropertyOutput(
                id=p.id, name=p.name, type=p.type.key(), value=p.value
            )
            for p in page.properties
        )
        return self.PageOutput(
            id=page.id,
            title=page.title,
            content=page.content,
            properties=(id_prop, title_prop, *user_props),
        )
