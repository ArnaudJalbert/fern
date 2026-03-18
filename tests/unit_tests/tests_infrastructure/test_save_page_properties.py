"""Regression tests: saving a page through the controller must persist properties to disk.

The bug: save_page previously only wrote title + content to the markdown file,
silently dropping in-memory properties. After a reload the properties were gone.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import frontmatter

from fern.domain.entities.properties import BooleanProperty, StringProperty
from fern.interface_adapters.repositories.markdown_page_repository import (
    MarkdownPageRepository,
)
from fern.interface_adapters.repositories.vault_database_repository import (
    VaultDatabaseRepository,
)
from fern.application.dtos import (
    AddPropertyInputDTO,
    ApplyPropertyToPagesInputDTO,
    BooleanPropertyInputDTO,
    StringPropertyInputDTO,
)
from fern.application.use_cases.add_property import AddPropertyUseCase
from fern.application.use_cases.apply_property_to_pages import (
    ApplyPropertyToPagesUseCase,
)


# ---------------------------------------------------------------------------
# Helpers – lightweight stand-ins so we don't need PySide at test time
# ---------------------------------------------------------------------------


@dataclass
class _PropertyLike:
    """Mimics PropertyData from the UI layer (type stored as a string key)."""

    id: str
    name: str
    type: str
    value: object
    mandatory: bool = False


def _build_save_page(vault_path: Path):
    """Build the same save_page callable the ControllerFactory creates."""
    from fern.domain.entities.properties import PropertyType
    from fern.interface_adapters.repositories.markdown_page_repository import (
        MarkdownPageRepository,
    )

    def save_page(
        vp: Path,
        database_name: str,
        page_id: int,
        title: str,
        content: str,
        properties: list | None = None,
    ) -> None:
        db_dir = Path(vp) / database_name
        repo = MarkdownPageRepository(db_dir)
        domain_props = None
        if properties is not None:
            domain_props = []
            for page_property in properties:
                property_id = getattr(page_property, "id", "")
                if property_id in ("id", "title"):
                    continue
                property_type_key = getattr(page_property, "type", "string")
                if not isinstance(property_type_key, str):
                    property_type_key = "string"
                property_type = PropertyType.from_key(property_type_key)
                domain_props.append(
                    property_type.create(
                        id=property_id,
                        name=getattr(page_property, "name", property_id),
                        value=getattr(page_property, "value", None),
                    )
                )
        repo.update(page_id, title, content, properties=domain_props)

    return save_page


def _setup_database(
    tmp_path: Path, db_name: str = "mydb"
) -> tuple[Path, MarkdownPageRepository]:
    """Create a database folder with a marker and return (vault_path, repo)."""
    db_dir = tmp_path / db_name
    db_dir.mkdir()
    (db_dir / "database.json").write_text(
        json.dumps({"properties": [], "propertyOrder": []}), encoding="utf-8"
    )
    return tmp_path, MarkdownPageRepository(db_dir)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSavePagePersistsProperties:
    """Ensure save_page writes properties into the markdown frontmatter."""

    def test_properties_written_to_disk(self, tmp_path: Path) -> None:
        vault, repo = _setup_database(tmp_path)
        page = repo.create("Test Page", "body")
        assert page.properties == []

        save = _build_save_page(vault)
        props = [
            _PropertyLike(id="id", name="ID", type="id", value=page.id, mandatory=True),
            _PropertyLike(
                id="title",
                name="Title",
                type="title",
                value="Test Page",
                mandatory=True,
            ),
            _PropertyLike(id="done", name="Done", type="boolean", value=True),
            _PropertyLike(id="note", name="Note", type="string", value="hello"),
        ]
        save(vault, "mydb", page.id, "Test Page", "body", props)

        reloaded = repo.get_by_id(page.id)
        assert reloaded is not None
        assert len(reloaded.properties) == 2
        by_id = {p.id: p for p in reloaded.properties}
        assert by_id["done"].value is True
        assert by_id["note"].value == "hello"

    def test_properties_none_preserves_existing(self, tmp_path: Path) -> None:
        """When properties=None the existing on-disk properties must survive."""
        vault, repo = _setup_database(tmp_path)
        page = repo.create("Page", "")
        repo.update(
            page.id,
            "Page",
            "",
            properties=[
                StringProperty(id="status", name="Status", value="draft"),
            ],
        )

        save = _build_save_page(vault)
        save(vault, "mydb", page.id, "Page", "updated body", None)

        reloaded = repo.get_by_id(page.id)
        assert reloaded is not None
        assert reloaded.content == "updated body"
        assert len(reloaded.properties) == 1
        assert reloaded.properties[0].id == "status"
        assert reloaded.properties[0].value == "draft"

    def test_mandatory_props_stripped_from_disk(self, tmp_path: Path) -> None:
        """id and title pseudo-properties must not be written as real properties."""
        vault, repo = _setup_database(tmp_path)
        page = repo.create("P", "")

        save = _build_save_page(vault)
        props = [
            _PropertyLike(id="id", name="ID", type="id", value=1, mandatory=True),
            _PropertyLike(
                id="title", name="Title", type="title", value="P", mandatory=True
            ),
            _PropertyLike(id="flag", name="Flag", type="boolean", value=False),
        ]
        save(vault, "mydb", page.id, "P", "", props)

        reloaded = repo.get_by_id(page.id)
        assert reloaded is not None
        prop_ids = [p.id for p in reloaded.properties]
        assert "id" not in prop_ids
        assert "title" not in prop_ids
        assert "flag" in prop_ids

    def test_empty_properties_list_clears_on_disk(self, tmp_path: Path) -> None:
        """Passing an empty list should remove all properties from the file."""
        vault, repo = _setup_database(tmp_path)
        page = repo.create("P", "")
        repo.update(
            page.id,
            "P",
            "",
            properties=[
                BooleanProperty(id="x", name="X", value=True),
            ],
        )
        assert len(repo.get_by_id(page.id).properties) == 1

        save = _build_save_page(vault)
        save(vault, "mydb", page.id, "P", "", [])

        reloaded = repo.get_by_id(page.id)
        assert reloaded is not None
        assert reloaded.properties == []

    def test_save_roundtrip_multiple_types(self, tmp_path: Path) -> None:
        """Boolean and string properties survive a save → reload cycle."""
        vault, repo = _setup_database(tmp_path)
        page = repo.create("Multi", "content")

        save = _build_save_page(vault)
        props = [
            _PropertyLike(id="done", name="Done", type="boolean", value=False),
            _PropertyLike(id="tag", name="Tag", type="string", value="urgent"),
        ]
        save(vault, "mydb", page.id, "Multi", "content", props)

        reloaded = repo.get_by_id(page.id)
        assert reloaded is not None
        by_id = {p.id: p for p in reloaded.properties}
        assert by_id["done"].value is False
        assert by_id["done"].type_key() == "boolean"
        assert by_id["tag"].value == "urgent"
        assert by_id["tag"].type_key() == "string"

    def test_save_preserves_content_and_title(self, tmp_path: Path) -> None:
        """Properties save must not corrupt title or content."""
        vault, repo = _setup_database(tmp_path)
        page = repo.create("Original", "original body")

        save = _build_save_page(vault)
        props = [
            _PropertyLike(id="p1", name="P1", type="boolean", value=True),
        ]
        save(vault, "mydb", page.id, "Renamed", "new body", props)

        reloaded = repo.get_by_id(page.id)
        assert reloaded is not None
        assert reloaded.title == "Renamed"
        assert reloaded.content == "new body"
        assert len(reloaded.properties) == 1

    def test_frontmatter_on_disk_contains_properties(self, tmp_path: Path) -> None:
        """Directly read the .md file to confirm properties are in YAML frontmatter."""
        vault, repo = _setup_database(tmp_path)
        page = repo.create("Check", "")

        save = _build_save_page(vault)
        props = [
            _PropertyLike(id="rating", name="Rating", type="string", value="5"),
        ]
        save(vault, "mydb", page.id, "Check", "", props)

        md_file = tmp_path / "mydb" / "Check.md"
        assert md_file.exists()
        post = frontmatter.loads(md_file.read_text(encoding="utf-8"))
        raw_props = post.get("properties")
        assert isinstance(raw_props, list)
        assert len(raw_props) == 1
        assert raw_props[0]["id"] == "rating"
        assert raw_props[0]["value"] == "5"


# ---------------------------------------------------------------------------
# Regression: add_property must update schema AND every page's frontmatter
# ---------------------------------------------------------------------------


def _setup_database_with_schema(
    tmp_path: Path,
    db_name: str = "mydb",
) -> tuple[Path, Path]:
    """Create a vault with a database folder, marker, and return (vault_path, db_dir)."""
    db_dir = tmp_path / db_name
    db_dir.mkdir()
    (db_dir / "database.json").write_text(
        json.dumps({"properties": [], "propertyOrder": []}),
        encoding="utf-8",
    )
    return tmp_path, db_dir


class TestAddPropertyUpdatesFiles:
    """Ensure the full add_property flow writes the new property into every page's frontmatter."""

    def test_add_property_writes_to_all_pages(self, tmp_path: Path) -> None:
        vault, db_dir = _setup_database_with_schema(tmp_path)
        repo = MarkdownPageRepository(db_dir)
        repo.create("Page A", "content a")
        repo.create("Page B", "content b")

        db_repo = VaultDatabaseRepository(vault)

        schema_uc = AddPropertyUseCase(db_repo)
        schema_uc.execute(
            AddPropertyInputDTO(
                database_name="mydb",
                property=BooleanPropertyInputDTO(
                    property_id="done",
                    name="Done",
                ),
            )
        )

        apply_uc = ApplyPropertyToPagesUseCase(repo)
        apply_uc.execute(
            ApplyPropertyToPagesInputDTO(
                property_id="done",
                name="Done",
                type_key="boolean",
            )
        )

        for page in repo.list_all():
            prop_ids = [p.id for p in page.properties]
            assert "done" in prop_ids, f"Page '{page.title}' missing 'done' property"
            done_prop = next(p for p in page.properties if p.id == "done")
            assert done_prop.value is False

        schema_raw = json.loads((db_dir / "database.json").read_text())
        schema_ids = [p["id"] for p in schema_raw["properties"]]
        assert "done" in schema_ids

    def test_add_property_writes_frontmatter_on_disk(self, tmp_path: Path) -> None:
        """Read the raw .md files to confirm the property is in YAML frontmatter."""
        vault, db_dir = _setup_database_with_schema(tmp_path)
        repo = MarkdownPageRepository(db_dir)
        repo.create("Only Page", "body")

        db_repo = VaultDatabaseRepository(vault)

        AddPropertyUseCase(db_repo).execute(
            AddPropertyInputDTO(
                database_name="mydb",
                property=StringPropertyInputDTO(
                    property_id="tag",
                    name="Tag",
                ),
            )
        )
        ApplyPropertyToPagesUseCase(repo).execute(
            ApplyPropertyToPagesInputDTO(
                property_id="tag",
                name="Tag",
                type_key="string",
            )
        )

        md_file = db_dir / "Only Page.md"
        post = frontmatter.loads(md_file.read_text(encoding="utf-8"))
        raw_props = post.get("properties")
        assert isinstance(raw_props, list)
        prop_ids = [p["id"] for p in raw_props]
        assert "tag" in prop_ids

    def test_add_property_preserves_existing_properties(self, tmp_path: Path) -> None:
        vault, db_dir = _setup_database_with_schema(tmp_path)
        repo = MarkdownPageRepository(db_dir)
        page = repo.create("Page", "")
        repo.update(
            page.id,
            "Page",
            "",
            properties=[BooleanProperty(id="old", name="Old", value=True)],
        )

        db_repo = VaultDatabaseRepository(vault)

        AddPropertyUseCase(db_repo).execute(
            AddPropertyInputDTO(
                database_name="mydb",
                property=StringPropertyInputDTO(
                    property_id="new_prop",
                    name="New",
                ),
            )
        )
        ApplyPropertyToPagesUseCase(repo).execute(
            ApplyPropertyToPagesInputDTO(
                property_id="new_prop",
                name="New",
                type_key="string",
            )
        )

        reloaded = repo.get_by_id(page.id)
        assert reloaded is not None
        prop_ids = [p.id for p in reloaded.properties]
        assert "old" in prop_ids, "Existing property 'old' was lost"
        assert "new_prop" in prop_ids, "New property 'new_prop' not added"
        old_prop = next(p for p in reloaded.properties if p.id == "old")
        assert old_prop.value is True

    def test_add_property_to_empty_database(self, tmp_path: Path) -> None:
        """Adding a property when there are no pages should not error."""
        vault, db_dir = _setup_database_with_schema(tmp_path)
        repo = MarkdownPageRepository(db_dir)
        db_repo = VaultDatabaseRepository(vault)

        AddPropertyUseCase(db_repo).execute(
            AddPropertyInputDTO(
                database_name="mydb",
                property=BooleanPropertyInputDTO(
                    property_id="flag",
                    name="Flag",
                ),
            )
        )
        ApplyPropertyToPagesUseCase(repo).execute(
            ApplyPropertyToPagesInputDTO(
                property_id="flag",
                name="Flag",
                type_key="boolean",
            )
        )

        assert repo.list_all() == []
        schema_raw = json.loads((db_dir / "database.json").read_text())
        assert any(p["id"] == "flag" for p in schema_raw["properties"])
