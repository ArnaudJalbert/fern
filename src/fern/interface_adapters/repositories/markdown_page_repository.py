from pathlib import Path

import frontmatter

from fern.domain.entities.page import Page
from fern.domain.entities.properties import Property, PropertyType
from fern.domain.repositories.page_repository import PageRepository


def _safe_filename(name: str) -> str:
    """Return a filesystem-safe name (no path separators)."""
    return "".join(c for c in name if c not in "/\\").strip() or "untitled"


def _properties_from_raw(raw) -> list[Property]:
    """Build list[Property] from frontmatter (list of dicts or legacy dict)."""
    if isinstance(raw, list):
        out = []
        for item in raw:
            if not isinstance(item, dict) or "id" not in item:
                continue
            pid = str(item["id"])
            name = str(item.get("name", pid))
            ptype = PropertyType.from_key(str(item.get("type", "boolean")))
            raw_value = item.get("value")
            if raw_value is None and hasattr(ptype.value, "default_value"):
                raw_value = ptype.value.default_value()
            value = (
                ptype.value.coerce(raw_value)
                if hasattr(ptype.value, "coerce")
                else raw_value
            )
            out.append(Property(id=pid, name=name, type=ptype, value=value))
        return out
    if isinstance(raw, dict):
        return [
            Property(
                id=str(k), name=str(k), type=PropertyType.from_key("boolean"), value=v
            )
            for k, v in raw.items()
        ]
    return []


def _properties_to_raw(properties: list[Property]) -> list[dict]:
    """Serialize list[Property] for frontmatter (type as string for YAML)."""
    return [
        {"id": p.id, "name": p.name, "type": p.type.key(), "value": p.value}
        for p in properties
    ]


def _page_from_file(path: Path) -> Page | None:
    """Parse a single .md file with frontmatter; return Page or None if invalid."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    post = frontmatter.loads(text)
    fid = post.get("id")
    if fid is None:
        return None
    try:
        page_id = int(fid)
    except (ValueError, TypeError):
        return None
    title = path.stem
    content = post.content or ""
    properties = _properties_from_raw(post.get("properties"))
    return Page(
        id=page_id, title=title, content=content, properties=properties, folder=""
    )


class MarkdownPageRepository(PageRepository):
    """PageRepository that reads pages from Markdown files.

    Each .md file must start with YAML frontmatter between two --- containing id:
    ---
    id: 1234
    ---

    The filename (without .md) is the page title. The content is everything after the closing ---.
    """

    def __init__(self, pages_dir: Path | str, *, folder: str = "") -> None:
        self._pages_dir = Path(pages_dir)
        self._folder = folder

    def get_by_id(self, page_id: int) -> Page | None:
        for path in self._pages_dir.glob("*.md"):
            if not path.is_file():
                continue
            page = _page_from_file(path)
            if page is not None and page.id == page_id:
                return Page(
                    id=page.id,
                    title=page.title,
                    content=page.content,
                    properties=page.properties,
                    folder=self._folder,
                )
        return None

    def list_all(self) -> list[Page]:
        result: list[Page] = []
        for path in self._pages_dir.glob("*.md"):
            if not path.is_file():
                continue
            page = _page_from_file(path)
            if page is not None:
                result.append(
                    Page(
                        id=page.id,
                        title=page.title,
                        content=page.content,
                        properties=page.properties,
                        folder=self._folder,
                    )
                )
        return result

    def update(
        self,
        page_id: int,
        title: str,
        content: str,
        *,
        properties: list | None = None,
    ) -> None:
        self._pages_dir.mkdir(parents=True, exist_ok=True)
        old_path: Path | None = None
        existing: Page | None = None
        for path in self._pages_dir.glob("*.md"):
            if not path.is_file():
                continue
            page = _page_from_file(path)
            if page is not None and page.id == page_id:
                old_path = path
                existing = page
                break
        if old_path is None:
            return
        props_raw = (
            _properties_to_raw(properties)
            if properties is not None
            else _properties_to_raw(existing.properties if existing else [])
        )
        front = {"id": page_id, "properties": props_raw}
        post = frontmatter.Post(content, **front)
        payload = frontmatter.dumps(post)
        new_name = _safe_filename(title) or "untitled"
        new_path = self._pages_dir / f"{new_name}.md"
        if new_path.resolve() != old_path.resolve():
            new_path.write_text(payload, encoding="utf-8")
            old_path.unlink(missing_ok=True)
        else:
            old_path.write_text(payload, encoding="utf-8")

    def create(self, title: str, content: str) -> Page:
        pages = self.list_all()
        next_id = max((p.id for p in pages), default=0) + 1
        name = _safe_filename(title) or "untitled"
        path = self._pages_dir / f"{name}.md"
        if path.exists():
            base, ext = name, ".md"
            for n in range(1, 1000):
                path = self._pages_dir / f"{base} {n}{ext}"
                if not path.exists():
                    break
        post = frontmatter.Post(content, **{"id": next_id, "properties": []})
        path.write_text(frontmatter.dumps(post), encoding="utf-8")
        return Page(
            id=next_id,
            title=path.stem,
            content=content,
            properties=[],
            folder=self._folder,
        )

    def delete(self, page_id: int) -> None:
        for path in self._pages_dir.glob("*.md"):
            if not path.is_file():
                continue
            page = _page_from_file(path)
            if page is not None and page.id == page_id:
                path.unlink(missing_ok=True)
                return
