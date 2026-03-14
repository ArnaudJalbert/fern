# Fern

**Offline-first desktop app for vaults, databases, and pages** — an open-source alternative to Notion/AppFlowy. Native PySide6 UI; data lives as markdown + frontmatter in local folders.

- **Vaults** → folder with a `Databases/` subfolder; each database is a subfolder of markdown pages.
- **Pages** → one `.md` file per page (YAML frontmatter for id, properties; body = content).
- **Properties** → schema in `schema.json` per database; boolean/string (and more) with table + editor UI.

## Install

```bash
pip install fern
# or
uv add fern
```

## Run

```bash
fern
```

Open a folder as a vault; create and edit pages and properties from the UI.

---

## Technical

| Item | Detail |
|------|--------|
| **Python** | 3.13+ |
| **GUI** | PySide6 |
| **Data** | Markdown + YAML frontmatter, `schema.json` per database |
| **Build** | Hatchling (pyproject.toml) |
| **Dev / test** | uv, pytest, pytest-cov |

**Architecture (clean / hexagonal):**

- **Domain** — entities (Vault, Database, Page, Property, PropertyType), repository ports (abstract).
- **Application** — use cases only (open vault, list DBs/pages, CRUD page, add/remove/update property, update property order, update page property).
- **Interface adapters** — repository implementations: filesystem vault, vault DB (markdown + schema.json), in-memory/markdown page repos.
- **Infrastructure** — PySide6 views and components, controller, factory wiring adapters into use cases.

**Layout:** `src/fern/` → `application/`, `domain/`, `interface_adapters/`, `infrastructure/`.

**Development:**

```bash
uv sync --all-groups
uv run pytest tests/unit_tests/ --cov
uv build
```

Unit tests target application, domain, and interface_adapters (100% coverage enforced). Coverage scope: `.coveragerc` → `fern.application`, `fern.domain`, `fern.interface_adapters`.

**CI/CD (GitLab):**

- **Merge requests:** version must differ from target branch; `CHANGELOG.md` must have `## [x.y.z]` for that version; unit tests (uv + pytest + cov); package build.
- **Push to default branch:** build → publish to **GitLab Package Registry** and **PyPI** (twine); create **release** and **tag** `v<x.y.z>` via Releases API; build and deploy **documentation** to **GitLab Pages**. PyPI requires CI variable `PYPI_API_TOKEN`.

**Documentation:** Architecture and developer guide built with [MkDocs](https://www.mkdocs.org/) + [Material](https://squidfunk.github.io/mkdocs-material/), hosted on GitLab Pages. Run locally with `uv run mkdocs serve`.

**Versioning:** Semantic Versioning; changelog format [Keep a Changelog](https://keepachangelog.com/). Bump `version` in `pyproject.toml` and add a changelog section for each release.
