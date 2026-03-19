# Controller Refactoring Plan

*Created: 2025-10-20*
*Status: Proposed*

## Vision

Make the controller a thin orchestration layer that:
- Receives **instances** of repositories and use cases (not callables)
- Converts UI data to DTOs
- Executes use cases
- Returns output data
- Has no business logic
- Is simple to test and understand

## Current Problems

1. **ControllerFactory** is ~300 lines with deeply nested closures
2. Property conversion logic duplicated in multiple places
3. Imports inside functions (bad for type hints and testing)
4. Controller receives callables instead of proper dependencies
5. No clear separation between orchestration and business logic

## Proposed Architecture

### 1. Repository Interfaces (Domain)

Already exist:
- `VaultRepository` (port)
- `DatabaseRepository` (port)
- `PageRepository` (port)

Add:
- `RecentVaultsRepository` (port) - for persisting/loading recent vault list

### 2. Recent Vaults as a Proper Entity

**Domain Entity**: `RecentVaults`
- `paths: list[Path]` (most recent first)
- `max_size: int = 10`

**Repository Interface**: `RecentVaultsRepository`
```python
class RecentVaultsRepository(ABC):
    @abstractmethod
    def get(self) -> list[Path]: ...
    @abstractmethod
    def add(self, path: Path) -> None: ...
    @abstractmethod
    def remove(self, path: Path) -> None: ...
```

**Concrete Implementation**: `JsonRecentVaultsRepository`
- Stores in `~/.fern/recent_vaults.json`
- Implements the three methods

**Use Case**: `ManageRecentVaultsUseCase`
```python
class ManageRecentVaultsUseCase:
    def __init__(self, repository: RecentVaultsRepository): ...

    def get_recent(self) -> list[Path]: ...
    def add_vault(self, path: Path) -> None: ...
    def remove_vault(self, path: Path) -> None: ...
```

### 3. AppController (Infrastructure)

**Constructor** - receives instances (not factories, not callables):

```python
class AppController:
    def __init__(
        self,
        *,
        vault_repository: VaultRepository,          # instance, configured with vault_path
        database_repository: DatabaseRepository,    # instance, configured with vault_path
        page_repository_class: type[PageRepository], # class, to instantiate with db_path
        recent_vaults_use_case: ManageRecentVaultsUseCase,
        is_database_folder: Callable[[Path], bool],  # utility function (or make it a service)
        database_marker_name: str,                  # constant (or config entity)
    ) -> None:
        self._vault_repository = vault_repository
        self._database_repository = database_repository
        self._page_repository_class = page_repository_class
        self._recent_vaults_use_case = recent_vaults_use_case
        self._is_database_folder = is_database_folder
        self._database_marker_name = database_marker_name
```

**Methods** - simple orchestration:

```python
def open_vault(self) -> OpenVaultOutput:
    use_case = OpenVaultUseCase(self._vault_repository)
    try:
        return use_case.execute(OpenVaultUseCase.Input())
    except _AppVaultNotFoundError as error:
        raise VaultNotFoundError(str(error)) from error

def save_page(
    self,
    database_name: str,
    page_id: int,
    title: str,
    content: str,
    properties: list | None = None,
) -> None:
    domain_props = self._ui_to_domain_properties(properties)
    page_repo = self._page_repository_class(self._db_dir(database_name))
    # Either use a SavePageUseCase or direct repo call
    page_repo.update(page_id, title, content, properties=domain_props)

def _ui_to_domain_properties(self, ui_properties: list | None) -> list[Property] | None:
    """Convert UI property DTOs to domain Properties."""
    if ui_properties is None:
        return None
    domain_props = []
    for ui_prop in ui_properties:
        prop_id = getattr(ui_prop, "id", "")
        if prop_id in ("id", "title"):
            continue
        # Extract type (support both patterns)
        if hasattr(ui_prop, "type_key") and callable(ui_prop.type_key):
            type_key = ui_prop.type_key()
        else:
            type_raw = getattr(ui_prop, "type", None)
            if type_raw is None:
                raise ValueError(f"Property {prop_id!r} has no type")
            type_key = type_raw.key() if hasattr(type_raw, "key") else str(type_raw)
        property_type = PropertyType.from_key(type_key)
        domain_prop = property_type.create(
            id=prop_id,
            name=getattr(ui_prop, "name", prop_id),
            value=getattr(ui_prop, "value", None),
        )
        domain_props.append(domain_prop)
    return domain_props

def get_recent_vaults(self) -> list[Path]:
    return self._recent_vaults_use_case.get_recent()

def add_recent_vault(self, path: Path) -> None:
    self._recent_vaults_use_case.add_vault(path)

def remove_recent_vault(self, path: Path) -> None:
    self._recent_vaults_use_case.remove_vault(path)
```

### 4. ControllerFactory (Infrastructure)

**Purpose**: Single composition root that wires all dependencies.

```python
class ControllerFactory:
    def __init__(self) -> None:
        self._recent_vaults_repository = JsonRecentVaultsRepository()
        self._recent_vaults_use_case = ManageRecentVaultsUseCase(
            self._recent_vaults_repository
        )

    def create_controller(self, vault_path: Path) -> AppController:
        """Create a fully-wired controller for the given vault."""
        from fern.interface_adapters.repositories.filesystem_vault_repository import (
            FilesystemVaultRepository,
        )
        from fern.interface_adapters.repositories.vault_database_repository import (
            VaultDatabaseRepository,
        )
        from fern.interface_adapters.repositories.markdown_page_repository import (
            MarkdownPageRepository,
        )
        from fern.application.use_cases.is_database_folder import is_database_folder
        from fern.interface_adapters.repositories.vault_database_repository import DATABASE_MARKER

        vault_repo = FilesystemVaultRepository(vault_path)
        db_repo = VaultDatabaseRepository(vault_path)

        return AppController(
            vault_repository=vault_repo,
            database_repository=db_repo,
            page_repository_class=MarkdownPageRepository,
            recent_vaults_use_case=self._recent_vaults_use_case,
            is_database_folder=is_database_folder,
            database_marker_name=DATABASE_MARKER,
        )
```

### 5. Missing Use Cases

Create use cases for operations that don't have them yet:

- `SavePageUseCase` - wraps `PageRepository.update()`
- `CreateRootPageUseCase` - creates page at vault root
- `CreateDatabaseUseCase` - creates database marker
- `CreateVaultUseCase` - creates vault directory

Or, for trivial operations, the controller can call repositories directly. Consistency is key.

## Implementation Steps

1. **Create Recent Vaults Domain**
   - `RecentVaultsRepository` interface (domain/repositories/)
   - `JsonRecentVaultsRepository` implementation (infrastructure/)
   - `ManageRecentVaultsUseCase` (application/)
   - Update `ControllerFactory` to use it

2. **Extract Property Conversion**
   - Move conversion logic from `ControllerFactory` closure to `AppController._ui_to_domain_properties()`
   - Ensure it handles both `type_key()` and `type` attribute patterns

3. **Simplify Controller**
   - Remove all callable dependencies
   - Inject instances/classes as shown above
   - Remove vault_path from all methods (it's in the injected repositories)
   - Keep database_name parameter where needed

4. **Simplify ControllerFactory**
   - Remove all nested closures
   - Just wire dependencies and return `AppController`
   - Cache recent vaults use case in factory

5. **Update UI Code**
   - Change from `factory.get_controller()` to `factory.create_controller(vault_path)`
   - Update method calls (remove vault_path parameters where removed)

6. **Add Tests**
   - Test `AppController` with mock repositories/use cases
   - Test property conversion edge cases
   - Test error translation

## Benefits

- **Simple controller**: ~200 lines instead of 300+ with closures
- **Clear dependencies**: All dependencies explicit in constructor
- **Testable**: Mock repositories/use cases easily
- **Maintainable**: No nested functions, no magic
- **Consistent**: Everything follows same pattern (entity → repository → use case → controller)

## Trade-offs

- Controller is per-vault (but that's natural - a vault is a unit of work)
- Need to create `SavePageUseCase` etc. if we want full consistency
- `is_database_folder` and `DATABASE_MARKER` are still "leaky" - could be wrapped in config use case

## Open Questions

1. Should `is_database_folder` be a repository method or a separate utility?
2. Should we create use cases for trivial operations (like `create_database`) or call repos directly?
3. Should `database_marker_name` be configurable? If so, inject via config use case.

## Next Steps

1. Get approval on this design
2. Implement recent vaults refactoring first (small, self-contained)
3. Implement controller simplification
4. Update UI code
5. Add tests
6. Review and iterate