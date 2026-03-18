"""Unit tests for Page entity."""

from fern.domain.entities import BooleanProperty, Page


def test_page_create_minimal() -> None:
    p = Page(id=1, title="Foo", content="bar")
    assert p.id == 1
    assert p.title == "Foo"
    assert p.content == "bar"
    assert p.properties == []


def test_page_create_with_properties() -> None:
    prop = BooleanProperty(id="p1", name="Done", value=True)
    p = Page(id=2, title="Task", content="", properties=[prop])
    assert len(p.properties) == 1
    assert p.properties[0].id == "p1"
