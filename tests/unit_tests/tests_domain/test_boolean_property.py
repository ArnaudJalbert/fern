"""Unit tests for BooleanProperty type."""

from fern.domain.entities import BooleanProperty


def _make_boolean(**kwargs) -> BooleanProperty:
    defaults = {"id": "test", "name": "Test"}
    return BooleanProperty(**{**defaults, **kwargs})


def test_boolean_property_type_key() -> None:
    assert _make_boolean().type_key() == "boolean"


def test_boolean_property_default_value() -> None:
    assert _make_boolean().default_value() is False


def test_boolean_property_validate_accepts_bool() -> None:
    prop = _make_boolean()
    assert prop.validate(True) is True
    assert prop.validate(False) is True


def test_boolean_property_validate_rejects_non_bool() -> None:
    prop = _make_boolean()
    assert prop.validate(1) is False
    assert prop.validate("true") is False


def test_boolean_property_coerce_bool_unchanged() -> None:
    prop = _make_boolean()
    assert prop.coerce(True) is True
    assert prop.coerce(False) is False


def test_boolean_property_coerce_string_true() -> None:
    prop = _make_boolean()
    assert prop.coerce("true") is True
    assert prop.coerce("TRUE") is True
    assert prop.coerce("1") is True
    assert prop.coerce("yes") is True


def test_boolean_property_coerce_string_false() -> None:
    prop = _make_boolean()
    assert prop.coerce("false") is False
    assert prop.coerce("0") is False
    assert prop.coerce("no") is False


def test_boolean_property_coerce_other_boolified() -> None:
    prop = _make_boolean()
    assert prop.coerce(1) is True
    assert prop.coerce(0) is False
