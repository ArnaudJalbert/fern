"""Unit tests for StatusProperty."""


from fern.domain.entities import StatusProperty


def test_status_property_type_key() -> None:
    prop = StatusProperty(id="s1", name="Status", choices=[])
    assert prop.type_key() == "status"


def test_status_property_default_value() -> None:
    prop = StatusProperty(id="s1", name="Status", choices=[])
    assert prop.default_value() == ""


def test_status_property_validate_accepts_str() -> None:
    prop = StatusProperty(id="s1", name="Status", choices=[])
    assert prop.validate("") is True
    assert prop.validate("Done") is True


def test_status_property_validate_rejects_non_str() -> None:
    prop = StatusProperty(id="s1", name="Status", choices=[])
    assert prop.validate(123) is False
    assert prop.validate(None) is False


def test_status_property_coerce_none_to_empty() -> None:
    prop = StatusProperty(id="s1", name="Status", choices=[])
    assert prop.coerce(None) == ""


def test_status_property_coerce_non_str_converted() -> None:
    prop = StatusProperty(id="s1", name="Status", choices=[])
    assert prop.coerce(42) == "42"
    assert prop.coerce(True) == "True"
