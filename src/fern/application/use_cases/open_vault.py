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

    @dataclass(frozen=True)
    class PagePropertyOutput:
        id: str
        name: str
        type: str
        value: object

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
            self.DatabaseOutput(
                name=db.name,
                pages=tuple(self._page_to_output(p) for p in db.pages),
                schema=tuple(
                    self.PropertyOutput(id=p.id, name=p.name, type=p.type.key())
                    for p in db.manifest.properties
                ),
            )
            for db in vault.databases
        )
        return self.Output(
            success=True,
            vault_name=vault.name,
            databases=databases,
        )

    def _page_to_output(self, page: Page) -> PageOutput:
        return self.PageOutput(
            id=page.id,
            title=page.title,
            content=page.content,
            properties=tuple(
                self.PagePropertyOutput(
                    id=p.id, name=p.name, type=p.type.key(), value=p.value
                )
                for p in page.properties
            ),
        )
