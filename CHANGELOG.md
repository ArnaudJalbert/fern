# Changelog

All notable changes to Fern are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- (Nothing yet.)

### Changed

- (Nothing yet.)

### Fixed

- (Nothing yet.)

---

## [0.1.0] - 2026-03-12

### Added

- **Vaults and databases**: Open a folder as a vault; list databases with card or table view.
- **Pages**: List pages per database (ID, Title); create, edit, and delete pages with markdown content.
- **Properties**: Schema-defined properties on pages (stored in frontmatter; schema in `manifest.json`).
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
