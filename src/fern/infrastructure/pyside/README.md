# PySide6 UI layer

This folder contains the Qt/PySide6 UI for Fern.

For full documentation, run `mkdocs serve` from the repo root and see the **PySide UI** section.

## Layout

- **`views/`** — Screen-level views
  - `base.py` — `FernView`: base class with toolbar (back, options), content area
  - `main_window.py` — Top-level window: welcome page and vault view stack
  - `welcome_page.py` — Welcome screen: recent vaults, Open/Create vault
  - `vault_view.py` — File-tree sidebar + content stack orchestrator
  - `database_view.py` — Database list (cards or table)
  - `pages_view.py` — Pages table with schema-driven columns
  - `editor_view.py` — Page editor: title + properties + markdown content
  - `database_window.py` — Standalone single-database window
  - `databases_overview_window.py` — All-databases overview window
  - `database_view_coordinator.py` — Shared page/property CRUD logic
  - `database_page_manager.py` — Page operations manager
  - `property_manager.py` — Property CRUD manager
  - `root_page_manager.py` — Root `.md` file manager

- **`components/`** — Reusable widgets, organized into sub-packages:
  - `dialogs/` — Confirmation, error, and property edit dialogs
  - `properties/` — PropertyField, PropertyCard, PropertyCardsWidget, settings
  - `table/` — Table view, model, and cell delegates
  - `card.py` — Generic clickable card widget
  - `command_palette.py` — Cmd+P command palette
  - `markdown_highlighter.py` — Syntax highlighter for markdown
  - `toast.py` — Toast notifications

- **`styles/`** — QSS files loaded by `theme.load_global_stylesheet()`

- **`icons/`** — SVG assets

- **`actions.py`** — Central action registry for menus and context menus

- **`theme.py`** — Stylesheet loading

- **`recent_vaults.py`** — Recent vault persistence

Public API: `from fern.infrastructure.pyside import MainWindow`
