"""Unit tests for TitleProperty type."""

from fern.domain.entities import TitleProperty


def test_title_property_type_key() -> None:
    assert TitleProperty.TYPE_KEY == "title"


def test_title_property_default_value() -> None:
    assert TitleProperty.default_value() == ""


def test_title_property_validate_accepts_str() -> None:
    assert TitleProperty.validate("hello") is True
    assert TitleProperty.validate("") is True


def test_title_property_validate_rejects_non_str() -> None:
    assert TitleProperty.validate(123) is False
    assert TitleProperty.validate(None) is False


def test_title_property_coerce_none_to_empty() -> None:
    assert TitleProperty.coerce(None) == ""


def test_title_property_coerce_str_unchanged() -> None:
    assert TitleProperty.coerce("hi") == "hi"


def test_title_property_coerce_non_str_converted() -> None:
    assert TitleProperty.coerce(42) == "42"
