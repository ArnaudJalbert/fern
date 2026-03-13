"""Manages root-level .md pages: load, save, create, delete.

All file I/O for vault-root markdown pages lives here so VaultView stays
focused on layout and navigation. Root pages support optional frontmatter
properties (same shape as database pages) stored in the .md file.
"""

from __future__ import annotations

import os
from pathlib import Path

import frontmatter

from fern.domain.entities import PropertyType
from fern.infrastructure.controller import AppController

from .page_data import PageData, PropertyData


def _properties_from_frontmatter(raw) -> list[PropertyData]:
    """Build list[PropertyData] from frontmatter 'properties' (list of dicts)."""
    if not isinstance(raw, list):
        return []
    out = []
    for item in raw:
        if not isinstance(item, dict) or "id" not in item:
            continue
        pid = str(item["id"])
        name = str(item.get("name", pid))
        type_key = str(item.get("type", "string"))
        value = item.get("value")
        if value is None:
            try:
                value = PropertyType.from_key(type_key).value.default_value()
            except Exception:
                value = None
        out.append(
            PropertyData(id=pid, name=name, type=type_key, value=value, mandatory=False)
        )
    return out


def _properties_to_frontmatter(properties: list[PropertyData]) -> list[dict]:
    """Serialize list[PropertyData] for frontmatter."""
    return [
        {"id": p.id, "name": p.name, "type": p.type, "value": p.value}
        for p in properties
    ]


def safe_path_from_qt(raw) -> Path | None:
    """Convert a value retrieved from Qt item data to a Path safely.

    Qt can hand back a pathlib.Path whose internal state is broken; we
    reconstruct the string via os.path.join on .parts to avoid calling
    Path.__str__ / __fspath__ on the corrupted object.
    """
    if raw is None:
        return None
    if isinstance(raw, str):
        s = raw
    elif isinstance(raw, Path):
        try:
            s = os.path.join(*raw.parts)
        except Exception:
            return None
    else:
        try:
            s = str(raw)
        except Exception:
            return None
    if not s:
        return None
    return Path(os.path.realpath(s))


class RootPageManager:
    """Encapsulates all root-page file operations."""

    def __init__(self, controller: AppController, vault_path: Path) -> None:
        self._controller = controller
        self._vault_path = vault_path

    def list_root_pages(self) -> list[Path]:
        """Return sorted list of .md files at the vault root."""
        return sorted(self._vault_path.glob("*.md"))

    def load(self, path: Path) -> PageData | None:
        """Read a root .md file and return a PageData (id and properties from frontmatter)."""
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return None
        post = frontmatter.loads(text)
        page_id = post.get("id")
        if page_id is not None:
            try:
                page_id = int(page_id)
            except (TypeError, ValueError):
                page_id = None
        properties = _properties_from_frontmatter(post.get("properties"))
        return PageData(
            id=page_id,
            title=path.stem,
            content=post.content or "",
            properties=properties,
            path=path,
        )

    def save(self, page: PageData, title: str, content: str) -> PageData:
        """Write the page back to disk. Renames the file if the title changed.

        Keeps the file in its original folder. Returns an updated PageData.
        """
        old_path = page.path or (self._vault_path / f"{page.title}.md")
        parent_dir = old_path.parent
        safe_name = (title or old_path.stem).strip().replace("/", "-") or old_path.stem
        new_path = parent_dir / f"{safe_name}.md"

        props_raw = _properties_to_frontmatter(getattr(page, "properties", []) or [])
        if page.id is not None or props_raw:
            front = {"properties": props_raw}
            if page.id is not None:
                front["id"] = page.id
            post = frontmatter.Post(content, **front)
            new_path.write_text(frontmatter.dumps(post), encoding="utf-8")
        else:
            new_path.write_text(content, encoding="utf-8")

        if new_path != old_path and old_path.is_file():
            old_path.unlink(missing_ok=True)

        return PageData(
            id=page.id,
            title=new_path.stem,
            content=content,
            properties=getattr(page, "properties", []) or [],
            path=new_path,
        )

    def add_property_to_page(
        self, path: Path, property_id: str, name: str, type_key: str
    ) -> PropertyData | None:
        """Add a single property to a root page's frontmatter. Returns PropertyData on success."""
        page = self.load(path)
        if page is None:
            return None
        for p in page.properties:
            if p.id == property_id:
                return None
        default = PropertyType.from_key(type_key).value.default_value()
        new_prop = PropertyData(
            id=property_id, name=name, type=type_key, value=default, mandatory=False
        )
        page.properties.append(new_prop)
        self.save(page, page.title, page.content)
        return new_prop

    def create(self, title: str = "Untitled") -> PageData:
        """Create a new root page via the controller use case."""
        out = self._controller.create_root_page(self._vault_path, title=title)
        return PageData(
            id=out.page_id,
            title=out.title,
            content=out.content,
            properties=[],
            path=out.path,
        )

    def delete(self, path: Path) -> bool:
        """Delete the file at *path*. Returns True if removed."""
        try:
            path.unlink()
            return True
        except OSError:
            return False
