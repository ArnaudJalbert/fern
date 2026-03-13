"""Unit tests for UpdatePropertyOrderUseCase."""

from unittest.mock import MagicMock

from fern.application.use_cases.update_property_order import UpdatePropertyOrderUseCase
from fern.domain.entities import Property, PropertyType


def test_update_property_order_success() -> None:
    db_repo = MagicMock()
    db_repo.get_schema.return_value = (
        [Property(id="p1", name="A", type=PropertyType.BOOLEAN)],
        ["p1"],
    )

    use_case = UpdatePropertyOrderUseCase(database_repository=db_repo)
    out = use_case.execute(
        UpdatePropertyOrderUseCase.Input(
            database_name="DB", property_order=("p2", "p1")
        )
    )

    assert out.success is True
    db_repo.save_schema.assert_called_once()
    call_args = db_repo.save_schema.call_args[0]
    assert call_args[0] == "DB"
    assert call_args[2] == ["p2", "p1"]
