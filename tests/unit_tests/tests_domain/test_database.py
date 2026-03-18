"""Unit tests for Database entity."""

from fern.domain.entities import Database, Page, StringProperty


def test_database_create_minimal() -> None:
    db = Database(name="Inbox")
    assert db.name == "Inbox"
    assert db.pages == []
    assert db.properties == []
    assert db.property_order == []


def test_database_create_with_pages_and_schema() -> None:
    page = Page(id=1, title="P", content="")
    prop = StringProperty(id="p1", name="Status")
    db = Database(
        name="Notes",
        pages=[page],
        properties=[prop],
        property_order=["p1"],
    )
    assert db.name == "Notes"
    assert len(db.pages) == 1
    assert len(db.properties) == 1
    assert db.property_order == ["p1"]
