"""Unit tests for PropertyType enum."""

from fern.domain.entities import PropertyType


def test_property_type_key_boolean() -> None:
    assert PropertyType.BOOLEAN.key() == "boolean"


def test_property_type_key_string() -> None:
    assert PropertyType.STRING.key() == "string"


def test_property_type_key_id() -> None:
    assert PropertyType.ID.key() == "id"


def test_property_type_key_title() -> None:
    assert PropertyType.TITLE.key() == "title"


def test_property_type_from_key_boolean() -> None:
    assert PropertyType.from_key("boolean") == PropertyType.BOOLEAN


def test_property_type_from_key_string() -> None:
    assert PropertyType.from_key("string") == PropertyType.STRING


def test_property_type_from_key_id() -> None:
    assert PropertyType.from_key("id") == PropertyType.ID


def test_property_type_from_key_title() -> None:
    assert PropertyType.from_key("title") == PropertyType.TITLE


def test_property_type_from_key_unknown_defaults_to_boolean() -> None:
    assert PropertyType.from_key("unknown") == PropertyType.BOOLEAN
    assert PropertyType.from_key("") == PropertyType.BOOLEAN
    assert PropertyType.from_key("  ") == PropertyType.BOOLEAN


def test_property_type_from_key_case_insensitive() -> None:
    assert PropertyType.from_key("STRING") == PropertyType.STRING
    assert PropertyType.from_key("Boolean") == PropertyType.BOOLEAN
    assert PropertyType.from_key("ID") == PropertyType.ID
    assert PropertyType.from_key("Title") == PropertyType.TITLE


def test_property_type_user_creatable() -> None:
    creatable = PropertyType.user_creatable()
    assert PropertyType.BOOLEAN in creatable
    assert PropertyType.STRING in creatable
    assert PropertyType.ID not in creatable
    assert PropertyType.TITLE not in creatable
    assert len(creatable) == 2
