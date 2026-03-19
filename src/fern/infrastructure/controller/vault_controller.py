"""Controller for operations on a specific vault (bound to a vault path)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable  # noqa: F401 - used in type hints

from fern.application.dtos import (
    AddPagePropertyInputDTO,
    AddPropertyInputDTO,
    ApplyPropertyToPagesInputDTO,
    BooleanPropertyInputDTO,
    ChoiceDTO,
    PropertyInputDTO,
    PropertyValueDTO,
    StatusPropertyInputDTO,
    StringPropertyInputDTO,
    UpdatePropertyInputDTO,
)
from fern.application.errors import (
    PageNotFoundError as AppPageNotFoundError,
)
from fern.application.errors import (
    PropertyAlreadyExistsError as AppPropertyAlreadyExistsError,
)
from fern.application.errors import (
    PropertyAlreadyExistsOnPageError as AppPropertyAlreadyExistsOnPageError,
)
from fern.application.errors import (
    PropertyNotFoundError as AppPropertyNotFoundError,
)
from fern.application.errors import (
    PropertyNotFoundOnPageError as AppPropertyNotFoundOnPageError,
)
from fern.application.errors import (
    VaultNotFoundError as AppVaultNotFoundError,
)
from fern.application.repositories.database_repository import DatabaseRepository
from fern.application.repositories.vault_repository import VaultRepository
from fern.application.use_cases.add_page_property import AddPagePropertyUseCase
from fern.application.use_cases.add_property import AddPropertyUseCase
from fern.application.use_cases.apply_property_to_pages import (
    ApplyPropertyToPagesUseCase,
)
from fern.application.use_cases.create_page import CreatePageUseCase
from fern.application.use_cases.delete_page import DeletePageUseCase
from fern.application.use_cases.open_vault import OpenVaultUseCase
from fern.application.use_cases.remove_property import RemovePropertyUseCase
from fern.application.use_cases.save_page import SavePageUseCase
from fern.application.use_cases.update_page_property import UpdatePagePropertyUseCase
from fern.application.use_cases.update_property import UpdatePropertyUseCase
from fern.application.use_cases.update_property_order import UpdatePropertyOrderUseCase
from fern.infrastructure.controller.errors import (
    PageNotFoundError,
    PropertyAlreadyExistsError,
    PropertyAlreadyExistsOnPageError,
    PropertyNotFoundError,
    PropertyNotFoundOnPageError,
    VaultNotFoundError,
)
from fern.infrastructure.controller.factories.page_repository_factory import (
    PageRepositoryFactory,
)
from fern.interface_adapters.repositories.vault_database_repository import (
    is_database_folder,
)


@dataclass(frozen=True)
class CreateRootPageOutput:
    """Result of creating a new page at the vault root (id + title)."""

    path: Path
    page_id: int
    title: str
    content: str


class VaultController:
    """Controller for vault-specific operations. Bound to a specific vault path.

    This controller handles all operations that work within a particular vault,
    such as managing pages, databases, and properties. It does not handle
    recent vaults or vault creation/deletion.
    """

    def __init__(
        self,
        *,
        vault_path: Path,
        vault_repository: VaultRepository,
        database_repository: DatabaseRepository,
        page_repository_factory: PageRepositoryFactory,
    ) -> None:
        """Initialize a vault-specific controller.

        Args:
            vault_path: The path to the vault this controller operates on.
            vault_repository: Repository for vault operations (bound to vault_path).
            database_repository: Repository for database schema operations (bound to vault_path).
            page_repository_factory: Factory for creating page repositories for specific database paths.
        """
        self._vault_path = vault_path
        self._vault_repository = vault_repository
        self._database_repository = database_repository
        self._page_repository_factory = page_repository_factory

    def open_vault(self) -> OpenVaultUseCase.Output:
        """Open the vault and return its data."""
        use_case = OpenVaultUseCase(self._vault_repository)
        try:
            return use_case.execute(OpenVaultUseCase.Input())
        except AppVaultNotFoundError as error:
            raise VaultNotFoundError(
                path=self._vault_path, message=str(error)
            ) from error

    def open_vault_refresh(self) -> OpenVaultUseCase.Output:
        """Re-open the vault and return fresh output (e.g. after schema change)."""
        return self.open_vault()

    def save_page(
        self,
        database_name: str,
        page_id: int,
        title: str,
        content: str,
        properties: list | None = None,
    ) -> None:
        """Persist page changes to disk."""
        property_dtos = self._ui_to_property_value_dtos(properties)
        page_repo = self._page_repository_factory.create(self._db_dir(database_name))
        use_case = SavePageUseCase(page_repo)
        use_case.execute(
            SavePageUseCase.Input(
                page_id=page_id,
                title=title,
                content=content,
                properties=property_dtos,
            )
        )

    def create_page(
        self,
        database_name: str,
        title: str = "Untitled",
        content: str = "",
    ) -> CreatePageUseCase.Output:
        """Create a new page in the given database; returns (page_id, title, content)."""
        page_repo = self._page_repository_factory.create(self._db_dir(database_name))
        use_case = CreatePageUseCase(page_repo)
        return use_case.execute(CreatePageUseCase.Input(title=title, content=content))

    def create_root_page(self, title: str = "Untitled") -> CreateRootPageOutput:
        """Create a new page at the vault root (id + title); returns path, page_id, title, content."""
        page_repo = self._page_repository_factory.create(self._vault_path)
        use_case = CreatePageUseCase(page_repo)
        output = use_case.execute(CreatePageUseCase.Input(title=title, content=""))
        path = self._vault_path / f"{output.title}.md"
        return CreateRootPageOutput(
            path=path,
            page_id=output.page_id,
            title=output.title,
            content=output.content,
        )

    def create_database(self, folder_rel: str) -> bool:
        """Create a database.json marker in the given folder (relative to vault).

        Returns True if created, False if it already exists.
        """
        import json

        from fern.interface_adapters.repositories.vault_database_repository import (
            DATABASE_MARKER,
        )

        target = self._vault_path / folder_rel
        marker = target / DATABASE_MARKER
        if marker.exists():
            return False
        target.mkdir(parents=True, exist_ok=True)
        data = {"properties": [], "propertyOrder": []}
        marker.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return True

    def delete_page(
        self,
        database_name: str,
        page_id: int,
    ) -> None:
        """Remove the page from the given database. Raises PageNotFoundError if not found."""
        page_repo = self._page_repository_factory.create(self._db_dir(database_name))
        use_case = DeletePageUseCase(page_repo)
        try:
            return use_case.execute(DeletePageUseCase.Input(page_id=page_id))
        except AppPageNotFoundError as error:
            raise PageNotFoundError(
                page_id=page_id,
                database_name=database_name,
                vault_path=self._vault_path,
                message=str(error),
            ) from error

    def add_property(
        self,
        database_name: str,
        property_id: str,
        name: str,
        property_type: str,
        choices: list | None = None,
    ) -> None:
        """Add a property to the schema and apply it to all pages. Raises PropertyAlreadyExistsError if id exists."""
        property_dto = self._build_property_dto(
            property_id, name, property_type, choices
        )

        # Add to schema using use case
        try:
            add_property_uc = AddPropertyUseCase(self._database_repository)
            add_property_uc.execute(
                AddPropertyInputDTO(
                    database_name=database_name,
                    property=property_dto,
                )
            )
        except AppPropertyAlreadyExistsError as error:
            raise PropertyAlreadyExistsError(
                property_id=property_id,
                database_name=database_name,
                vault_path=self._vault_path,
                message=str(error),
            ) from error

        # Apply to pages
        page_repo = self._page_repository_factory.create(self._db_dir(database_name))
        apply_uc = ApplyPropertyToPagesUseCase(page_repo)
        apply_uc.execute(
            ApplyPropertyToPagesInputDTO(
                property_id=property_id,
                name=name,
                type_key=property_type,
            )
        )

    def add_page_property(
        self,
        database_name: str,
        page_id: int,
        property_id: str,
        name: str,
        property_type: str,
    ) -> None:
        """Add a property to a single page only. Raises PageNotFoundError or PropertyAlreadyExistsOnPageError."""
        page_repo = self._page_repository_factory.create(self._db_dir(database_name))
        use_case = AddPagePropertyUseCase(page_repo)
        try:
            return use_case.execute(
                AddPagePropertyInputDTO(
                    page_id=page_id,
                    property_id=property_id,
                    name=name,
                    type_key=property_type,
                )
            )
        except AppPageNotFoundError as error:
            raise PageNotFoundError(
                page_id=page_id,
                database_name=database_name,
                vault_path=self._vault_path,
                message=str(error),
            ) from error
        except AppPropertyAlreadyExistsOnPageError as error:
            raise PropertyAlreadyExistsOnPageError(
                page_id=page_id,
                property_id=property_id,
                vault_path=self._vault_path,
                message=str(error),
            ) from error

    def remove_property(
        self,
        database_name: str,
        property_id: str,
    ) -> None:
        """Remove a property from the schema and from all pages. Raises PropertyNotFoundError if not in schema."""
        use_case = RemovePropertyUseCase(
            self._database_repository,
            self._page_repository_factory.create(self._db_dir(database_name)),
        )
        try:
            return use_case.execute(
                RemovePropertyUseCase.Input(
                    database_name=database_name,
                    property_id=property_id,
                )
            )
        except AppPropertyNotFoundError as error:
            raise PropertyNotFoundError(
                property_id=property_id,
                database_name=database_name,
                vault_path=self._vault_path,
                message=str(error),
            ) from error

    def update_property(
        self,
        database_name: str,
        property_id: str,
        new_name: str | None = None,
        new_type: str | None = None,
        new_choices: list | None = None,
    ) -> None:
        """Update a property's name and/or type in the schema and on all pages. Raises PropertyNotFoundError if not found."""
        use_case = UpdatePropertyUseCase(
            self._database_repository,
            self._page_repository_factory.create(self._db_dir(database_name)),
        )
        new_choices_dto = None
        if new_choices is not None:
            from fern.application.dtos import ChoiceDTO

            new_choices_dto = tuple(
                ChoiceDTO(name=c.name, category=c.category, color=c.color)
                for c in new_choices
            )
        try:
            return use_case.execute(
                UpdatePropertyInputDTO(
                    database_name=database_name,
                    property_id=property_id,
                    new_name=new_name,
                    new_type_key=new_type,
                    new_choices=new_choices_dto,
                )
            )
        except AppPropertyNotFoundError as error:
            raise PropertyNotFoundError(
                property_id=property_id,
                database_name=database_name,
                vault_path=self._vault_path,
                message=str(error),
            ) from error

    def update_property_order(
        self,
        database_name: str,
        property_order: tuple[str, ...],
    ) -> None:
        """Save the display order of properties for the database."""
        use_case = UpdatePropertyOrderUseCase(self._database_repository)
        return use_case.execute(
            UpdatePropertyOrderUseCase.Input(
                database_name=database_name,
                property_order=property_order,
            )
        )

    def update_page_property(
        self,
        database_name: str,
        page_id: int,
        property_id: str,
        value: bool | str,
    ) -> None:
        """Update one property value on a page and persist. Raises PageNotFoundError or PropertyNotFoundOnPageError."""
        page_repo = self._page_repository_factory.create(self._db_dir(database_name))
        use_case = UpdatePagePropertyUseCase(page_repo)
        try:
            return use_case.execute(
                UpdatePagePropertyUseCase.Input(
                    page_id=page_id,
                    property_id=property_id,
                    value=value,
                )
            )
        except AppPageNotFoundError as error:
            raise PageNotFoundError(
                page_id=page_id,
                database_name=database_name,
                vault_path=self._vault_path,
                message=str(error),
            ) from error
        except AppPropertyNotFoundOnPageError as error:
            raise PropertyNotFoundOnPageError(
                page_id=page_id,
                property_id=property_id,
                vault_path=self._vault_path,
                message=str(error),
            ) from error

    def is_database_folder(self, path: Path) -> bool:
        """Return True if the folder contains a database marker file."""
        return is_database_folder(path)

    @property
    def database_marker_name(self) -> str:
        """The filename used as a database marker (e.g. 'database.json')."""
        from fern.interface_adapters.repositories.vault_database_repository import (
            DATABASE_MARKER,
        )

        return DATABASE_MARKER

    def _db_dir(self, database_name: str) -> Path:
        """Resolve a database_name (relative path) to its absolute folder."""
        return self._vault_path / database_name

    def _ui_to_property_value_dtos(
        self, ui_properties: list | None
    ) -> list[PropertyValueDTO] | None:
        """Convert UI property DTOs to PropertyValueDTOs for the use case.

        Supports two UI property DTO patterns:
        - New pattern: DTO has callable type_key() method
        - Legacy pattern: DTO has type attribute (string or object with key() method)
        """
        if ui_properties is None:
            return None
        property_dtos = []
        for ui_prop in ui_properties:
            prop_id = getattr(ui_prop, "id", "")
            if prop_id in ("id", "title"):
                continue
            # Extract type (support both patterns)
            if hasattr(ui_prop, "type_key") and callable(ui_prop.type_key):
                type_key_raw = ui_prop.type_key()
            else:
                type_raw = getattr(ui_prop, "type", None)
                if type_raw is None:
                    raise ValueError(f"Property {prop_id!r} has no type")
                type_key_raw = type_raw.key() if hasattr(type_raw, "key") else type_raw
            type_key = str(type_key_raw)
            property_dtos.append(
                PropertyValueDTO(
                    property_id=prop_id,
                    name=getattr(ui_prop, "name", prop_id),
                    type_key=type_key,
                    value=getattr(ui_prop, "value", None),
                )
            )
        return property_dtos

    @staticmethod
    def _build_property_dto(
        property_id: str,
        name: str,
        property_type: str,
        choices: list | None,
    ) -> PropertyInputDTO:
        """Build the appropriate property DTO based on type."""
        if property_type == "boolean":
            return BooleanPropertyInputDTO(property_id=property_id, name=name)
        elif property_type == "string":
            return StringPropertyInputDTO(property_id=property_id, name=name)
        elif property_type == "status":
            if choices is None:
                raise ValueError("status property requires choices")
            choice_dtos = [
                ChoiceDTO(name=c["name"], category=c["category"], color=c["color"])
                for c in choices
            ]
            return StatusPropertyInputDTO(
                property_id=property_id, name=name, choices=tuple(choice_dtos)
            )
        else:
            raise ValueError(f"Unknown property type: {property_type}")
