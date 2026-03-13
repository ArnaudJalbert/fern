"""Unit tests for AddPropertyUseCase."""

from unittest.mock import MagicMock

from fern.application.use_cases.add_property import AddPropertyUseCase
from fern.domain.entities import Page, Property, PropertyType


def test_add_property_success() -> None:
    db_repo = MagicMock()
    db_repo.get_schema.return_value = ([], [])
    page_repo = MagicMock()
    page_repo.list_all.return_value = []

    use_case = AddPropertyUseCase(database_repository=db_repo, page_repository=page_repo)
    out = use_case.execute(
        AddPropertyUseCase.Input(database_name="DB", property_id="p1", name="Done", type=PropertyType.BOOLEAN)
    )

    assert out.success is True
    db_repo.save_schema.assert_called_once()
    call_args = db_repo.save_schema.call_args
    assert call_args[0][0] == "DB"
    assert len(call_args[0][1]) == 1
    assert call_args[0][1][0].id == "p1"
    assert call_args[0][2] == ["p1"]


def test_add_property_duplicate_id_fails() -> None:
    existing = Property(id="p1", name="X", type=PropertyType.BOOLEAN)
    db_repo = MagicMock()
    db_repo.get_schema.return_value = ([existing], ["p1"])
    page_repo = MagicMock()

    use_case = AddPropertyUseCase(database_repository=db_repo, page_repository=page_repo)
    out = use_case.execute(
        AddPropertyUseCase.Input(database_name="DB", property_id="p1", name="Done", type=PropertyType.BOOLEAN)
    )

    assert out.success is False
    db_repo.save_schema.assert_not_called()


def test_add_property_updates_all_pages_with_default() -> None:
    db_repo = MagicMock()
    db_repo.get_schema.return_value = ([], [])
    page = Page(id=1, title="P", content="", properties=[])
    page_repo = MagicMock()
    page_repo.list_all.return_value = [page]

    use_case = AddPropertyUseCase(database_repository=db_repo, page_repository=page_repo)
    use_case.execute(
        AddPropertyUseCase.Input(database_name="DB", property_id="p1", name="Done", type=PropertyType.BOOLEAN)
    )

    page_repo.update.assert_called_once()
    updated_props = page_repo.update.call_args[1]["properties"]
    assert len(updated_props) == 1
    assert updated_props[0].value is False
