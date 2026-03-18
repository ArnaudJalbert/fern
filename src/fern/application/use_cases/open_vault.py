"""Use case: open a vault using the repository's configured path."""

from __future__ import annotations

from dataclasses import dataclass

from fern.application.errors import VaultNotFoundError
from fern.domain.entities import Page, StatusProperty
from fern.domain.repositories.vault_repository import VaultRepository


class OpenVaultUseCase:
    """Open a vault; path is configured on the repository. Returns output DTO only."""

    @dataclass(frozen=True)
    class Input:
        """No input (path is on the repository)."""

        pass

    @dataclass(frozen=True)
    class ChoiceOutput:
        """DTO for a single status choice (name, category, color)."""

        name: str
        category: str
        color: str

    @dataclass(frozen=True)
    class IdPropertyOutput:
        """Schema output for an id property."""

        id: str
        name: str
        type: str = "id"
        mandatory: bool = True

    @dataclass(frozen=True)
    class TitlePropertyOutput:
        """Schema output for a title property."""

        id: str
        name: str
        type: str = "title"
        mandatory: bool = True

    @dataclass(frozen=True)
    class BooleanPropertyOutput:
        """Schema output for a boolean property."""

        id: str
        name: str
        type: str = "boolean"
        mandatory: bool = False

    @dataclass(frozen=True)
    class StringPropertyOutput:
        """Schema output for a string property."""

        id: str
        name: str
        type: str = "string"
        mandatory: bool = False

    @dataclass(frozen=True)
    class StatusPropertyOutput:
        """Schema output for a status property; includes choices."""

        id: str
        name: str
        type: str = "status"
        mandatory: bool = False
        choices: tuple[OpenVaultUseCase.ChoiceOutput, ...] = ()

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
        schema: tuple[
            OpenVaultUseCase.IdPropertyOutput
            | OpenVaultUseCase.TitlePropertyOutput
            | OpenVaultUseCase.BooleanPropertyOutput
            | OpenVaultUseCase.StringPropertyOutput
            | OpenVaultUseCase.StatusPropertyOutput,
            ...,
        ]
        property_order: tuple[str, ...]

    @dataclass(frozen=True)
    class Output:
        vault_name: str
        databases: tuple[OpenVaultUseCase.DatabaseOutput, ...]

    def __init__(self, vault_repository: VaultRepository) -> None:
        """Initialize the use case with the vault repository.

        Args:
            vault_repository: The repository for loading the vault at its path.
        """
        self._vault_repository = vault_repository

    def execute(self, input_data: Input) -> Output:
        """Return output DTO for the vault at the repository's path.

        Raises:
            VaultNotFoundError: If the vault path is invalid or not found.
        """
        vault = self._vault_repository.get()
        if vault is None:
            raise VaultNotFoundError()

        databases = tuple(
            self._database_to_output(database) for database in vault.databases
        )
        return self.Output(vault_name=vault.name, databases=databases)

    def _ordered_schema(self, properties: list, property_order: list):
        """Return property outputs in display order (property_order, then rest)."""
        order = list(property_order) or []
        by_id = {schema_property.id: schema_property for schema_property in properties}
        ordered = [by_id[order_entry] for order_entry in order if order_entry in by_id]
        ordered += [
            schema_property
            for schema_property in properties
            if schema_property.id not in order
        ]
        result = []
        for schema_property in ordered:
            result.append(self._schema_property_to_output(schema_property))
        return tuple(result)

    def _schema_property_to_output(
        self,
        schema_property,
    ) -> (
        "OpenVaultUseCase.IdPropertyOutput"
        | "OpenVaultUseCase.TitlePropertyOutput"
        | "OpenVaultUseCase.BooleanPropertyOutput"
        | "OpenVaultUseCase.StringPropertyOutput"
        | "OpenVaultUseCase.StatusPropertyOutput"
    ):
        """Build the type-specific output DTO for a schema property."""
        key = schema_property.type_key()
        if key == "id":
            return self.IdPropertyOutput(
                id=schema_property.id,
                name=schema_property.name,
                mandatory=schema_property.mandatory,
            )
        if key == "title":
            return self.TitlePropertyOutput(
                id=schema_property.id,
                name=schema_property.name,
                mandatory=schema_property.mandatory,
            )
        if key == "boolean":
            return self.BooleanPropertyOutput(
                id=schema_property.id,
                name=schema_property.name,
                mandatory=schema_property.mandatory,
            )
        if key == "string":
            return self.StringPropertyOutput(
                id=schema_property.id,
                name=schema_property.name,
                mandatory=schema_property.mandatory,
            )
        choices_out = ()
        if isinstance(schema_property, StatusProperty):
            choices_out = tuple(
                self.ChoiceOutput(
                    name=choice.name,
                    category=choice.category,
                    color=choice.color,
                )
                for choice in schema_property.choices
            )
        return self.StatusPropertyOutput(
            id=schema_property.id,
            name=schema_property.name,
            mandatory=schema_property.mandatory,
            choices=choices_out,
        )

    def _database_to_output(self, database) -> DatabaseOutput:
        schema = self._ordered_schema(
            database.properties,
            database.property_order,
        )
        order = (
            tuple(database.property_order)
            if database.property_order
            else tuple(schema_property.id for schema_property in database.properties)
        )
        return self.DatabaseOutput(
            name=database.name,
            pages=tuple(
                self._page_to_output(page, database.properties)
                for page in database.pages
            ),
            schema=schema,
            property_order=order,
        )

    def _page_to_output(
        self,
        page: Page,
        database_properties: list,
    ) -> PageOutput:
        id_property = self.PagePropertyOutput(
            id="id",
            name="ID",
            type="id",
            value=page.id,
            mandatory=True,
        )
        title_property = self.PagePropertyOutput(
            id="title",
            name="Title",
            type="title",
            value=page.title,
            mandatory=True,
        )
        user_properties = tuple(
            self.PagePropertyOutput(
                id=page_property.id,
                name=page_property.name,
                type=page_property.type_key(),
                value=page_property.value,
            )
            for page_property in page.properties
        )
        return self.PageOutput(
            id=page.id,
            title=page.title,
            content=page.content,
            properties=(id_property, title_property, *user_properties),
        )
