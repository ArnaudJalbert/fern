"""Unit tests for property_factory (build_property_from_dto, build_property_from_type, build_choices_from_dtos)."""

from fern.application.dtos import (
    ChoiceDTO,
    BooleanPropertyInputDTO,
    StatusPropertyInputDTO,
    StringPropertyInputDTO,
)
from fern.application.property_factory import (
    build_choices_from_dtos,
    build_property_from_dto,
    build_property_from_type,
)
from fern.domain.entities import PropertyType, StatusProperty


def test_build_property_from_dto_status_with_choices() -> None:
    dto = StatusPropertyInputDTO(
        property_id="s1",
        name="Status",
        choices=(
            ChoiceDTO(name="Done", category="cat1", color="#0f0"),
            ChoiceDTO(name="Todo", category="cat1", color="#00f"),
        ),
    )
    prop = build_property_from_dto(dto)
    assert isinstance(prop, StatusProperty)
    assert prop.id == "s1"
    assert prop.name == "Status"
    assert len(prop.choices) == 2
    assert prop.choices[0].name == "Done"
    assert prop.choices[1].name == "Todo"


def test_build_property_from_dto_string() -> None:
    dto = StringPropertyInputDTO(property_id="p1", name="Note")
    prop = build_property_from_dto(dto)
    assert prop.id == "p1"
    assert prop.type_key() == "string"


def test_build_property_from_dto_boolean_fallback() -> None:
    dto = BooleanPropertyInputDTO(property_id="p1", name="Done")
    prop = build_property_from_dto(dto)
    assert prop.id == "p1"
    assert prop.type_key() == "boolean"


def test_build_property_from_type_status_with_choices() -> None:
    from fern.domain.entities import Choice
    from fern.domain.entities.properties.choice_category import ChoiceCategory

    choices = [
        Choice(name="Done", category=ChoiceCategory(name="c1"), color="#0f0"),
    ]
    prop = build_property_from_type(
        property_id="s1",
        name="Status",
        property_type=PropertyType.STATUS,
        choices=choices,
    )
    assert isinstance(prop, StatusProperty)
    assert prop.id == "s1"
    assert prop.name == "Status"
    assert len(prop.choices) == 1
    assert prop.choices[0].name == "Done"


def test_build_property_from_type_status_without_choices() -> None:
    prop = build_property_from_type(
        property_id="s1",
        name="Status",
        property_type=PropertyType.STATUS,
    )
    assert isinstance(prop, StatusProperty)
    assert prop.choices == []


def test_build_property_from_type_non_status_uses_create() -> None:
    prop = build_property_from_type(
        property_id="p1",
        name="Done",
        property_type=PropertyType.BOOLEAN,
    )
    assert prop.type_key() == "boolean"
    assert prop.id == "p1"


def test_build_choices_from_dtos_none_returns_empty() -> None:
    assert build_choices_from_dtos(None) == []


def test_build_choices_from_dtos_empty_tuple_returns_empty() -> None:
    assert build_choices_from_dtos(()) == []


def test_build_choices_from_dtos_non_empty_returns_choices() -> None:
    choice_dtos = (
        ChoiceDTO(name="A", category="c1", color="#f00"),
        ChoiceDTO(name="B", category="c2", color="#0f0"),
    )
    result = build_choices_from_dtos(choice_dtos)
    assert len(result) == 2
    assert result[0].name == "A"
    assert result[0].color == "#f00"
    assert result[1].name == "B"
    assert result[1].category == "c2"
