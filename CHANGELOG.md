# Changelog

All notable changes to Fern are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.3] - 2026-03-18

### Fixed

- GitHub Actions workflow: Fix `uv publish` failing with `No files found to publish` by downloading package artifacts into `dist/` and publishing `dist/*`
- GitHub Actions workflow: List downloaded artifacts before publishing to simplify debugging

## [0.6.2] - 2026-03-18

### Fixed

- GitHub Actions workflow: Fixed artifact download path for package publishing (removed nested dist directory issue)
- GitHub Actions workflow: Added required permissions for release creation and package publishing

## [0.6.1] - 2026-03-18

### Added

- GitHub Actions CI/CD workflow to replace GitLab CI/CD

## [0.6.0] - 2026-03-17

### Added

- **Color class**: New `Color` value object for hex color values used in status choices.
- **ChoiceCategory class**: New `ChoiceCategory` with name and optional color for categorizing status choices.
- **Comprehensive error tests**: New `test_errors.py` covering all application error constructors and messages.

### Changed

- **Property hierarchy unification**: Refactored property system from strategy pattern to proper class hierarchy:
  - `Property` is now an abstract base class with abstract methods: `type_key()`, `default_value()`, `validate()`, `coerce()`.
  - All concrete property types (`BooleanProperty`, `StringProperty`, `StatusProperty`, `IdProperty`, `TitleProperty`) inherit from `Property` and implement instance methods instead of class methods.
  - Removed `type` and `choices` fields from base `Property`; `choices` now only on `StatusProperty`.
  - `mandatory` flag moved to base class with appropriate defaults per subclass.
- **PropertyType enum**: Redesigned to map type keys to concrete classes via `(key, class)` tuples. Added factory method `create(**kwargs)` and `default_value_for_type()`. `from_key()` now raises `ValueError` for invalid keys instead of defaulting to `BOOLEAN`.
- **Application use cases**: Updated all use cases (`AddProperty`, `UpdateProperty`, `AddPageProperty`, `ApplyPropertyToPages`, `UpdatePageProperty`, `OpenVault`) to use new property API:
  - Direct construction of concrete types (e.g., `StatusProperty(id=..., choices=...)`) instead of generic `Property(...)`.
  - Call `property.coerce()` directly instead of via `property.type.value.coerce()`.
  - Use `property.type_key()` instead of `property.type.key()`.
- **Repositories**: Updated `VaultDatabaseRepository` and `MarkdownPageRepository` to instantiate concrete property types and use new API. Added stricter validation for missing `type` fields.
- **Controller**: `default_value_for_type()` now uses `PropertyType.default_value_for_type()`.
- **DTOs**: Simplified `PropertyInputDTO` hierarchy - base class holds `property_id` and `name`; specific DTOs inherit without redefining fields.
- **Tests**: Extensive updates across all test suites to reflect new property architecture. Added `test_property_factory.py` for factory functions. Updated all property, repository, and use case tests.

### Fixed

- **PropertyType.from_key**: Now raises clear `ValueError` for missing or unknown type keys instead of silently defaulting to boolean.
- **Repository deserialization**: Added required `type` field validation; raises `ValueError` if missing from property definition.

## [0.5.0] - 2026-03-14

### Added

- **Status property type**: New `StatusProperty` with named choices, categories, and colors. Status columns render as colored combo dropdowns in the pages table.
- **Status choices editor**: Dialog for managing status choices (name, category, color) with an inline color picker.
- **Command palette**: Cmd+P fuzzy search across all available actions.
- **Toast notifications**: Non-intrusive bottom-right toasts with countdown bar.
- **DatabaseViewCoordinator**: Shared page/property CRUD logic extracted from three host views, eliminating ~500 lines of duplication.
- **MkDocs documentation**: Architecture and PySide developer guide with Material theme, mermaid diagrams, hosted on GitLab Pages.
- **GitLab Pages CI job**: Automatically builds and deploys docs on merge to main.
- **Ruff linting in CI**: `ruff check` and `ruff format --check` run on merge requests.

### Changed

- **Unified action system**: Collapsed three identical action item dataclasses into a single `ActionItem`; added `build_options_menu()` utility to eliminate repetitive menu-building loops.
- **Merged property edit dialogs**: `BooleanPropertyEditDialog` and `StringPropertyEditDialog` replaced by a single `SimplePropertyEditDialog` parameterized by type key.
- **Components reorganized**: `components/` split into sub-packages — `dialogs/`, `properties/`, `table/` — for better discoverability.
- **Clean layer boundaries**: PySide UI no longer imports from `fern.application` or `fern.domain`. Output types, errors, and helpers are re-exported through `fern.infrastructure.controller`.
- **Integrated scrollbars and toolbar buttons**: Minimal, transparent styling for scrollbars; borderless toolbar buttons with subtle hover highlights.
- **Table interaction**: Status dropdowns open immediately on double-click; checkboxes toggle only on double-click; single click highlights the row.
- **Error handling**: Application errors include detailed messages; generic `show_error()` dialog used consistently across all views.

### Fixed

- **Error display**: All views now use `show_error()` for consistent error presentation instead of ad-hoc alert dialogs.
- **Editor property visibility**: "Add property" option hidden in editor when not in a database context.

## [0.4.0] - 2026-03-12

### Added

- **Save page with properties**: `save_page` (controller and factory) now accepts an optional `properties` argument; editor save and auto-save persist all page properties to markdown frontmatter so they are not lost on reload.
- **Regression tests**: `tests_infrastructure/test_save_page_properties.py` — verifies that saving a page writes properties to disk and that the full add-property flow updates every page's frontmatter.

### Changed

- **Add property is synchronous**: Adding a property to a database schema now immediately applies it to every page's markdown file (frontmatter). The previous async QThread-based apply was removed; the synchronous apply is fast and reliable.
- **Controller `add_property`**: No longer takes an `on_pages_updated` callback; callers refresh the UI after the call returns.
- **Editor "Add property"**: Only shown when editing a database page (`in_database=True`); hidden for root-level markdown pages.

### Fixed

- **Add property not updating files**: New schema properties are now written to each page's frontmatter so the property appears in the UI and persists on disk.
- **Add property not updating UI**: Views refresh and re-set the editor page after add property so the new property appears in the table and in the editor properties pane.
- **Save overwriting properties**: Editor save (and `save_page`) now pass the current page's properties to the repository so frontmatter is preserved instead of being dropped.

## [0.3.0] - 2026-03-12

### Changed

- **Renamed PyPI package** from `fern` to `fern-app` (imports remain `fern`).
- **CI/CD**: Version and changelog check is now mandatory on merge requests (no longer allow_failure).

## [0.2.0] - 2026-03-12

### Added

- **Mandatory properties**: `id` and `title` are now first-class properties in the schema with dedicated `IdProperty` and `TitleProperty` types. They appear as sortable columns but cannot be hidden, removed, or edited.
- **Column drag-and-drop**: Drag column headers to reorder with a green drop indicator showing the target position.
- **Move left / Move right**: Context menu actions on column headers to shift columns one position.
- **Save column order**: Persist display order to `schema.json` via the options menu.
- **`UpdatePropertyOrderUseCase`**: New use case for persisting property display order.
- **Unit tests**: Comprehensive test suite (149 tests, 99% coverage on domain/application/interface_adapters).

### Changed

- **CI/CD**: Use `uv publish` instead of twine for publishing to PyPI and GitLab Package Registry. Fix GitLab create-release 422 by passing `ref` to the Releases API.
- **Removed `ManifestRepository`**: All schema persistence now goes through `DatabaseRepository` with `get_schema()` and `save_schema()` methods. `JsonManifestRepository` has been deleted.
- **Renamed `manifest.json` to `schema.json`**: Database schema files are now stored as `schema.json`.
- **`PropertyType` enum**: Extended with `ID` and `TITLE` members; added `user_creatable()` to filter mandatory types from UI selection.
- **`Property` entity**: Added `mandatory: bool` flag.
- **Use cases** (`AddProperty`, `RemoveProperty`, `UpdateProperty`, `UpdatePropertyOrder`): Now accept `DatabaseRepository` instead of `ManifestRepository`; inputs include `database_name`.
- **`TableModel`**: Supports read-only columns via `set_readonly_columns()` instead of hardcoded column indices.
- **`PagesView`**: Fully schema-driven — no hardcoded id/title column indices. Custom header drag-and-drop replaces Qt's built-in section moving.

### Fixed

- Column move left/right now operates on visible column order instead of the full property order (which included hidden columns).
- Column drag-and-drop no longer causes stale header mappings after model resets.
- Save column order no longer blocked when only id and title columns exist.
- Removed dead code (redundant guard) in `UpdatePagePropertyUseCase`.

---

## [0.1.0] - 2026-03-12

### Added

- **Vaults and databases**: Open a folder as a vault; list databases with card or table view.
- **Pages**: List pages per database (ID, Title); create, edit, and delete pages with markdown content.
- **Properties**: Schema-defined properties on pages (stored in frontmatter; schema in `schema.json`).
  - **Boolean** property type (checkbox in table and editor).
  - **String** property type (text field in table and editor).
- **Property UI**:
  - Add property from the pages view options menu (name + type in one settings widget).
  - Right-click a property column header in the pages table to **Edit property** (name/type) or **Remove property**.
  - Property cards in the page editor: stacked rows with label and modifier, optional border on the container.
- **Reusable components**: `PropertyField`, `PropertyCard`, `PropertyCardsWidget`, `PropertySettingsWidget`, `CheckboxDelegate`, shared `utils` (icons, `property_type_key`, `set_expanding`).
- **Styling**: QSS for welcome, vault, editor, table, and cards; dark theme for editor and properties.

### Fixed

- Property value changes from the editor or table persist correctly.
- Edit/Add property dialog: capture name and type before dialog is destroyed to avoid deleted widget access.
- Removed invalid `font-family: inherit` in editor QSS to avoid Qt font warning.

[Unreleased]: https://gitlab.com/arnaudjalbert/fern/-/compare/v0.6.2...HEAD
[0.6.1]: https://gitlab.com/arnaudjalbert/fern/-/compare/v0.6.0...0.6.1
[0.6.0]: https://gitlab.com/arnaudjalbert/fern/-/compare/v0.5.0...v0.6.0
[0.5.0]: https://gitlab.com/arnaudjalbert/fern/-/compare/v0.4.0...v0.5.0
[0.4.0]: https://gitlab.com/arnaudjalbert/fern/-/compare/v0.3.0...v0.4.0
[0.3.0]: https://gitlab.com/arnaudjalbert/fern/-/tags/v0.3.0
[0.2.0]: https://gitlab.com/arnaudjalbert/fern/-/tags/v0.2.0
[0.1.0]: https://gitlab.com/arnaudjalbert/fern/-/tags/v0.1.0
