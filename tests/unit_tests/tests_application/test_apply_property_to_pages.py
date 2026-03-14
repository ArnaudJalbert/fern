"""Unit tests for ApplyPropertyToPagesUseCase."""

from unittest.mock import MagicMock

from fern.application.dtos import ApplyPropertyToPagesInputDTO
from fern.application.use_cases.apply_property_to_pages import (
    ApplyPropertyToPagesUseCase,
)
from fern.domain.entities import Page


def test_apply_property_to_pages_updates_all() -> None:
    page1 = Page(id=1, title="P1", content="", properties=[])
    page2 = Page(id=2, title="P2", content="", properties=[])
    page_repo = MagicMock()
    page_repo.list_all.return_value = [page1, page2]

    use_case = ApplyPropertyToPagesUseCase(page_repository=page_repo)
    use_case.execute(
        ApplyPropertyToPagesInputDTO(
            property_id="status", name="Status", type_key="string"
        )
    )

    assert page_repo.update.call_count == 2
    for call in page_repo.update.call_args_list:
        kwargs = call[1]
        assert "properties" in kwargs
        props = kwargs["properties"]
        assert len(props) == 1
        assert props[0].id == "status"
        assert props[0].value == ""


def test_apply_property_to_pages_empty_list() -> None:
    page_repo = MagicMock()
    page_repo.list_all.return_value = []

    use_case = ApplyPropertyToPagesUseCase(page_repository=page_repo)
    use_case.execute(
        ApplyPropertyToPagesInputDTO(property_id="x", name="X", type_key="boolean")
    )

    page_repo.update.assert_not_called()
