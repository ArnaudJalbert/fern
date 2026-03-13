"""Filesystem implementation of DatabaseRepository: databases are subdirs of vault/Databases/."""

import json
import os
from pathlib import Path

from fern.domain.entities import Database, Property, PropertyType
from fern.domain.repositories.database_repository import DatabaseRepository
from fern.interface_adapters.repositories.markdown_page_repository import (
    MarkdownPageRepository,
)

DATABASES_DIRNAME = "Databases"
SCHEMA_FILENAME = "schema.json"

ID_PROPERTY = Property(id="id", name="ID", type=PropertyType.ID, mandatory=True)
TITLE_PROPERTY = Property(id="title", name="Title", type=PropertyType.TITLE, mandatory=True)


def _property_from_dict(d: dict) -> Property:
    raw = d.get("type", "boolean")
    ptype = PropertyType.from_key(raw)
    return Property(id=str(d["id"]), name=str(d["name"]), type=ptype)


def _property_to_dict(p: Property) -> dict:
    return {"id": p.id, "name": p.name, "type": p.type.key()}


def ensure_mandatory_properties(
    properties: list[Property], property_order: list[str]
) -> tuple[list[Property], list[str]]:
    """Prepend id/title to properties and property_order if not already present."""
    prop_ids = {p.id for p in properties}
    full_props = list(properties)
    if "title" not in prop_ids:
        full_props.insert(0, TITLE_PROPERTY)
    if "id" not in prop_ids:
        full_props.insert(0, ID_PROPERTY)

    order_set = set(property_order)
    full_order = list(property_order)
    if "title" not in order_set:
        full_order.insert(0, "title")
    if "id" not in order_set:
        full_order.insert(0, "id")

    return full_props, full_order


def _read_schema(db_dir: Path) -> tuple[list[Property], list[str]]:
    """Read properties and property_order from schema.json in db_dir."""
    path = db_dir / SCHEMA_FILENAME
    if not path.is_file():
        return ([], [])
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return ([], [])
    props = data.get("properties") or []
    order = data.get("propertyOrder") or []
    if isinstance(order, list):
        order = [str(x) for x in order]
    else:
        order = []
    properties = [
        _property_from_dict(p)
        for p in props
        if isinstance(p, dict) and "id" in p
    ]
    return (properties, order)


def _write_schema(
    db_dir: Path, properties: list[Property], property_order: list[str]
) -> None:
    """Write properties and property_order to schema.json in db_dir."""
    dir_path = Path(db_dir).resolve()
    dir_path.mkdir(parents=True, exist_ok=True)
    file_path = dir_path / SCHEMA_FILENAME
    user_props = [p for p in properties if not getattr(p, "mandatory", False)]
    data = {
        "properties": [_property_to_dict(p) for p in user_props],
        "propertyOrder": list(property_order),
    }
    raw = json.dumps(data, indent=2)
    with file_path.open("w", encoding="utf-8") as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())


class VaultDatabaseRepository(DatabaseRepository):
    """Databases are subdirectories of vault_path/Databases/; schema stored in schema.json."""

    def __init__(self, vault_path: Path | str) -> None:
        self._vault_path = Path(vault_path)

    def _databases_dir(self) -> Path:
        return self._vault_path / DATABASES_DIRNAME

    def _resolve_db_dir(self, database_name: str) -> Path | None:
        """Find the exact database directory by name (case-sensitive then insensitive)."""
        databases_dir = self._databases_dir()
        if not databases_dir.is_dir():
            return None
        for d in databases_dir.iterdir():
            if d.is_dir() and not d.name.startswith(".") and d.name == database_name:
                return d
        for d in databases_dir.iterdir():
            if d.is_dir() and not d.name.startswith(".") and d.name.lower() == database_name.lower():
                return d
        return None

    def list_all(self) -> list[Database]:
        databases_dir = self._databases_dir()
        if not databases_dir.is_dir():
            return []
        result = []
        for d in databases_dir.iterdir():
            if not d.is_dir() or d.name.startswith("."):
                continue
            page_repo = MarkdownPageRepository(d)
            pages = page_repo.list_all()
            properties, property_order = _read_schema(d)
            properties, property_order = ensure_mandatory_properties(properties, property_order)
            result.append(
                Database(
                    name=d.name,
                    pages=pages,
                    properties=properties,
                    property_order=property_order,
                )
            )
        return result

    def get_schema(self, database_name: str) -> tuple[list[Property], list[str]]:
        db_dir = self._resolve_db_dir(database_name)
        if db_dir is None:
            return ([], [])
        properties, property_order = _read_schema(db_dir)
        properties, property_order = ensure_mandatory_properties(properties, property_order)
        return (properties, property_order)

    def save_schema(
        self, database_name: str, properties: list[Property], property_order: list[str]
    ) -> None:
        db_dir = self._resolve_db_dir(database_name)
        if db_dir is None:
            raise FileNotFoundError(
                f"Database folder not found: {database_name!r} in {self._databases_dir()}"
            )
        _write_schema(db_dir, properties, property_order)
