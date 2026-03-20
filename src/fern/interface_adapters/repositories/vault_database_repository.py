"""Filesystem implementation of DatabaseRepository.

Databases are any folder in the vault that contains a database.json marker file.
The marker stores the schema (properties + display order). Pages are .md files
in the same folder.
"""

import json
import os
from pathlib import Path

from fern.application.repositories.database_repository import DatabaseRepository
from fern.domain.entities import (
    Choice,
    Database,
    IdProperty,
    Property,
    PropertyType,
    StatusProperty,
    TitleProperty,
)
from fern.interface_adapters.repositories.markdown_page_repository import (
    MarkdownPageRepository,
)

DATABASE_MARKER = "database.json"

ID_PROPERTY = IdProperty(id="id", name="ID")
TITLE_PROPERTY = TitleProperty(id="title", name="Title")


def _property_from_dict(raw_dict: dict) -> Property:
    raw_type = raw_dict.get("type")
    if raw_type is None:
        raise ValueError(
            f"Property definition missing 'type' (id={raw_dict.get('id', '?')})"
        )
    property_type = PropertyType.from_key(str(raw_type))

    if property_type == PropertyType.STATUS:
        raw_choices = raw_dict.get("choices")
        choices: list[Choice] = []
        if isinstance(raw_choices, list):
            choices = [
                Choice(
                    name=str(choice_dict.get("name", "")),
                    category=str(choice_dict.get("category", "")),
                    color=str(choice_dict.get("color", "")),
                )
                for choice_dict in raw_choices
                if isinstance(choice_dict, dict)
            ]
        return StatusProperty(
            id=str(raw_dict["id"]),
            name=str(raw_dict["name"]),
            choices=choices,
        )

    return property_type.create(
        id=str(raw_dict["id"]),
        name=str(raw_dict["name"]),
    )


def _property_to_dict(schema_property: Property) -> dict:
    out: dict = {
        "id": schema_property.id,
        "name": schema_property.name,
        "type": schema_property.type_key(),
    }
    if isinstance(schema_property, StatusProperty) and schema_property.choices:
        out["choices"] = [
            {"name": choice.name, "category": choice.category, "color": choice.color}
            for choice in schema_property.choices
        ]
    return out


def ensure_mandatory_properties(
    properties: list[Property], property_order: list[str]
) -> tuple[list[Property], list[str]]:
    """Prepend id/title to properties and property_order if not already present."""
    prop_ids = {page_property.id for page_property in properties}
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
    """Read properties and property_order from database.json in db_dir."""
    path = db_dir / DATABASE_MARKER
    if not path.is_file():
        return ([], [])
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return ([], [])
    props = data.get("properties") or []
    order = data.get("propertyOrder") or []
    if isinstance(order, list):
        order = [str(entry) for entry in order]
    else:
        order = []
    properties = [
        _property_from_dict(raw_property)
        for raw_property in props
        if isinstance(raw_property, dict) and "id" in raw_property
    ]
    return (properties, order)


def _write_schema(
    db_dir: Path, properties: list[Property], property_order: list[str]
) -> None:
    """Write properties and property_order to database.json in db_dir."""
    dir_path = Path(db_dir).resolve()
    dir_path.mkdir(parents=True, exist_ok=True)
    file_path = dir_path / DATABASE_MARKER
    user_props = [
        page_property for page_property in properties if not page_property.mandatory
    ]
    data = {
        "properties": [
            _property_to_dict(schema_property) for schema_property in user_props
        ],
        "propertyOrder": list(property_order),
    }
    raw = json.dumps(data, indent=2)
    with file_path.open("w", encoding="utf-8") as file_handle:
        file_handle.write(raw)
        file_handle.flush()
        os.fsync(file_handle.fileno())


def is_database_folder(folder: Path) -> bool:
    """Return True if the folder contains a database.json marker."""
    return (folder / DATABASE_MARKER).is_file()


def find_databases(vault_path: Path) -> list[Path]:
    """Recursively find all folders under vault_path that contain database.json.

    Skips hidden directories (starting with .).
    Does not descend into database folders (a DB cannot be nested inside another).
    """
    result: list[Path] = []
    _scan(vault_path, result)
    return result


def _scan(directory: Path, out: list[Path]) -> None:
    """DFS scan for database.json markers."""
    try:
        entries = sorted(directory.iterdir())
    except OSError:
        return
    for entry in entries:
        try:
            if not entry.is_dir() or entry.name.startswith("."):
                continue
        except OSError:
            continue
        if is_database_folder(entry):
            out.append(entry)
        else:
            _scan(entry, out)


def database_name_from_path(vault_path: Path, db_path: Path) -> str:
    """Return the relative path from vault root to the database folder as the DB name.

    e.g. vault/Projects/Tasks -> 'Projects/Tasks'
    """
    try:
        return str(db_path.relative_to(vault_path))
    except ValueError:
        return db_path.name


class VaultDatabaseRepository(DatabaseRepository):
    """Databases are any folder under vault_path containing database.json."""

    def __init__(self, vault_path: Path | str) -> None:
        self._vault_path = Path(vault_path)

    def _resolve_db_dir(self, database_name: str) -> Path | None:
        """Find the exact database directory by relative name."""
        candidate = self._vault_path / database_name
        if candidate.is_dir() and is_database_folder(candidate):
            return candidate
        target = database_name.lower()
        for db_path in find_databases(self._vault_path):
            name = database_name_from_path(self._vault_path, db_path)
            if name.lower() == target:
                return db_path
        return None

    def list_all(self) -> list[Database]:
        result = []
        for db_path in find_databases(self._vault_path):
            folder = database_name_from_path(self._vault_path, db_path)
            page_repo = MarkdownPageRepository(db_path, folder=folder)
            pages = page_repo.list_all()
            properties, property_order = _read_schema(db_path)
            properties, property_order = ensure_mandatory_properties(
                properties, property_order
            )
            result.append(
                Database(
                    name=folder,
                    pages=pages,
                    properties=properties,
                    property_order=property_order,
                    folder=folder,
                )
            )
        return result

    def get_schema(self, database_name: str) -> tuple[list[Property], list[str]]:
        db_dir = self._resolve_db_dir(database_name)
        if db_dir is None:
            return ([], [])
        properties, property_order = _read_schema(db_dir)
        properties, property_order = ensure_mandatory_properties(
            properties, property_order
        )
        return (properties, property_order)

    def save_schema(
        self, database_name: str, properties: list[Property], property_order: list[str]
    ) -> None:
        db_dir = self._resolve_db_dir(database_name)
        if db_dir is None:
            raise FileNotFoundError(
                f"Database folder not found: {database_name!r} in {self._vault_path}"
            )
        _write_schema(db_dir, properties, property_order)
