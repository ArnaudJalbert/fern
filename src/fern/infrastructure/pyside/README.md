# PySide6 UI layer

This folder contains the Qt/PySide6 UI for Fern. Layout:

- **`views/`** — Screen-level views
  - `base.py` — `FernView`: base class with toolbar (back, options), content area, and `currentView` for styling
  - `main_window.py` — Top-level window: welcome page and vault view stack
  - `welcome_page.py` — Welcome screen: recent vaults, Open/Create vault
  - `vault_view.py` — Vault open: sidebar (Databases) + stack of database / pages / editor views
  - `database_view.py` — List of databases (cards or table); emits `database_selected`
  - `pages_view.py` — Table of pages (ID, Title); New page, context menu (Delete)
  - `editor_view.py` — Page editor: title + markdown content with syntax highlighting and debounced save

- **`components/`** — Reusable widgets
  - `card.py` — Card widget (title, subtitle, optional icon)
  - `table.py` — Table with `TableModel`; sync `set_data()` or async `load_async()`
  - `table_model.py` — `QAbstractTableModel` for dict-based rows
  - `markdown_highlighter.py` — `QSyntaxHighlighter` for markdown in `QPlainTextEdit`

- **`styles/`** — QSS files (base, welcome, card, table, vault, editor). Loaded by `theme.load_global_stylesheet()`.

- **`icons/`** — SVG assets (e.g. options, databases).

- **`theme.py`** — Loads and applies the global stylesheet.

- **`recent_vaults.py`** — Persists recent vault paths to `~/.fern/recent_vaults.json`.

Public API: use `from fern.infrastructure.pyside import MainWindow` and `from fern.infrastructure.pyside.theme import load_global_stylesheet`.
