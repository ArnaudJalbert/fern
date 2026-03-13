"""Unit tests for AddPagePropertyUseCase."""

from unittest.mock import MagicMock

from fern.application.use_cases.add_page_property import AddPagePropertyUseCase
from fern.domain.entities import Page, Property, PropertyType


def test_add_page_property_success() -> None:
    page = Page(id=1, title="P", content="", properties=[])
    page_repo = MagicMock()
    page_repo.get_by_id.return_value = page

    use_case = AddPagePropertyUseCase(page_repository=page_repo)
    out = use_case.execute(
        AddPagePropertyUseCase.Input(
            page_id=1, property_id="status", name="Status", type=PropertyType.STRING
        )
    )

    assert out.success is True
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
    out = use_case.execute(
        AddPagePropertyUseCase.Input(
            page_id=99, property_id="x", name="X", type=PropertyType.BOOLEAN
        )
    )

    assert out.success is False
    page_repo.update.assert_not_called()


def test_add_page_property_duplicate_id_on_page_fails() -> None:
    existing = Property(id="status", name="Status", type=PropertyType.STRING, value="")
    page = Page(id=1, title="P", content="", properties=[existing])
    page_repo = MagicMock()
    page_repo.get_by_id.return_value = page

    use_case = AddPagePropertyUseCase(page_repository=page_repo)
    out = use_case.execute(
        AddPagePropertyUseCase.Input(
            page_id=1, property_id="status", name="Status", type=PropertyType.STRING
        )
    )

    assert out.success is False
    page_repo.update.assert_not_called()
