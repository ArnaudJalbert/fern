"""Unit tests for VaultDatabaseRepository. Uses tmp_path and real child repos."""

import json
from pathlib import Path

import pytest

from fern.domain.entities import (
    BooleanProperty,
    IdProperty,
    StatusProperty,
    StringProperty,
    TitleProperty,
)
from fern.interface_adapters.repositories.vault_database_repository import (
    DATABASE_MARKER,
    VaultDatabaseRepository,
    database_name_from_path,
    ensure_mandatory_properties,
    find_databases,
    is_database_folder,
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
    user_prop = BooleanProperty(id="done", name="Done")
    props, order = ensure_mandatory_properties([user_prop], ["done"])
    assert len(props) == 3
    assert props[0].id == "id"
    assert props[1].id == "title"
    assert props[2].id == "done"
    assert order == ["id", "title", "done"]


def test_ensure_mandatory_properties_no_duplicate_if_present() -> None:
    id_prop = IdProperty(id="id", name="ID")
    title_prop = TitleProperty(id="title", name="Title")
    props, order = ensure_mandatory_properties([id_prop, title_prop], ["id", "title"])
    assert len(props) == 2
    assert order == ["id", "title"]


# --- _property_from_dict / _property_to_dict ---


def test_property_from_dict_boolean() -> None:
    p = _property_from_dict({"id": "p1", "name": "Done", "type": "boolean"})
    assert p.id == "p1"
    assert p.name == "Done"
    assert p.type_key() == "boolean"


def test_property_from_dict_missing_type_raises() -> None:
    with pytest.raises(ValueError, match="missing 'type'"):
        _property_from_dict({"id": "p1", "name": "X"})


def test_property_to_dict() -> None:
    p = BooleanProperty(id="p1", name="Done")
    d = _property_to_dict(p)
    assert d == {"id": "p1", "name": "Done", "type": "boolean"}


def test_property_from_dict_status_with_choices() -> None:
    raw = {
        "id": "status",
        "name": "Status",
        "type": "status",
        "choices": [
            {"name": "Done", "category": "c1", "color": "#0f0"},
            {"name": "Todo", "category": "c1", "color": "#f00"},
        ],
    }
    prop = _property_from_dict(raw)
    assert isinstance(prop, StatusProperty)
    assert prop.id == "status"
    assert prop.name == "Status"
    assert len(prop.choices) == 2
    assert prop.choices[0].name == "Done"
    assert prop.choices[1].name == "Todo"


def test_property_from_dict_status_empty_choices() -> None:
    raw = {"id": "status", "name": "Status", "type": "status"}
    prop = _property_from_dict(raw)
    assert isinstance(prop, StatusProperty)
    assert prop.choices == []


def test_property_to_dict_status_with_choices() -> None:
    from fern.domain.entities import Choice
    from fern.domain.entities.properties.choice_category import ChoiceCategory

    choice = Choice(name="Done", category=ChoiceCategory(name="c1"), color="#0f0")
    prop = StatusProperty(id="p1", name="Status", choices=[choice])
    d = _property_to_dict(prop)
    assert d["type"] == "status"
    assert "choices" in d
    assert len(d["choices"]) == 1
    assert d["choices"][0]["name"] == "Done"
    assert d["choices"][0]["color"] == "#0f0"


# --- _read_schema ---


def test_read_schema_no_file(tmp_path: Path) -> None:
    props, order = _read_schema(tmp_path)
    assert props == []
    assert order == []


def test_read_schema_invalid_json(tmp_path: Path) -> None:
    (tmp_path / DATABASE_MARKER).write_text("not json {{{", encoding="utf-8")
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
    (tmp_path / DATABASE_MARKER).write_text(json.dumps(data), encoding="utf-8")
    props, order = _read_schema(tmp_path)
    assert len(props) == 2
    assert props[0].id == "p1"
    assert props[0].type_key() == "string"
    assert props[1].id == "p2"
    assert props[1].type_key() == "boolean"
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
    (tmp_path / DATABASE_MARKER).write_text(json.dumps(data), encoding="utf-8")
    props, _ = _read_schema(tmp_path)
    assert len(props) == 2


def test_read_schema_non_list_order(tmp_path: Path) -> None:
    data = {"properties": [], "propertyOrder": "not_a_list"}
    (tmp_path / DATABASE_MARKER).write_text(json.dumps(data), encoding="utf-8")
    _, order = _read_schema(tmp_path)
    assert order == []


def test_read_schema_missing_keys(tmp_path: Path) -> None:
    (tmp_path / DATABASE_MARKER).write_text("{}", encoding="utf-8")
    props, order = _read_schema(tmp_path)
    assert props == []
    assert order == []


# --- _write_schema ---


def test_write_schema_creates_dir_and_file(tmp_path: Path) -> None:
    db_dir = tmp_path / "newdb"
    prop = BooleanProperty(id="p1", name="Done")
    _write_schema(db_dir, [prop], ["p1"])
    assert db_dir.is_dir()
    data = json.loads((db_dir / DATABASE_MARKER).read_text(encoding="utf-8"))
    assert data["properties"] == [{"id": "p1", "name": "Done", "type": "boolean"}]
    assert data["propertyOrder"] == ["p1"]


def test_write_schema_skips_mandatory_properties(tmp_path: Path) -> None:
    id_prop = IdProperty(id="id", name="ID")
    user_prop = BooleanProperty(id="done", name="Done")
    _write_schema(tmp_path, [id_prop, user_prop], ["id", "done"])
    data = json.loads((tmp_path / DATABASE_MARKER).read_text(encoding="utf-8"))
    assert len(data["properties"]) == 1
    assert data["properties"][0]["id"] == "done"
    assert data["propertyOrder"] == ["id", "done"]


def test_write_then_read_roundtrip(tmp_path: Path) -> None:
    props = [
        StringProperty(id="a", name="A"),
        BooleanProperty(id="b", name="B"),
    ]
    _write_schema(tmp_path, props, ["b", "a"])
    loaded_props, loaded_order = _read_schema(tmp_path)
    assert len(loaded_props) == 2
    assert loaded_props[0].id == "a"
    assert loaded_props[1].id == "b"
    assert loaded_order == ["b", "a"]


# --- is_database_folder / find_databases / database_name_from_path ---


def test_is_database_folder_true(tmp_path: Path) -> None:
    db = tmp_path / "mydb"
    db.mkdir()
    (db / DATABASE_MARKER).write_text("{}", encoding="utf-8")
    assert is_database_folder(db) is True


def test_is_database_folder_false(tmp_path: Path) -> None:
    folder = tmp_path / "regular"
    folder.mkdir()
    assert is_database_folder(folder) is False


def test_find_databases_recursive(tmp_path: Path) -> None:
    # vault/Inbox (db)
    inbox = tmp_path / "Inbox"
    inbox.mkdir()
    (inbox / DATABASE_MARKER).write_text("{}", encoding="utf-8")
    # vault/Projects/Tasks (db)
    tasks = tmp_path / "Projects" / "Tasks"
    tasks.mkdir(parents=True)
    (tasks / DATABASE_MARKER).write_text("{}", encoding="utf-8")
    # vault/Notes (not a db)
    (tmp_path / "Notes").mkdir()

    dbs = find_databases(tmp_path)
    names = {database_name_from_path(tmp_path, d) for d in dbs}
    assert "Inbox" in names
    assert str(Path("Projects") / "Tasks") in names
    assert len(dbs) == 2


def test_find_databases_skips_hidden(tmp_path: Path) -> None:
    hidden = tmp_path / ".hidden"
    hidden.mkdir()
    (hidden / DATABASE_MARKER).write_text("{}", encoding="utf-8")
    assert find_databases(tmp_path) == []


def test_database_name_from_path(tmp_path: Path) -> None:
    db_path = tmp_path / "A" / "B"
    assert database_name_from_path(tmp_path, db_path) == str(Path("A") / "B")


def test_database_name_from_path_unrelated_falls_back_to_name(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    unrelated = tmp_path / "other" / "MyDB"
    assert database_name_from_path(vault, unrelated) == "MyDB"


def test_find_databases_skips_unreadable_dir(tmp_path: Path) -> None:
    """_scan gracefully skips directories it cannot list."""
    from unittest.mock import patch

    good = tmp_path / "Good"
    good.mkdir()
    (good / DATABASE_MARKER).write_text("{}", encoding="utf-8")
    bad = tmp_path / "Bad"
    bad.mkdir()

    original_iterdir = Path.iterdir

    def patched_iterdir(self):
        if self == bad:
            raise OSError("permission denied")
        return original_iterdir(self)

    with patch.object(Path, "iterdir", patched_iterdir):
        result = find_databases(tmp_path)

    names = {d.name for d in result}
    assert "Good" in names
    assert "Bad" not in names


def test_scan_skips_entry_where_is_dir_raises(tmp_path: Path) -> None:
    """_scan skips entries where is_dir() raises OSError."""
    from unittest.mock import patch

    good = tmp_path / "Good"
    good.mkdir()
    (good / DATABASE_MARKER).write_text("{}", encoding="utf-8")

    original_is_dir = Path.is_dir

    call_count = 0

    def patched_is_dir(self):
        nonlocal call_count
        if self.name == "Bad":
            raise OSError("stat failed")
        return original_is_dir(self)

    bad = tmp_path / "Bad"
    bad.mkdir()

    with patch.object(Path, "is_dir", patched_is_dir):
        result = find_databases(tmp_path)

    assert len(result) == 1
    assert result[0].name == "Good"


# --- VaultDatabaseRepository._resolve_db_dir case-insensitive fallback ---


def test_resolve_db_dir_case_insensitive_via_scan(tmp_path: Path) -> None:
    """When the direct candidate path doesn't exist, _resolve_db_dir falls back to scanning."""
    from unittest.mock import patch

    db_dir = tmp_path / "MyNotes"
    db_dir.mkdir()
    (db_dir / DATABASE_MARKER).write_text("{}", encoding="utf-8")
    repo = VaultDatabaseRepository(tmp_path)

    original_is_dir = Path.is_dir
    first_call = [True]

    def patched_is_dir(self):
        if first_call[0] and self == tmp_path / "mynotes":
            first_call[0] = False
            return False
        return original_is_dir(self)

    with patch.object(Path, "is_dir", patched_is_dir):
        props, order = repo.get_schema("mynotes")

    assert "id" in order
    assert "title" in order


def test_resolve_db_dir_scan_returns_none_when_no_match(tmp_path: Path) -> None:
    """_resolve_db_dir returns None when no database matches (even via scan)."""
    repo = VaultDatabaseRepository(tmp_path)
    assert repo._resolve_db_dir("nonexistent") is None


# --- VaultDatabaseRepository.list_all ---


def test_list_all_empty_vault(tmp_path: Path) -> None:
    repo = VaultDatabaseRepository(tmp_path)
    assert repo.list_all() == []


def test_list_all_ignores_dot_dirs(tmp_path: Path) -> None:
    hidden = tmp_path / ".hidden"
    hidden.mkdir()
    (hidden / DATABASE_MARKER).write_text("{}", encoding="utf-8")
    visible = tmp_path / "Visible"
    visible.mkdir()
    (visible / DATABASE_MARKER).write_text("{}", encoding="utf-8")
    (visible / "page.md").write_text("---\nid: 1\n---\ncontent", encoding="utf-8")
    repo = VaultDatabaseRepository(tmp_path)
    dbs = repo.list_all()
    assert len(dbs) == 1
    assert dbs[0].name == "Visible"


def test_list_all_returns_databases_with_pages_and_schema(tmp_path: Path) -> None:
    inbox = tmp_path / "Inbox"
    inbox.mkdir()
    (inbox / "Note.md").write_text("---\nid: 1\n---\nhello", encoding="utf-8")
    manifest = {
        "properties": [{"id": "p1", "name": "Done", "type": "boolean"}],
        "propertyOrder": ["p1"],
    }
    (inbox / DATABASE_MARKER).write_text(json.dumps(manifest), encoding="utf-8")
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
    for name in ("A", "B"):
        d = tmp_path / name
        d.mkdir()
        (d / DATABASE_MARKER).write_text("{}", encoding="utf-8")
    (tmp_path / "A" / "page.md").write_text("---\nid: 1\n---\n", encoding="utf-8")
    repo = VaultDatabaseRepository(tmp_path)
    dbs = repo.list_all()
    names = {d.name for d in dbs}
    assert "A" in names
    assert "B" in names


def test_list_all_nested_database(tmp_path: Path) -> None:
    nested = tmp_path / "Projects" / "Tasks"
    nested.mkdir(parents=True)
    (nested / DATABASE_MARKER).write_text("{}", encoding="utf-8")
    (nested / "task.md").write_text("---\nid: 1\n---\ndo it", encoding="utf-8")
    repo = VaultDatabaseRepository(tmp_path)
    dbs = repo.list_all()
    assert len(dbs) == 1
    assert dbs[0].name == str(Path("Projects") / "Tasks")


# --- VaultDatabaseRepository.get_schema ---


def test_get_schema_existing_db(tmp_path: Path) -> None:
    db_dir = tmp_path / "Notes"
    db_dir.mkdir()
    manifest = {
        "properties": [{"id": "p1", "name": "Done", "type": "boolean"}],
        "propertyOrder": ["p1"],
    }
    (db_dir / DATABASE_MARKER).write_text(json.dumps(manifest), encoding="utf-8")
    repo = VaultDatabaseRepository(tmp_path)
    props, order = repo.get_schema("Notes")
    prop_ids = {p.id for p in props}
    assert "p1" in prop_ids
    assert "id" in prop_ids
    assert "title" in prop_ids
    assert "p1" in order


def test_get_schema_nonexistent_db(tmp_path: Path) -> None:
    repo = VaultDatabaseRepository(tmp_path)
    props, order = repo.get_schema("NoSuchDb")
    assert props == []
    assert order == []


def test_get_schema_case_insensitive(tmp_path: Path) -> None:
    db_dir = tmp_path / "Notes"
    db_dir.mkdir()
    (db_dir / DATABASE_MARKER).write_text(
        json.dumps({"properties": [], "propertyOrder": []}), encoding="utf-8"
    )
    repo = VaultDatabaseRepository(tmp_path)
    props, order = repo.get_schema("notes")
    assert "id" in order
    assert "title" in order


# --- VaultDatabaseRepository.save_schema ---


def test_save_schema_writes_manifest(tmp_path: Path) -> None:
    db_dir = tmp_path / "Notes"
    db_dir.mkdir()
    (db_dir / DATABASE_MARKER).write_text("{}", encoding="utf-8")
    repo = VaultDatabaseRepository(tmp_path)
    prop = BooleanProperty(id="p1", name="Done")
    repo.save_schema("Notes", [prop], ["p1"])
    data = json.loads((db_dir / DATABASE_MARKER).read_text(encoding="utf-8"))
    assert data["properties"][0]["id"] == "p1"
    assert data["propertyOrder"] == ["p1"]


def test_save_schema_nonexistent_db_raises(tmp_path: Path) -> None:
    repo = VaultDatabaseRepository(tmp_path)
    with pytest.raises(FileNotFoundError):
        repo.save_schema("NoSuchDb", [], [])


def test_save_schema_case_insensitive(tmp_path: Path) -> None:
    db_dir = tmp_path / "Notes"
    db_dir.mkdir()
    (db_dir / DATABASE_MARKER).write_text("{}", encoding="utf-8")
    repo = VaultDatabaseRepository(tmp_path)
    repo.save_schema("notes", [], ["id", "title"])
    data = json.loads((db_dir / DATABASE_MARKER).read_text(encoding="utf-8"))
    assert data["propertyOrder"] == ["id", "title"]


def test_save_then_get_schema_roundtrip(tmp_path: Path) -> None:
    db_dir = tmp_path / "DB"
    db_dir.mkdir()
    (db_dir / DATABASE_MARKER).write_text("{}", encoding="utf-8")
    repo = VaultDatabaseRepository(tmp_path)
    prop = StringProperty(id="status", name="Status")
    repo.save_schema("DB", [prop], ["id", "title", "status"])
    props, order = repo.get_schema("DB")
    user_props = [p for p in props if not p.mandatory]
    assert len(user_props) == 1
    assert user_props[0].id == "status"
    assert "status" in order
