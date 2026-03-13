"""Unit tests for UpdatePropertyUseCase."""

from unittest.mock import MagicMock, patch

from fern.application.use_cases.update_property import UpdatePropertyUseCase
from fern.domain.entities import Page, Property, PropertyType


def test_update_property_success() -> None:
    prop = Property(id="p1", name="Old", type=PropertyType.STRING)
    db_repo = MagicMock()
    db_repo.get_schema.return_value = ([prop], ["p1"])
    page_repo = MagicMock()
    page_repo.list_all.return_value = []

    use_case = UpdatePropertyUseCase(database_repository=db_repo, page_repository=page_repo)
    out = use_case.execute(
        UpdatePropertyUseCase.Input(database_name="DB", property_id="p1", new_name="New Name", new_type="boolean")
    )

    assert out.success is True
    db_repo.save_schema.assert_called_once()
    call_args = db_repo.save_schema.call_args[0]
    assert call_args[1][0].name == "New Name"
    assert call_args[1][0].type == PropertyType.BOOLEAN


def test_update_property_not_found_fails() -> None:
    db_repo = MagicMock()
    db_repo.get_schema.return_value = ([], [])
    page_repo = MagicMock()

    use_case = UpdatePropertyUseCase(database_repository=db_repo, page_repository=page_repo)
    out = use_case.execute(UpdatePropertyUseCase.Input(database_name="DB", property_id="p1", new_name="X"))

    assert out.success is False
    db_repo.save_schema.assert_not_called()


def test_update_property_name_only() -> None:
    prop = Property(id="p1", name="Old", type=PropertyType.STRING)
    db_repo = MagicMock()
    db_repo.get_schema.return_value = ([prop], ["p1"])
    page_repo = MagicMock()
    page_repo.list_all.return_value = []

    use_case = UpdatePropertyUseCase(database_repository=db_repo, page_repository=page_repo)
    out = use_case.execute(
        UpdatePropertyUseCase.Input(database_name="DB", property_id="p1", new_name="New")
    )

    assert out.success is True
    saved_prop = db_repo.save_schema.call_args[0][1][0]
    assert saved_prop.name == "New"
    assert saved_prop.type == PropertyType.STRING


def test_update_property_coerces_page_values() -> None:
    prop = Property(id="p1", name="Done", type=PropertyType.STRING)
    db_repo = MagicMock()
    db_repo.get_schema.return_value = ([prop], ["p1"])
    page_prop = Property(id="p1", name="Done", type=PropertyType.STRING, value="true")
    page = Page(id=1, title="T", content="", properties=[page_prop])
    page_repo = MagicMock()
    page_repo.list_all.return_value = [page]

    use_case = UpdatePropertyUseCase(database_repository=db_repo, page_repository=page_repo)
    use_case.execute(
        UpdatePropertyUseCase.Input(database_name="DB", property_id="p1", new_type="boolean")
    )

    updated_props = page_repo.update.call_args[1]["properties"]
    assert updated_props[0].value is True
    assert updated_props[0].type == PropertyType.BOOLEAN


def test_update_property_empty_name_keeps_old() -> None:
    prop = Property(id="p1", name="Old", type=PropertyType.STRING)
    db_repo = MagicMock()
    db_repo.get_schema.return_value = ([prop], ["p1"])
    page_repo = MagicMock()
    page_repo.list_all.return_value = []

    use_case = UpdatePropertyUseCase(database_repository=db_repo, page_repository=page_repo)
    use_case.execute(
        UpdatePropertyUseCase.Input(database_name="DB", property_id="p1", new_name="  ")
    )

    saved_prop = db_repo.save_schema.call_args[0][1][0]
    assert saved_prop.name == "Old"


def test_update_property_page_with_other_properties_preserved() -> None:
    prop = Property(id="p1", name="Old", type=PropertyType.STRING)
    db_repo = MagicMock()
    db_repo.get_schema.return_value = ([prop], ["p1"])
    other_prop = Property(id="p2", name="Other", type=PropertyType.BOOLEAN, value=True)
    page_prop = Property(id="p1", name="Old", type=PropertyType.STRING, value="hi")
    page = Page(id=1, title="T", content="", properties=[page_prop, other_prop])
    page_repo = MagicMock()
    page_repo.list_all.return_value = [page]

    use_case = UpdatePropertyUseCase(database_repository=db_repo, page_repository=page_repo)
    use_case.execute(
        UpdatePropertyUseCase.Input(database_name="DB", property_id="p1", new_name="New")
    )

    updated_props = page_repo.update.call_args[1]["properties"]
    assert len(updated_props) == 2
    assert updated_props[0].name == "New"
    assert updated_props[1].id == "p2"
    assert updated_props[1].value is True


def test_update_property_empty_type_keeps_old() -> None:
    prop = Property(id="p1", name="X", type=PropertyType.STRING)
    db_repo = MagicMock()
    db_repo.get_schema.return_value = ([prop], ["p1"])
    page_repo = MagicMock()
    page_repo.list_all.return_value = []

    use_case = UpdatePropertyUseCase(database_repository=db_repo, page_repository=page_repo)
    use_case.execute(
        UpdatePropertyUseCase.Input(database_name="DB", property_id="p1", new_type="  ")
    )

    saved_prop = db_repo.save_schema.call_args[0][1][0]
    assert saved_prop.type == PropertyType.STRING


def test_update_property_uses_default_value_when_coerced_value_is_none() -> None:
    """When updating property type, if coerced value is None, use type's default_value()."""
    prop = Property(id="p1", name="Done", type=PropertyType.STRING)
    db_repo = MagicMock()
    db_repo.get_schema.return_value = ([prop], ["p1"])
    page_prop = Property(id="p1", name="Done", type=PropertyType.STRING, value=None)
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
            UpdatePropertyUseCase.Input(
                database_name="DB", property_id="p1", new_type="boolean"
            )
        )

    updated_props = page_repo.update.call_args[1]["properties"]
    assert updated_props[0].value is False
    assert updated_props[0].type == PropertyType.BOOLEAN
