"""Unit tests for TitleProperty type."""

from fern.domain.entities import TitleProperty


def _make_title(**kwargs) -> TitleProperty:
    defaults = {"id": "title", "name": "Title"}
    return TitleProperty(**{**defaults, **kwargs})


def test_title_property_type_key() -> None:
    assert _make_title().type_key() == "title"


def test_title_property_default_value() -> None:
    assert _make_title().default_value() == ""


def test_title_property_validate_accepts_str() -> None:
    prop = _make_title()
    assert prop.validate("hello") is True
    assert prop.validate("") is True


def test_title_property_validate_rejects_non_str() -> None:
    prop = _make_title()
    assert prop.validate(123) is False
    assert prop.validate(None) is False


def test_title_property_coerce_none_to_empty() -> None:
    assert _make_title().coerce(None) == ""


def test_title_property_coerce_str_unchanged() -> None:
    assert _make_title().coerce("hi") == "hi"


def test_title_property_coerce_non_str_converted() -> None:
    assert _make_title().coerce(42) == "42"
