"""Unit tests for IdProperty type."""

from fern.domain.entities import IdProperty


def _make_id(**kwargs) -> IdProperty:
    defaults = {"id": "id", "name": "ID"}
    return IdProperty(**{**defaults, **kwargs})


def test_id_property_type_key() -> None:
    assert _make_id().type_key() == "id"


def test_id_property_default_value() -> None:
    assert _make_id().default_value() == 0


def test_id_property_validate_accepts_int() -> None:
    prop = _make_id()
    assert prop.validate(42) is True
    assert prop.validate(0) is True


def test_id_property_validate_rejects_non_int() -> None:
    prop = _make_id()
    assert prop.validate("42") is False
    assert prop.validate(3.14) is False
    assert prop.validate(None) is False


def test_id_property_coerce_int_unchanged() -> None:
    assert _make_id().coerce(42) == 42


def test_id_property_coerce_string_to_int() -> None:
    assert _make_id().coerce("123") == 123


def test_id_property_coerce_invalid_returns_zero() -> None:
    prop = _make_id()
    assert prop.coerce("abc") == 0
    assert prop.coerce(None) == 0
