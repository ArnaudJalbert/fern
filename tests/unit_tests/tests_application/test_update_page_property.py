"""Unit tests for UpdatePagePropertyUseCase."""

from unittest.mock import MagicMock

from fern.application.use_cases.update_page_property import UpdatePagePropertyUseCase
from fern.domain.entities import Page, Property, PropertyType


def test_update_page_property_success() -> None:
    prop = Property(id="p1", name="Done", type=PropertyType.BOOLEAN, value=False)
    page = Page(id=1, title="T", content="", properties=[prop])
    repo = MagicMock()
    repo.get_by_id.return_value = page

    use_case = UpdatePagePropertyUseCase(page_repository=repo)
    out = use_case.execute(
        UpdatePagePropertyUseCase.Input(page_id=1, property_id="p1", value=True)
    )

    assert out.success is True
    repo.update.assert_called_once()
    updated_props = repo.update.call_args[1]["properties"]
    assert updated_props[0].value is True


def test_update_page_property_page_not_found() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = None

    use_case = UpdatePagePropertyUseCase(page_repository=repo)
    out = use_case.execute(
        UpdatePagePropertyUseCase.Input(page_id=999, property_id="p1", value=True)
    )

    assert out.success is False
    repo.update.assert_not_called()


def test_update_page_property_property_not_on_page() -> None:
    page = Page(id=1, title="T", content="", properties=[])
    repo = MagicMock()
    repo.get_by_id.return_value = page

    use_case = UpdatePagePropertyUseCase(page_repository=repo)
    out = use_case.execute(
        UpdatePagePropertyUseCase.Input(page_id=1, property_id="p1", value=True)
    )

    assert out.success is False
    repo.update.assert_not_called()
