"""Unit tests for VaultDatabaseRepository. Uses tmp_path and real child repos."""

import json
from pathlib import Path

import pytest

from fern.domain.entities import Property, PropertyType
from fern.interface_adapters.repositories.vault_database_repository import (
    DATABASES_DIRNAME,
    SCHEMA_FILENAME,
    VaultDatabaseRepository,
    ensure_mandatory_properties,
    _read_schema,
    _write_schema,
    _property_from_dict,
    _property_to_dict,
)


# --- ensure_mandatory_properties ---


def test_ensure_mandatory_properties_adds_id_and_title() -> None:
    props, order = ensure_mandatory_properties([], [])
    assert len(props) == 2
    assert props[0].id == "id"
    assert props[0].mandatory is True
    assert props[1].id == "title"
    assert props[1].mandatory is True
    assert order == ["id", "title"]


def test_ensure_mandatory_properties_preserves_existing() -> None:
    user_prop = Property(id="done", name="Done", type=PropertyType.BOOLEAN)
    props, order = ensure_mandatory_properties([user_prop], ["done"])
    assert len(props) == 3
    assert props[0].id == "id"
    assert props[1].id == "title"
    assert props[2].id == "done"
    assert order == ["id", "title", "done"]


def test_ensure_mandatory_properties_no_duplicate_if_present() -> None:
    id_prop = Property(id="id", name="ID", type=PropertyType.ID, mandatory=True)
    title_prop = Property(id="title", name="Title", type=PropertyType.TITLE, mandatory=True)
    props, order = ensure_mandatory_properties([id_prop, title_prop], ["id", "title"])
    assert len(props) == 2
    assert order == ["id", "title"]


# --- _property_from_dict / _property_to_dict ---


def test_property_from_dict_boolean() -> None:
    p = _property_from_dict({"id": "p1", "name": "Done", "type": "boolean"})
    assert p.id == "p1"
    assert p.name == "Done"
    assert p.type == PropertyType.BOOLEAN


def test_property_from_dict_defaults_to_boolean() -> None:
    p = _property_from_dict({"id": "p1", "name": "X"})
    assert p.type == PropertyType.BOOLEAN


def test_property_to_dict() -> None:
    p = Property(id="p1", name="Done", type=PropertyType.BOOLEAN)
    d = _property_to_dict(p)
    assert d == {"id": "p1", "name": "Done", "type": "boolean"}


# --- _read_schema ---


def test_read_schema_no_file(tmp_path: Path) -> None:
    props, order = _read_schema(tmp_path)
    assert props == []
    assert order == []


def test_read_schema_invalid_json(tmp_path: Path) -> None:
    (tmp_path / SCHEMA_FILENAME).write_text("not json {{{", encoding="utf-8")
    props, order = _read_schema(tmp_path)
    assert props == []
    assert order == []


def test_read_schema_valid(tmp_path: Path) -> None:
    data = {
        "properties": [
            {"id": "p1", "name": "Status", "type": "string"},
            {"id": "p2", "name": "Done", "type": "boolean"},
        ],
        "propertyOrder": ["p2", "p1"],
    }
    (tmp_path / SCHEMA_FILENAME).write_text(json.dumps(data), encoding="utf-8")
    props, order = _read_schema(tmp_path)
    assert len(props) == 2
    assert props[0].id == "p1"
    assert props[0].type == PropertyType.STRING
    assert props[1].id == "p2"
    assert props[1].type == PropertyType.BOOLEAN
    assert order == ["p2", "p1"]


def test_read_schema_skips_invalid_entries(tmp_path: Path) -> None:
    data = {
        "properties": [
            {"id": "p1", "name": "A", "type": "boolean"},
            {"name": "no_id"},
            "not_a_dict",
            {"id": "p2", "name": "B", "type": "string"},
        ],
        "propertyOrder": [],
    }
    (tmp_path / SCHEMA_FILENAME).write_text(json.dumps(data), encoding="utf-8")
    props, _ = _read_schema(tmp_path)
    assert len(props) == 2


def test_read_schema_non_list_order(tmp_path: Path) -> None:
    data = {"properties": [], "propertyOrder": "not_a_list"}
    (tmp_path / SCHEMA_FILENAME).write_text(json.dumps(data), encoding="utf-8")
    _, order = _read_schema(tmp_path)
    assert order == []


def test_read_schema_missing_keys(tmp_path: Path) -> None:
    (tmp_path / SCHEMA_FILENAME).write_text("{}", encoding="utf-8")
    props, order = _read_schema(tmp_path)
    assert props == []
    assert order == []


# --- _write_schema ---


def test_write_schema_creates_dir_and_file(tmp_path: Path) -> None:
    db_dir = tmp_path / "newdb"
    prop = Property(id="p1", name="Done", type=PropertyType.BOOLEAN)
    _write_schema(db_dir, [prop], ["p1"])
    assert db_dir.is_dir()
    data = json.loads((db_dir / SCHEMA_FILENAME).read_text(encoding="utf-8"))
    assert data["properties"] == [{"id": "p1", "name": "Done", "type": "boolean"}]
    assert data["propertyOrder"] == ["p1"]


def test_write_schema_skips_mandatory_properties(tmp_path: Path) -> None:
    id_prop = Property(id="id", name="ID", type=PropertyType.ID, mandatory=True)
    user_prop = Property(id="done", name="Done", type=PropertyType.BOOLEAN)
    _write_schema(tmp_path, [id_prop, user_prop], ["id", "done"])
    data = json.loads((tmp_path / SCHEMA_FILENAME).read_text(encoding="utf-8"))
    assert len(data["properties"]) == 1
    assert data["properties"][0]["id"] == "done"
    assert data["propertyOrder"] == ["id", "done"]


def test_write_then_read_roundtrip(tmp_path: Path) -> None:
    props = [
        Property(id="a", name="A", type=PropertyType.STRING),
        Property(id="b", name="B", type=PropertyType.BOOLEAN),
    ]
    _write_schema(tmp_path, props, ["b", "a"])
    loaded_props, loaded_order = _read_schema(tmp_path)
    assert len(loaded_props) == 2
    assert loaded_props[0].id == "a"
    assert loaded_props[1].id == "b"
    assert loaded_order == ["b", "a"]


# --- VaultDatabaseRepository.list_all ---


def test_list_all_empty_vault(tmp_path: Path) -> None:
    (tmp_path / DATABASES_DIRNAME).mkdir()
    repo = VaultDatabaseRepository(tmp_path)
    assert repo.list_all() == []


def test_list_all_no_databases_dir(tmp_path: Path) -> None:
    repo = VaultDatabaseRepository(tmp_path)
    assert repo.list_all() == []


def test_list_all_ignores_dot_dirs(tmp_path: Path) -> None:
    (tmp_path / DATABASES_DIRNAME).mkdir()
    (tmp_path / DATABASES_DIRNAME / ".hidden").mkdir()
    (tmp_path / DATABASES_DIRNAME / "Visible").mkdir()
    (tmp_path / DATABASES_DIRNAME / "Visible" / "page.md").write_text(
        "---\nid: 1\n---\ncontent", encoding="utf-8"
    )
    repo = VaultDatabaseRepository(tmp_path)
    dbs = repo.list_all()
    assert len(dbs) == 1
    assert dbs[0].name == "Visible"


def test_list_all_returns_databases_with_pages_and_schema(tmp_path: Path) -> None:
    (tmp_path / DATABASES_DIRNAME).mkdir()
    inbox = tmp_path / DATABASES_DIRNAME / "Inbox"
    inbox.mkdir()
    (inbox / "Note.md").write_text("---\nid: 1\n---\nhello", encoding="utf-8")
    manifest = {
        "properties": [{"id": "p1", "name": "Done", "type": "boolean"}],
        "propertyOrder": ["p1"],
    }
    (inbox / SCHEMA_FILENAME).write_text(json.dumps(manifest), encoding="utf-8")
    repo = VaultDatabaseRepository(tmp_path)
    dbs = repo.list_all()
    assert len(dbs) == 1
    db = dbs[0]
    assert db.name == "Inbox"
    assert len(db.pages) == 1
    prop_ids = {p.id for p in db.properties}
    assert "p1" in prop_ids
    assert "id" in prop_ids
    assert "title" in prop_ids


def test_list_all_multiple_databases(tmp_path: Path) -> None:
    (tmp_path / DATABASES_DIRNAME).mkdir()
    (tmp_path / DATABASES_DIRNAME / "A").mkdir()
    (tmp_path / DATABASES_DIRNAME / "B").mkdir()
    (tmp_path / DATABASES_DIRNAME / "A" / "page.md").write_text(
        "---\nid: 1\n---\n", encoding="utf-8"
    )
    repo = VaultDatabaseRepository(tmp_path)
    dbs = repo.list_all()
    names = {d.name for d in dbs}
    assert "A" in names
    assert "B" in names


# --- VaultDatabaseRepository.get_schema ---


def test_get_schema_existing_db(tmp_path: Path) -> None:
    (tmp_path / DATABASES_DIRNAME).mkdir()
    db_dir = tmp_path / DATABASES_DIRNAME / "Notes"
    db_dir.mkdir()
    manifest = {
        "properties": [{"id": "p1", "name": "Done", "type": "boolean"}],
        "propertyOrder": ["p1"],
    }
    (db_dir / SCHEMA_FILENAME).write_text(json.dumps(manifest), encoding="utf-8")
    repo = VaultDatabaseRepository(tmp_path)
    props, order = repo.get_schema("Notes")
    prop_ids = {p.id for p in props}
    assert "p1" in prop_ids
    assert "id" in prop_ids
    assert "title" in prop_ids
    assert "p1" in order


def test_get_schema_nonexistent_db(tmp_path: Path) -> None:
    (tmp_path / DATABASES_DIRNAME).mkdir()
    repo = VaultDatabaseRepository(tmp_path)
    props, order = repo.get_schema("NoSuchDb")
    assert props == []
    assert order == []


def test_get_schema_case_insensitive(tmp_path: Path) -> None:
    (tmp_path / DATABASES_DIRNAME).mkdir()
    db_dir = tmp_path / DATABASES_DIRNAME / "Notes"
    db_dir.mkdir()
    (db_dir / SCHEMA_FILENAME).write_text(
        json.dumps({"properties": [], "propertyOrder": []}), encoding="utf-8"
    )
    repo = VaultDatabaseRepository(tmp_path)
    props, order = repo.get_schema("notes")
    assert "id" in order
    assert "title" in order


def test_get_schema_no_databases_dir(tmp_path: Path) -> None:
    repo = VaultDatabaseRepository(tmp_path)
    props, order = repo.get_schema("Anything")
    assert props == []
    assert order == []


# --- VaultDatabaseRepository.save_schema ---


def test_save_schema_writes_manifest(tmp_path: Path) -> None:
    (tmp_path / DATABASES_DIRNAME).mkdir()
    db_dir = tmp_path / DATABASES_DIRNAME / "Notes"
    db_dir.mkdir()
    repo = VaultDatabaseRepository(tmp_path)
    prop = Property(id="p1", name="Done", type=PropertyType.BOOLEAN)
    repo.save_schema("Notes", [prop], ["p1"])
    data = json.loads((db_dir / SCHEMA_FILENAME).read_text(encoding="utf-8"))
    assert data["properties"][0]["id"] == "p1"
    assert data["propertyOrder"] == ["p1"]


def test_save_schema_nonexistent_db_raises(tmp_path: Path) -> None:
    (tmp_path / DATABASES_DIRNAME).mkdir()
    repo = VaultDatabaseRepository(tmp_path)
    with pytest.raises(FileNotFoundError):
        repo.save_schema("NoSuchDb", [], [])


def test_save_schema_case_insensitive(tmp_path: Path) -> None:
    (tmp_path / DATABASES_DIRNAME).mkdir()
    db_dir = tmp_path / DATABASES_DIRNAME / "Notes"
    db_dir.mkdir()
    repo = VaultDatabaseRepository(tmp_path)
    repo.save_schema("notes", [], ["id", "title"])
    data = json.loads((db_dir / SCHEMA_FILENAME).read_text(encoding="utf-8"))
    assert data["propertyOrder"] == ["id", "title"]


def test_save_then_get_schema_roundtrip(tmp_path: Path) -> None:
    (tmp_path / DATABASES_DIRNAME).mkdir()
    db_dir = tmp_path / DATABASES_DIRNAME / "DB"
    db_dir.mkdir()
    repo = VaultDatabaseRepository(tmp_path)
    prop = Property(id="status", name="Status", type=PropertyType.STRING)
    repo.save_schema("DB", [prop], ["id", "title", "status"])
    props, order = repo.get_schema("DB")
    user_props = [p for p in props if not p.mandatory]
    assert len(user_props) == 1
    assert user_props[0].id == "status"
    assert "status" in order
