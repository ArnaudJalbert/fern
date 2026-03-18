"""Unit tests for UpdatePropertyUseCase."""

import pytest
from unittest.mock import MagicMock, patch

from fern.application.dtos import ChoiceDTO, UpdatePropertyInputDTO
from fern.application.errors import PropertyNotFoundError
from fern.application.use_cases.update_property import UpdatePropertyUseCase
from fern.domain.entities import BooleanProperty, Page, StatusProperty, StringProperty


def test_update_property_success() -> None:
    prop = StringProperty(id="p1", name="Old")
    db_repo = MagicMock()
    db_repo.get_schema.return_value = ([prop], ["p1"])
    page_repo = MagicMock()
    page_repo.list_all.return_value = []

    use_case = UpdatePropertyUseCase(
        database_repository=db_repo, page_repository=page_repo
    )
    use_case.execute(
        UpdatePropertyInputDTO(
            database_name="DB",
            property_id="p1",
            new_name="New Name",
            new_type_key="boolean",
        )
    )

    db_repo.save_schema.assert_called_once()
    call_args = db_repo.save_schema.call_args[0]
    assert call_args[1][0].name == "New Name"
    assert call_args[1][0].type_key() == "boolean"


def test_update_property_not_found_fails() -> None:
    db_repo = MagicMock()
    db_repo.get_schema.return_value = ([], [])
    page_repo = MagicMock()

    use_case = UpdatePropertyUseCase(
        database_repository=db_repo, page_repository=page_repo
    )
    with pytest.raises(PropertyNotFoundError):
        use_case.execute(
            UpdatePropertyInputDTO(database_name="DB", property_id="p1", new_name="X")
        )

    db_repo.save_schema.assert_not_called()


def test_update_property_name_only() -> None:
    prop = StringProperty(id="p1", name="Old")
    db_repo = MagicMock()
    db_repo.get_schema.return_value = ([prop], ["p1"])
    page_repo = MagicMock()
    page_repo.list_all.return_value = []

    use_case = UpdatePropertyUseCase(
        database_repository=db_repo, page_repository=page_repo
    )
    use_case.execute(
        UpdatePropertyInputDTO(database_name="DB", property_id="p1", new_name="New")
    )

    saved_prop = db_repo.save_schema.call_args[0][1][0]
    assert saved_prop.name == "New"
    assert saved_prop.type_key() == "string"


def test_update_property_coerces_page_values() -> None:
    prop = StringProperty(id="p1", name="Done")
    db_repo = MagicMock()
    db_repo.get_schema.return_value = ([prop], ["p1"])
    page_prop = StringProperty(id="p1", name="Done", value="true")
    page = Page(id=1, title="T", content="", properties=[page_prop])
    page_repo = MagicMock()
    page_repo.list_all.return_value = [page]

    use_case = UpdatePropertyUseCase(
        database_repository=db_repo, page_repository=page_repo
    )
    use_case.execute(
        UpdatePropertyInputDTO(
            database_name="DB", property_id="p1", new_type_key="boolean"
        )
    )

    updated_props = page_repo.update.call_args[1]["properties"]
    assert updated_props[0].value is True
    assert updated_props[0].type_key() == "boolean"


def test_update_property_empty_name_keeps_old() -> None:
    prop = StringProperty(id="p1", name="Old")
    db_repo = MagicMock()
    db_repo.get_schema.return_value = ([prop], ["p1"])
    page_repo = MagicMock()
    page_repo.list_all.return_value = []

    use_case = UpdatePropertyUseCase(
        database_repository=db_repo, page_repository=page_repo
    )
    use_case.execute(
        UpdatePropertyInputDTO(database_name="DB", property_id="p1", new_name="  ")
    )

    saved_prop = db_repo.save_schema.call_args[0][1][0]
    assert saved_prop.name == "Old"


def test_update_property_page_with_other_properties_preserved() -> None:
    prop = StringProperty(id="p1", name="Old")
    db_repo = MagicMock()
    db_repo.get_schema.return_value = ([prop], ["p1"])
    other_prop = BooleanProperty(id="p2", name="Other", value=True)
    page_prop = StringProperty(id="p1", name="Old", value="hi")
    page = Page(id=1, title="T", content="", properties=[page_prop, other_prop])
    page_repo = MagicMock()
    page_repo.list_all.return_value = [page]

    use_case = UpdatePropertyUseCase(
        database_repository=db_repo, page_repository=page_repo
    )
    use_case.execute(
        UpdatePropertyInputDTO(database_name="DB", property_id="p1", new_name="New")
    )

    updated_props = page_repo.update.call_args[1]["properties"]
    assert len(updated_props) == 2
    assert updated_props[0].name == "New"
    assert updated_props[1].id == "p2"
    assert updated_props[1].value is True


def test_update_property_empty_type_keeps_old() -> None:
    prop = StringProperty(id="p1", name="X")
    db_repo = MagicMock()
    db_repo.get_schema.return_value = ([prop], ["p1"])
    page_repo = MagicMock()
    page_repo.list_all.return_value = []

    use_case = UpdatePropertyUseCase(
        database_repository=db_repo, page_repository=page_repo
    )
    use_case.execute(
        UpdatePropertyInputDTO(database_name="DB", property_id="p1", new_type_key="  ")
    )

    saved_prop = db_repo.save_schema.call_args[0][1][0]
    assert saved_prop.type_key() == "string"


def test_update_property_uses_default_value_when_coerced_value_is_none() -> None:
    """When updating property type, if coerced value is None, use type's default_value()."""
    prop = StringProperty(id="p1", name="Done")
    db_repo = MagicMock()
    db_repo.get_schema.return_value = ([prop], ["p1"])
    page_prop = StringProperty(id="p1", name="Done", value=None)
    page = Page(id=1, title="T", content="", properties=[page_prop])
    page_repo = MagicMock()
    page_repo.list_all.return_value = [page]

    with patch(
        "fern.domain.entities.properties.boolean.BooleanProperty.coerce",
        return_value=None,
    ):
        use_case = UpdatePropertyUseCase(
            database_repository=db_repo, page_repository=page_repo
        )
        use_case.execute(
            UpdatePropertyInputDTO(
                database_name="DB", property_id="p1", new_type_key="boolean"
            )
        )

    updated_props = page_repo.update.call_args[1]["properties"]
    assert updated_props[0].value is False
    assert updated_props[0].type_key() == "boolean"


def test_update_property_to_status_with_new_choices_uses_new_choices() -> None:
    """When changing to status and providing new_choices, they are used."""
    prop = StringProperty(id="p1", name="Status")
    db_repo = MagicMock()
    db_repo.get_schema.return_value = ([prop], ["p1"])
    page_repo = MagicMock()
    page_repo.list_all.return_value = []

    use_case = UpdatePropertyUseCase(
        database_repository=db_repo, page_repository=page_repo
    )
    use_case.execute(
        UpdatePropertyInputDTO(
            database_name="DB",
            property_id="p1",
            new_name="Stage",
            new_type_key="status",
            new_choices=(
                ChoiceDTO(name="A", category="c1", color="#f00"),
                ChoiceDTO(name="B", category="c1", color="#0f0"),
            ),
        )
    )

    saved_schema = db_repo.save_schema.call_args[0][1]
    assert len(saved_schema) == 1
    updated_prop = saved_schema[0]
    assert isinstance(updated_prop, StatusProperty)
    assert len(updated_prop.choices) == 2
    assert updated_prop.choices[0].name == "A"
    assert updated_prop.choices[1].name == "B"


def test_update_property_status_keep_name_preserves_existing_choices() -> None:
    """When updating a status property without new_choices, existing choices are preserved."""
    from fern.domain.entities import Choice
    from fern.domain.entities.properties.choice_category import ChoiceCategory

    existing_choice = Choice(
        name="Done", category=ChoiceCategory(name="c1"), color="#0f0"
    )
    status_prop = StatusProperty(id="p1", name="Old", choices=[existing_choice])
    db_repo = MagicMock()
    db_repo.get_schema.return_value = ([status_prop], ["p1"])
    page_repo = MagicMock()
    page_repo.list_all.return_value = []

    use_case = UpdatePropertyUseCase(
        database_repository=db_repo, page_repository=page_repo
    )
    use_case.execute(
        UpdatePropertyInputDTO(
            database_name="DB",
            property_id="p1",
            new_name="New Name",
            new_type_key="status",
            new_choices=None,
        )
    )

    saved_schema = db_repo.save_schema.call_args[0][1]
    updated_prop = saved_schema[0]
    assert isinstance(updated_prop, StatusProperty)
    assert len(updated_prop.choices) == 1
    assert updated_prop.choices[0].name == "Done"
    assert updated_prop.name == "New Name"
