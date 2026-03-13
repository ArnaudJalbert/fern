"""Factory that builds the app controller with default dependencies (PySide UI, filesystem repos)."""

from pathlib import Path

from fern.infrastructure.controller import AppController, RecentVaultsPort


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
        from fern.interface_adapters.repositories import DATABASES_DIRNAME
        from fern.interface_adapters.repositories.filesystem_vault_repository import (
            FilesystemVaultRepository,
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
            (path / DATABASES_DIRNAME).mkdir(parents=True)
            return path

        def save_page(
            vault_path: Path, database_name: str, page_id: int, title: str, content: str
        ) -> None:
            from fern.interface_adapters.repositories.markdown_page_repository import (
                MarkdownPageRepository,
            )

            pages_dir = Path(vault_path) / DATABASES_DIRNAME / database_name
            repo = MarkdownPageRepository(pages_dir)
            repo.update(page_id, title, content)

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

            pages_dir = Path(vault_path) / DATABASES_DIRNAME / database_name
            repo = MarkdownPageRepository(pages_dir)
            use_case = CreatePageUseCase(repo)
            return use_case.execute(
                CreatePageUseCase.Input(title=title, content=content)
            )

        def delete_page(vault_path: Path, database_name: str, page_id: int):
            from fern.application.use_cases.delete_page import DeletePageUseCase
            from fern.interface_adapters.repositories.markdown_page_repository import (
                MarkdownPageRepository,
            )

            pages_dir = Path(vault_path) / DATABASES_DIRNAME / database_name
            repo = MarkdownPageRepository(pages_dir)
            use_case = DeletePageUseCase(repo)
            return use_case.execute(DeletePageUseCase.Input(page_id=page_id))

        def add_property(
            vault_path: Path,
            database_name: str,
            property_id: str,
            name: str,
            property_type: str,
        ):
            from fern.application.use_cases.add_property import AddPropertyUseCase
            from fern.domain.entities import PropertyType
            from fern.interface_adapters.repositories.markdown_page_repository import (
                MarkdownPageRepository,
            )
            from fern.interface_adapters.repositories.vault_database_repository import (
                VaultDatabaseRepository,
            )

            db_repo = VaultDatabaseRepository(vault_path)
            page_repo = MarkdownPageRepository(
                Path(vault_path) / DATABASES_DIRNAME / database_name
            )
            use_case = AddPropertyUseCase(db_repo, page_repo)
            ptype = PropertyType.from_key(property_type)
            return use_case.execute(
                AddPropertyUseCase.Input(
                    database_name=database_name,
                    property_id=property_id,
                    name=name,
                    type=ptype,
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
            page_repo = MarkdownPageRepository(
                Path(vault_path) / DATABASES_DIRNAME / database_name
            )
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
        ):
            from fern.application.use_cases.update_property import UpdatePropertyUseCase
            from fern.interface_adapters.repositories.markdown_page_repository import (
                MarkdownPageRepository,
            )
            from fern.interface_adapters.repositories.vault_database_repository import (
                VaultDatabaseRepository,
            )

            db_repo = VaultDatabaseRepository(vault_path)
            page_repo = MarkdownPageRepository(
                Path(vault_path) / DATABASES_DIRNAME / database_name
            )
            use_case = UpdatePropertyUseCase(db_repo, page_repo)
            return use_case.execute(
                UpdatePropertyUseCase.Input(
                    database_name=database_name,
                    property_id=property_id,
                    new_name=new_name,
                    new_type=new_type,
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

            db_dir = Path(vault_path) / DATABASES_DIRNAME / database_name
            page_repo = MarkdownPageRepository(db_dir)
            use_case = UpdatePagePropertyUseCase(page_repo)
            return use_case.execute(
                UpdatePagePropertyUseCase.Input(
                    page_id=page_id,
                    property_id=property_id,
                    value=value,
                )
            )

        return AppController(
            recent_vaults=RecentVaultsAdapter(),
            open_vault=open_vault,
            create_vault=create_vault,
            save_page=save_page,
            create_page=create_page,
            delete_page=delete_page,
            add_property=add_property,
            remove_property=remove_property,
            update_property=update_property,
            update_property_order=update_property_order,
            update_page_property=update_page_property,
        )
