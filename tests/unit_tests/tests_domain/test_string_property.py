"""Unit tests for StringProperty type."""

from fern.domain.entities import StringProperty


def _make_string(**kwargs) -> StringProperty:
    defaults = {"id": "test", "name": "Test"}
    return StringProperty(**{**defaults, **kwargs})


def test_string_property_type_key() -> None:
    assert _make_string().type_key() == "string"


def test_string_property_default_value() -> None:
    assert _make_string().default_value() == ""


def test_string_property_validate_accepts_str() -> None:
    prop = _make_string()
    assert prop.validate("hello") is True
    assert prop.validate("") is True


def test_string_property_validate_rejects_non_str() -> None:
    prop = _make_string()
    assert prop.validate(123) is False
    assert prop.validate(True) is False
    assert prop.validate(None) is False


def test_string_property_coerce_none_to_empty() -> None:
    assert _make_string().coerce(None) == ""


def test_string_property_coerce_str_unchanged() -> None:
    assert _make_string().coerce("hi") == "hi"


def test_string_property_coerce_non_str_converted() -> None:
    assert _make_string().coerce(42) == "42"
