"""Unit tests for StringProperty type."""

from fern.domain.entities import StringProperty


def test_string_property_type_key() -> None:
    assert StringProperty.TYPE_KEY == "string"


def test_string_property_default_value() -> None:
    assert StringProperty.default_value() == ""


def test_string_property_validate_accepts_str() -> None:
    assert StringProperty.validate("hello") is True
    assert StringProperty.validate("") is True


def test_string_property_validate_rejects_non_str() -> None:
    assert StringProperty.validate(123) is False
    assert StringProperty.validate(True) is False
    assert StringProperty.validate(None) is False


def test_string_property_coerce_none_to_empty() -> None:
    assert StringProperty.coerce(None) == ""


def test_string_property_coerce_str_unchanged() -> None:
    assert StringProperty.coerce("hi") == "hi"


def test_string_property_coerce_non_str_converted() -> None:
    assert StringProperty.coerce(42) == "42"
