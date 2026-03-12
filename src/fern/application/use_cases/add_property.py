"""Use case: add a property to the schema and set default value on all pages."""

from __future__ import annotations

from dataclasses import dataclass

from fern.domain.entities import Manifest, Property, PropertyType
from fern.domain.repositories.manifest_repository import ManifestRepository
from fern.domain.repositories.page_repository import PageRepository


class AddPropertyUseCase:
    """Add a property to the manifest and add its default value to every page."""

    @dataclass(frozen=True)
    class Input:
        property_id: str
        name: str
        type: PropertyType

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
        for p in manifest.properties:
            if p.id == input_data.property_id:
                return self.Output(success=False)
        manifest = Manifest(
            properties=[
                *manifest.properties,
                Property(
                    id=input_data.property_id,
                    name=input_data.name,
                    type=input_data.type,
                ),
            ],
        )
        self._manifest_repository.save(manifest)
        default = input_data.type.value.default_value()
        new_prop = Property(
            id=input_data.property_id,
            name=input_data.name,
            type=input_data.type,
            value=default,
        )
        for page in self._page_repository.list_all():
            new_list = [*page.properties, new_prop]
            self._page_repository.update(
                page.id, page.title, page.content, properties=new_list
            )
        return self.Output(success=True)
