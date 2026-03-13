"""Unit tests for AddPropertyUseCase (schema only; page updates are async)."""

from unittest.mock import MagicMock

from fern.application.use_cases.add_property import AddPropertyUseCase
from fern.domain.entities import Property, PropertyType


def test_add_property_success() -> None:
    db_repo = MagicMock()
    db_repo.get_schema.return_value = ([], [])

    use_case = AddPropertyUseCase(database_repository=db_repo)
    out = use_case.execute(
        AddPropertyUseCase.Input(
            database_name="DB", property_id="p1", name="Done", type=PropertyType.BOOLEAN
        )
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

    use_case = AddPropertyUseCase(database_repository=db_repo)
    out = use_case.execute(
        AddPropertyUseCase.Input(
            database_name="DB", property_id="p1", name="Done", type=PropertyType.BOOLEAN
        )
    )

    assert out.success is False
    db_repo.save_schema.assert_not_called()
