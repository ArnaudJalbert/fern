"""Unit tests for IdProperty type."""

from fern.domain.entities import IdProperty


def test_id_property_type_key() -> None:
    assert IdProperty.TYPE_KEY == "id"


def test_id_property_default_value() -> None:
    assert IdProperty.default_value() == 0


def test_id_property_validate_accepts_int() -> None:
    assert IdProperty.validate(42) is True
    assert IdProperty.validate(0) is True


def test_id_property_validate_rejects_non_int() -> None:
    assert IdProperty.validate("42") is False
    assert IdProperty.validate(3.14) is False
    assert IdProperty.validate(None) is False


def test_id_property_coerce_int_unchanged() -> None:
    assert IdProperty.coerce(42) == 42


def test_id_property_coerce_string_to_int() -> None:
    assert IdProperty.coerce("123") == 123


def test_id_property_coerce_invalid_returns_zero() -> None:
    assert IdProperty.coerce("abc") == 0
    assert IdProperty.coerce(None) == 0
