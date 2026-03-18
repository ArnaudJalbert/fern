"""Unit tests for UpdatePagePropertyUseCase."""

import pytest
from unittest.mock import MagicMock

from fern.application.errors import PageNotFoundError, PropertyNotFoundOnPageError
from fern.application.use_cases.update_page_property import UpdatePagePropertyUseCase
from fern.domain.entities import BooleanProperty, Page


def test_update_page_property_success() -> None:
    prop = BooleanProperty(id="p1", name="Done", value=False)
    page = Page(id=1, title="T", content="", properties=[prop])
    repo = MagicMock()
    repo.get_by_id.return_value = page

    use_case = UpdatePagePropertyUseCase(page_repository=repo)
    use_case.execute(
        UpdatePagePropertyUseCase.Input(page_id=1, property_id="p1", value=True)
    )

    repo.update.assert_called_once()
    updated_props = repo.update.call_args[1]["properties"]
    assert updated_props[0].value is True


def test_update_page_property_page_not_found() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = None

    use_case = UpdatePagePropertyUseCase(page_repository=repo)
    with pytest.raises(PageNotFoundError):
        use_case.execute(
            UpdatePagePropertyUseCase.Input(page_id=999, property_id="p1", value=True)
        )

    repo.update.assert_not_called()


def test_update_page_property_property_not_on_page() -> None:
    page = Page(id=1, title="T", content="", properties=[])
    repo = MagicMock()
    repo.get_by_id.return_value = page

    use_case = UpdatePagePropertyUseCase(page_repository=repo)
    with pytest.raises(PropertyNotFoundOnPageError):
        use_case.execute(
            UpdatePagePropertyUseCase.Input(page_id=1, property_id="p1", value=True)
        )

    repo.update.assert_not_called()


def test_update_page_property_preserves_other_properties_on_page() -> None:
    """Updating one property leaves other properties on the page unchanged (else branch)."""
    prop_to_update = BooleanProperty(id="p1", name="Done", value=False)
    other_prop = BooleanProperty(id="p2", name="Other", value=True)
    page = Page(id=1, title="T", content="", properties=[prop_to_update, other_prop])
    repo = MagicMock()
    repo.get_by_id.return_value = page

    use_case = UpdatePagePropertyUseCase(page_repository=repo)
    use_case.execute(
        UpdatePagePropertyUseCase.Input(page_id=1, property_id="p1", value=True)
    )

    repo.update.assert_called_once()
    updated_props = repo.update.call_args[1]["properties"]
    assert len(updated_props) == 2
    assert updated_props[0].id == "p1"
    assert updated_props[0].value is True
    assert updated_props[1].id == "p2"
    assert updated_props[1].value is True
