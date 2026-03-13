"""Unit tests for BooleanProperty type."""

from fern.domain.entities import BooleanProperty


def test_boolean_property_type_key() -> None:
    assert BooleanProperty.TYPE_KEY == "boolean"


def test_boolean_property_default_value() -> None:
    assert BooleanProperty.default_value() is False


def test_boolean_property_validate_accepts_bool() -> None:
    assert BooleanProperty.validate(True) is True
    assert BooleanProperty.validate(False) is True


def test_boolean_property_validate_rejects_non_bool() -> None:
    assert BooleanProperty.validate(1) is False
    assert BooleanProperty.validate("true") is False


def test_boolean_property_coerce_bool_unchanged() -> None:
    assert BooleanProperty.coerce(True) is True
    assert BooleanProperty.coerce(False) is False


def test_boolean_property_coerce_string_true() -> None:
    assert BooleanProperty.coerce("true") is True
    assert BooleanProperty.coerce("TRUE") is True
    assert BooleanProperty.coerce("1") is True
    assert BooleanProperty.coerce("yes") is True


def test_boolean_property_coerce_string_false() -> None:
    assert BooleanProperty.coerce("false") is False
    assert BooleanProperty.coerce("0") is False
    assert BooleanProperty.coerce("no") is False


def test_boolean_property_coerce_other_boolified() -> None:
    assert BooleanProperty.coerce(1) is True
    assert BooleanProperty.coerce(0) is False
