"""Unit tests for Property entity."""

from fern.domain.entities import BooleanProperty, IdProperty, StringProperty


def test_property_create_minimal() -> None:
    p = BooleanProperty(id="x", name="X")
    assert p.id == "x"
    assert p.name == "X"
    assert p.type_key() == "boolean"
    assert p.value is False
    assert p.mandatory is False


def test_property_create_with_value() -> None:
    p = StringProperty(id="y", name="Y", value="hello")
    assert p.value == "hello"


def test_property_mandatory_flag() -> None:
    p = IdProperty(id="id", name="ID")
    assert p.mandatory is True
