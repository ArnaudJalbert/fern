# Fern Developer Documentation

Fern is an **open files, open source** alternative to Notion and AppFlowy for tasks and page management.

All user data lives as **markdown files with YAML frontmatter** in a folder the user controls — no databases, no proprietary formats, no lock-in.

## Quick Start

```bash
uv sync
uv run fern
```

## Key Principles

- **Data is files.** Every page is a `.md` file. Every database schema is a `database.json`.
- **Clean architecture.** Domain → Application → Interface Adapters → Infrastructure.
- **Composability.** Small, focused modules that can be combined or replaced.

## Documentation Sections

| Section | What it covers |
|---------|---------------|
| [Architecture Overview](architecture/overview.md) | High-level project layout and layer responsibilities |
| [Clean Architecture](architecture/clean-architecture.md) | Layer rules, dependency flow, and where to put new code |
| [PySide UI Overview](pyside/overview.md) | How the PySide6 UI layer is organized |
| [Views](pyside/views.md) | Screen-level views and the coordinator pattern |
| [Components](pyside/components.md) | Reusable widgets organized by sub-package |
| [Patterns](pyside/patterns.md) | Recurring patterns: managers, signal wiring, options menus |
| [Actions & Menus](pyside/actions.md) | The action registry and menu-building system |
