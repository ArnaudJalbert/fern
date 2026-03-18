"""Unit tests for AddPropertyUseCase (schema only; page updates are async)."""

import pytest
from unittest.mock import MagicMock

from fern.application.dtos import AddPropertyInputDTO, BooleanPropertyInputDTO
from fern.application.errors import PropertyAlreadyExistsError
from fern.application.use_cases.add_property import AddPropertyUseCase
from fern.domain.entities import BooleanProperty


def test_add_property_success() -> None:
    db_repo = MagicMock()
    db_repo.get_schema.return_value = ([], [])

    use_case = AddPropertyUseCase(database_repository=db_repo)
    use_case.execute(
        AddPropertyInputDTO(
            database_name="DB",
            property=BooleanPropertyInputDTO(property_id="p1", name="Done"),
        )
    )

    db_repo.save_schema.assert_called_once()
    call_args = db_repo.save_schema.call_args[0]
    assert call_args[0] == "DB"
    assert len(call_args[1]) == 1
    assert call_args[1][0].id == "p1"
    assert call_args[2] == ["p1"]


def test_add_property_duplicate_id_fails() -> None:
    existing = BooleanProperty(id="p1", name="X")
    db_repo = MagicMock()
    db_repo.get_schema.return_value = ([existing], ["p1"])

    use_case = AddPropertyUseCase(database_repository=db_repo)
    with pytest.raises(PropertyAlreadyExistsError):
        use_case.execute(
            AddPropertyInputDTO(
                database_name="DB",
                property=BooleanPropertyInputDTO(property_id="p1", name="Done"),
            )
        )

    db_repo.save_schema.assert_not_called()
