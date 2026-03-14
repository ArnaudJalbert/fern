# .cursor — version-controlled AI guidelines

This directory holds Cursor rules and documentation so that **all contributors and the AI agent** follow the same repo conventions. Everything here is committed to the repo.

## Contents

- **`rules/`** — Cursor rule files (`.mdc`). Rules with `alwaysApply: true` are loaded every session; others apply when matching files are open.
- **`README.md`** — This file.

## Design principles (summary)

The rules encode Fern’s stance:

1. **Unix philosophy** — Do one thing well; prefer text and composable tools; small, focused components.
2. **Open source** — Code and docs are open; no proprietary lock-in; contribution-friendly.
3. **Open files** — Data lives as human-editable files (markdown + frontmatter) in the user’s vault; no opaque database format.
4. **Clean architecture** — Hexagonal/ports-and-adapters: domain → application → interface_adapters → infrastructure; dependencies point inward.

See `rules/repo-guidelines.mdc` for the concrete rules the AI is instructed to follow.
