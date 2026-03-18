"""Unit tests for AddPagePropertyUseCase."""

import pytest
from unittest.mock import MagicMock

from fern.application.dtos import AddPagePropertyInputDTO
from fern.application.errors import PageNotFoundError, PropertyAlreadyExistsOnPageError
from fern.application.use_cases.add_page_property import AddPagePropertyUseCase
from fern.domain.entities import Page, StringProperty


def test_add_page_property_success() -> None:
    page = Page(id=1, title="P", content="", properties=[])
    page_repo = MagicMock()
    page_repo.get_by_id.return_value = page

    use_case = AddPagePropertyUseCase(page_repository=page_repo)
    use_case.execute(
        AddPagePropertyInputDTO(
            page_id=1, property_id="status", name="Status", type_key="string"
        )
    )

    page_repo.update.assert_called_once()
    call_kw = page_repo.update.call_args[1]
    assert call_kw["properties"] is not None
    props = call_kw["properties"]
    assert len(props) == 1
    assert props[0].id == "status"
    assert props[0].name == "Status"
    assert props[0].value == ""


def test_add_page_property_page_not_found_fails() -> None:
    page_repo = MagicMock()
    page_repo.get_by_id.return_value = None

    use_case = AddPagePropertyUseCase(page_repository=page_repo)
    with pytest.raises(PageNotFoundError):
        use_case.execute(
            AddPagePropertyInputDTO(
                page_id=99, property_id="x", name="X", type_key="boolean"
            )
        )

    page_repo.update.assert_not_called()


def test_add_page_property_duplicate_id_on_page_fails() -> None:
    existing = StringProperty(id="status", name="Status", value="")
    page = Page(id=1, title="P", content="", properties=[existing])
    page_repo = MagicMock()
    page_repo.get_by_id.return_value = page

    use_case = AddPagePropertyUseCase(page_repository=page_repo)
    with pytest.raises(PropertyAlreadyExistsOnPageError):
        use_case.execute(
            AddPagePropertyInputDTO(
                page_id=1, property_id="status", name="Status", type_key="string"
            )
        )

    page_repo.update.assert_not_called()
