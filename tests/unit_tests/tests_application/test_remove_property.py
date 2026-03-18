"""Unit tests for RemovePropertyUseCase."""

import pytest
from unittest.mock import MagicMock

from fern.application.errors import PropertyNotFoundError
from fern.application.use_cases.remove_property import RemovePropertyUseCase
from fern.domain.entities import BooleanProperty, Page


def test_remove_property_success() -> None:
    prop = BooleanProperty(id="p1", name="X")
    db_repo = MagicMock()
    db_repo.get_schema.return_value = ([prop], ["p1"])
    page_repo = MagicMock()
    page_repo.list_all.return_value = []

    use_case = RemovePropertyUseCase(
        database_repository=db_repo, page_repository=page_repo
    )
    use_case.execute(RemovePropertyUseCase.Input(database_name="DB", property_id="p1"))

    db_repo.save_schema.assert_called_once()
    call_args = db_repo.save_schema.call_args[0]
    assert len(call_args[1]) == 0
    assert call_args[2] == []


def test_remove_property_not_found_fails() -> None:
    db_repo = MagicMock()
    db_repo.get_schema.return_value = ([], [])
    page_repo = MagicMock()

    use_case = RemovePropertyUseCase(
        database_repository=db_repo, page_repository=page_repo
    )
    with pytest.raises(PropertyNotFoundError):
        use_case.execute(
            RemovePropertyUseCase.Input(database_name="DB", property_id="p1")
        )

    db_repo.save_schema.assert_not_called()


def test_remove_property_updates_pages() -> None:
    prop = BooleanProperty(id="p1", name="X")
    db_repo = MagicMock()
    db_repo.get_schema.return_value = ([prop], ["p1"])
    page_prop = BooleanProperty(id="p1", name="X", value=True)
    page = Page(id=1, title="T", content="", properties=[page_prop])
    page_repo = MagicMock()
    page_repo.list_all.return_value = [page]

    use_case = RemovePropertyUseCase(
        database_repository=db_repo, page_repository=page_repo
    )
    use_case.execute(RemovePropertyUseCase.Input(database_name="DB", property_id="p1"))

    page_repo.update.assert_called_once()
    updated_props = page_repo.update.call_args[1]["properties"]
    assert len(updated_props) == 0
