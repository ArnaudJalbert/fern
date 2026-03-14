"""Factory that builds the app controller with default dependencies (PySide UI, filesystem repos)."""

from pathlib import Path


from fern.infrastructure.controller import (
    AppController,
    CreateRootPageOutput,
    RecentVaultsPort,
)


class ControllerFactory:
    """Builds and caches a single AppController per factory instance (no globals)."""

    def __init__(self) -> None:
        self._controller: AppController | None = None

    def get_controller(self) -> AppController:
        """Return the controller, creating it once with default implementations."""
        if self._controller is None:
            self._controller = self._create_controller()
        return self._controller

    def _create_controller(self) -> AppController:
        """Wire and return a new AppController with default dependencies."""
        from fern.application.use_cases.open_vault import OpenVaultUseCase
        from fern.interface_adapters.repositories.filesystem_vault_repository import (
            FilesystemVaultRepository,
        )
        from fern.interface_adapters.repositories.vault_database_repository import (
            DATABASE_MARKER,
        )

        from fern.infrastructure.pyside.recent_vaults import (
            add_recent_vault,
            load_recent_vaults,
            remove_recent_vault,
        )

        class RecentVaultsAdapter(RecentVaultsPort):
            def get_list(self) -> list[Path]:
                return load_recent_vaults()

            def add(self, path: Path) -> None:
                add_recent_vault(path)

            def remove(self, path: Path) -> None:
                remove_recent_vault(path)

        def open_vault(path: Path):
            repo = FilesystemVaultRepository(path)
            use_case = OpenVaultUseCase(repo)
            return use_case.execute(OpenVaultUseCase.Input())

        def create_vault(parent_dir: Path, name: str) -> Path | None:
            path = parent_dir / name
            if path.exists():
                return None
            path.mkdir(parents=True)
            return path

        def _db_dir(vault_path: Path, database_name: str) -> Path:
            """Resolve a database_name (relative path) to its absolute folder."""
            return Path(vault_path) / database_name

        def save_page(
            vault_path: Path,
            database_name: str,
            page_id: int,
            title: str,
            content: str,
            properties: list | None = None,
        ) -> None:
            from fern.domain.entities.properties import Property, PropertyType
            from fern.interface_adapters.repositories.markdown_page_repository import (
                MarkdownPageRepository,
            )

            repo = MarkdownPageRepository(_db_dir(vault_path, database_name))
            domain_props = None
            if properties is not None:
                domain_props = []
                for page_property in properties:
                    property_id = getattr(page_property, "id", "")
                    if property_id in ("id", "title"):
                        continue
                    property_type = getattr(page_property, "type", "string")
                    if isinstance(property_type, str):
                        property_type = PropertyType.from_key(property_type)
                    domain_props.append(
                        Property(
                            id=property_id,
                            name=getattr(page_property, "name", property_id),
                            type=property_type,
                            value=getattr(page_property, "value", None),
                        )
                    )
            repo.update(page_id, title, content, properties=domain_props)

        def create_page(
            vault_path: Path,
            database_name: str,
            title: str = "Untitled",
            content: str = "",
        ):
            from fern.application.use_cases.create_page import CreatePageUseCase
            from fern.interface_adapters.repositories.markdown_page_repository import (
                MarkdownPageRepository,
            )

            repo = MarkdownPageRepository(_db_dir(vault_path, database_name))
            use_case = CreatePageUseCase(repo)
            return use_case.execute(
                CreatePageUseCase.Input(title=title, content=content)
            )

        def create_root_page(
            vault_path: Path, title: str = "Untitled"
        ) -> CreateRootPageOutput:
            from fern.application.use_cases.create_page import CreatePageUseCase
            from fern.interface_adapters.repositories.markdown_page_repository import (
                MarkdownPageRepository,
            )

            repo = MarkdownPageRepository(Path(vault_path))
            use_case = CreatePageUseCase(repo)
            out = use_case.execute(CreatePageUseCase.Input(title=title, content=""))
            path = Path(vault_path) / f"{out.title}.md"
            return CreateRootPageOutput(
                path=path,
                page_id=out.page_id,
                title=out.title,
                content=out.content,
            )

        def create_database(vault_path: Path, folder_rel: str) -> bool:
            """Create a database.json marker inside the given folder (relative to vault).

            Returns True if created, False if it already exists.
            """
            import json

            target = Path(vault_path) / folder_rel
            marker = target / DATABASE_MARKER
            if marker.exists():
                return False
            target.mkdir(parents=True, exist_ok=True)
            data = {"properties": [], "propertyOrder": []}
            marker.write_text(json.dumps(data, indent=2), encoding="utf-8")
            return True

        def delete_page(vault_path: Path, database_name: str, page_id: int):
            from fern.application.use_cases.delete_page import DeletePageUseCase
            from fern.interface_adapters.repositories.markdown_page_repository import (
                MarkdownPageRepository,
            )

            repo = MarkdownPageRepository(_db_dir(vault_path, database_name))
            use_case = DeletePageUseCase(repo)
            return use_case.execute(DeletePageUseCase.Input(page_id=page_id))

        def add_property(
            vault_path: Path,
            database_name: str,
            property_id: str,
            name: str,
            property_type: str,
            choices: list | None = None,
        ):
            from fern.application.dtos import (
                AddPropertyInputDTO,
                ApplyPropertyToPagesInputDTO,
                BooleanPropertyInputDTO,
                ChoiceDTO,
                StatusPropertyInputDTO,
                StringPropertyInputDTO,
            )
            from fern.application.use_cases.add_property import AddPropertyUseCase
            from fern.application.use_cases.apply_property_to_pages import (
                ApplyPropertyToPagesUseCase,
            )
            from fern.interface_adapters.repositories.markdown_page_repository import (
                MarkdownPageRepository,
            )
            from fern.interface_adapters.repositories.vault_database_repository import (
                VaultDatabaseRepository,
            )

            def _property_input_dto(
                prop_id: str,
                prop_name: str,
                prop_type: str,
                prop_choices: list | None,
            ):
                if prop_type == "status" and prop_choices:
                    return StatusPropertyInputDTO(
                        property_id=prop_id,
                        name=prop_name,
                        choices=tuple(
                            ChoiceDTO(
                                name=choice.name,
                                category=choice.category,
                                color=choice.color,
                            )
                            for choice in prop_choices
                        ),
                    )
                if prop_type == "string":
                    return StringPropertyInputDTO(
                        property_id=prop_id,
                        name=prop_name,
                    )
                return BooleanPropertyInputDTO(
                    property_id=prop_id,
                    name=prop_name,
                )

            property_dto = _property_input_dto(
                prop_id=property_id,
                prop_name=name,
                prop_type=property_type,
                prop_choices=choices,
            )
            db_repo = VaultDatabaseRepository(vault_path)
            use_case = AddPropertyUseCase(db_repo)
            use_case.execute(
                AddPropertyInputDTO(
                    database_name=database_name,
                    property=property_dto,
                )
            )
            page_repo = MarkdownPageRepository(_db_dir(vault_path, database_name))
            apply_uc = ApplyPropertyToPagesUseCase(page_repo)
            apply_uc.execute(
                ApplyPropertyToPagesInputDTO(
                    property_id=property_id,
                    name=name,
                    type_key=property_type,
                )
            )

        def add_page_property(
            vault_path: Path,
            database_name: str,
            page_id: int,
            property_id: str,
            name: str,
            property_type: str,
        ):
            from fern.application.dtos import AddPagePropertyInputDTO
            from fern.application.use_cases.add_page_property import (
                AddPagePropertyUseCase,
            )
            from fern.interface_adapters.repositories.markdown_page_repository import (
                MarkdownPageRepository,
            )

            page_repo = MarkdownPageRepository(_db_dir(vault_path, database_name))
            use_case = AddPagePropertyUseCase(page_repo)
            return use_case.execute(
                AddPagePropertyInputDTO(
                    page_id=page_id,
                    property_id=property_id,
                    name=name,
                    type_key=property_type,
                )
            )

        def remove_property(vault_path: Path, database_name: str, property_id: str):
            from fern.application.use_cases.remove_property import RemovePropertyUseCase
            from fern.interface_adapters.repositories.markdown_page_repository import (
                MarkdownPageRepository,
            )
            from fern.interface_adapters.repositories.vault_database_repository import (
                VaultDatabaseRepository,
            )

            db_repo = VaultDatabaseRepository(vault_path)
            page_repo = MarkdownPageRepository(_db_dir(vault_path, database_name))
            use_case = RemovePropertyUseCase(db_repo, page_repo)
            return use_case.execute(
                RemovePropertyUseCase.Input(
                    database_name=database_name,
                    property_id=property_id,
                )
            )

        def update_property(
            vault_path: Path,
            database_name: str,
            property_id: str,
            new_name: str | None = None,
            new_type: str | None = None,
            new_choices: list | None = None,
        ):
            from fern.application.dtos import ChoiceDTO, UpdatePropertyInputDTO
            from fern.application.use_cases.update_property import UpdatePropertyUseCase
            from fern.interface_adapters.repositories.markdown_page_repository import (
                MarkdownPageRepository,
            )
            from fern.interface_adapters.repositories.vault_database_repository import (
                VaultDatabaseRepository,
            )

            db_repo = VaultDatabaseRepository(vault_path)
            page_repo = MarkdownPageRepository(_db_dir(vault_path, database_name))
            use_case = UpdatePropertyUseCase(db_repo, page_repo)
            new_choices_dto = None
            if new_choices is not None:
                new_choices_dto = tuple(
                    ChoiceDTO(name=c.name, category=c.category, color=c.color)
                    for c in new_choices
                )
            return use_case.execute(
                UpdatePropertyInputDTO(
                    database_name=database_name,
                    property_id=property_id,
                    new_name=new_name,
                    new_type_key=new_type,
                    new_choices=new_choices_dto,
                )
            )

        def update_property_order(
            vault_path: Path,
            database_name: str,
            property_order: tuple[str, ...],
        ):
            from fern.application.use_cases.update_property_order import (
                UpdatePropertyOrderUseCase,
            )
            from fern.interface_adapters.repositories.vault_database_repository import (
                VaultDatabaseRepository,
            )

            db_repo = VaultDatabaseRepository(Path(vault_path).resolve())
            use_case = UpdatePropertyOrderUseCase(db_repo)
            return use_case.execute(
                UpdatePropertyOrderUseCase.Input(
                    database_name=database_name,
                    property_order=property_order,
                )
            )

        def update_page_property(
            vault_path: Path,
            database_name: str,
            page_id: int,
            property_id: str,
            value: bool | str,
        ):
            from fern.application.use_cases.update_page_property import (
                UpdatePagePropertyUseCase,
            )
            from fern.interface_adapters.repositories.markdown_page_repository import (
                MarkdownPageRepository,
            )

            page_repo = MarkdownPageRepository(_db_dir(vault_path, database_name))
            use_case = UpdatePagePropertyUseCase(page_repo)
            return use_case.execute(
                UpdatePagePropertyUseCase.Input(
                    page_id=page_id,
                    property_id=property_id,
                    value=value,
                )
            )

        from fern.interface_adapters.repositories.vault_database_repository import (
            is_database_folder,
        )

        return AppController(
            recent_vaults=RecentVaultsAdapter(),
            open_vault=open_vault,
            create_vault=create_vault,
            save_page=save_page,
            create_page=create_page,
            create_root_page=create_root_page,
            create_database=create_database,
            is_database_folder=is_database_folder,
            database_marker_name=DATABASE_MARKER,
            delete_page=delete_page,
            add_property=add_property,
            add_page_property=add_page_property,
            remove_property=remove_property,
            update_property=update_property,
            update_property_order=update_property_order,
            update_page_property=update_page_property,
        )
