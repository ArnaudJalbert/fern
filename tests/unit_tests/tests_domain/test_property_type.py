"""Unit tests for PropertyType enum."""

import pytest

from fern.domain.entities import PropertyType


def test_property_type_key_boolean() -> None:
    assert PropertyType.BOOLEAN.key() == "boolean"


def test_property_type_key_string() -> None:
    assert PropertyType.STRING.key() == "string"


def test_property_type_key_id() -> None:
    assert PropertyType.ID.key() == "id"


def test_property_type_key_title() -> None:
    assert PropertyType.TITLE.key() == "title"


def test_property_type_key_status() -> None:
    assert PropertyType.STATUS.key() == "status"


def test_property_type_from_key_boolean() -> None:
    assert PropertyType.from_key("boolean") == PropertyType.BOOLEAN


def test_property_type_from_key_string() -> None:
    assert PropertyType.from_key("string") == PropertyType.STRING


def test_property_type_from_key_id() -> None:
    assert PropertyType.from_key("id") == PropertyType.ID


def test_property_type_from_key_title() -> None:
    assert PropertyType.from_key("title") == PropertyType.TITLE


def test_property_type_from_key_status() -> None:
    assert PropertyType.from_key("status") == PropertyType.STATUS


def test_property_type_from_key_unknown_raises() -> None:
    with pytest.raises(ValueError, match="Invalid property type key 'unknown'"):
        PropertyType.from_key("unknown")


def test_property_type_from_key_empty_raises() -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        PropertyType.from_key("")
    with pytest.raises(ValueError, match="cannot be empty"):
        PropertyType.from_key("  ")


def test_property_type_from_key_none_raises() -> None:
    with pytest.raises(ValueError, match="required"):
        PropertyType.from_key(None)


def test_property_type_from_key_case_insensitive() -> None:
    assert PropertyType.from_key("STRING") == PropertyType.STRING
    assert PropertyType.from_key("Boolean") == PropertyType.BOOLEAN
    assert PropertyType.from_key("ID") == PropertyType.ID
    assert PropertyType.from_key("Title") == PropertyType.TITLE


def test_property_type_user_creatable() -> None:
    creatable = PropertyType.user_creatable()
    assert PropertyType.BOOLEAN in creatable
    assert PropertyType.STRING in creatable
    assert PropertyType.STATUS in creatable
    assert PropertyType.ID not in creatable
    assert PropertyType.TITLE not in creatable
    assert len(creatable) == 3


def test_property_type_create_returns_instance() -> None:
    prop = PropertyType.BOOLEAN.create(id="p1", name="Done")
    assert prop.id == "p1"
    assert prop.name == "Done"
    assert prop.type_key() == "boolean"


def test_property_type_default_value_for_type() -> None:
    assert PropertyType.BOOLEAN.default_value_for_type() is False
    assert PropertyType.STRING.default_value_for_type() == ""
    assert PropertyType.STATUS.default_value_for_type() == ""
