"""Use case: remove a property from the schema and from all pages."""

from __future__ import annotations

from dataclasses import dataclass

from fern.domain.entities import Manifest
from fern.domain.repositories.manifest_repository import ManifestRepository
from fern.domain.repositories.page_repository import PageRepository


class RemovePropertyUseCase:
    """Remove a property from the manifest and remove its value from every page."""

    @dataclass(frozen=True)
    class Input:
        property_id: str

    @dataclass(frozen=True)
    class Output:
        success: bool

    def __init__(
        self,
        manifest_repository: ManifestRepository,
        page_repository: PageRepository,
    ) -> None:
        self._manifest_repository = manifest_repository
        self._page_repository = page_repository

    def execute(self, input_data: Input) -> Output:
        manifest = self._manifest_repository.get()
        new_properties = [
            p for p in manifest.properties if p.id != input_data.property_id
        ]
        if len(new_properties) == len(manifest.properties):
            return self.Output(success=False)
        self._manifest_repository.save(Manifest(properties=new_properties))
        for page in self._page_repository.list_all():
            new_list = [p for p in page.properties if p.id != input_data.property_id]
            self._page_repository.update(
                page.id, page.title, page.content, properties=new_list
            )
        return self.Output(success=True)
