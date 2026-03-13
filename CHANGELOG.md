# Changelog

All notable changes to Fern are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Mandatory properties**: `id` and `title` are now first-class properties in the schema with dedicated `IdProperty` and `TitleProperty` types. They appear as sortable columns but cannot be hidden, removed, or edited.
- **Column drag-and-drop**: Drag column headers to reorder with a green drop indicator showing the target position.
- **Move left / Move right**: Context menu actions on column headers to shift columns one position.
- **Save column order**: Persist display order to `schema.json` via the options menu.
- **`UpdatePropertyOrderUseCase`**: New use case for persisting property display order.
- **Unit tests**: Comprehensive test suite (149 tests, 99% coverage on domain/application/interface_adapters).

### Changed

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

[Unreleased]: https://github.com/your-org/fern/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/your-org/fern/releases/tag/v0.1.0
