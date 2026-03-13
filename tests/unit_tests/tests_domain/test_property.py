"""Unit tests for Property entity."""

from fern.domain.entities import Property, PropertyType


def test_property_create_minimal() -> None:
    p = Property(id="x", name="X", type=PropertyType.BOOLEAN)
    assert p.id == "x"
    assert p.name == "X"
    assert p.type == PropertyType.BOOLEAN
    assert p.value is None
    assert p.mandatory is False


def test_property_create_with_value() -> None:
    p = Property(id="y", name="Y", type=PropertyType.STRING, value="hello")
    assert p.value == "hello"


def test_property_mandatory_flag() -> None:
    p = Property(id="id", name="ID", type=PropertyType.ID, mandatory=True)
    assert p.mandatory is True
