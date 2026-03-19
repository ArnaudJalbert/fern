"""Unit tests for VaultController property conversion and error handling."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from fern.application.dtos import (
    BooleanPropertyInputDTO,
    PropertyValueDTO,
    StatusPropertyInputDTO,
    StringPropertyInputDTO,
)
from fern.application.errors import (
    PageNotFoundError as AppPageNotFoundError,
)
from fern.application.errors import (
    PropertyAlreadyExistsError as AppPropertyAlreadyExistsError,
)
from fern.infrastructure.controller.errors import (
    PageNotFoundError,
    PropertyAlreadyExistsError,
    VaultNotFoundError,
)
from fern.infrastructure.controller.vault_controller import VaultController


class MockPropertyDTOWithTypeKey:
    """Mock property DTO that uses callable type_key() method."""

    def __init__(self, prop_id: str, name: str, type_key: str = "string", value=None):
        self.id = prop_id
        self.name = name
        self._type_key = type_key
        self.value = value

    def type_key(self) -> str:
        return self._type_key


class MockPropertyDTOWithTypeAttr:
    """Mock property DTO that uses type attribute (legacy pattern)."""

    def __init__(self, prop_id: str, name: str, type_str: str = "string", value=None):
        self.id = prop_id
        self.name = name
        self.type = type_str
        self.value = value


@pytest.fixture
def vault_controller():
    """Create a VaultController with mocked dependencies."""
    vault_path = Path("/test/vault").resolve()
    vault_repo = MagicMock()
    db_repo = MagicMock()
    page_repo_factory = MagicMock()
    page_repo = MagicMock()
    page_repo_factory.create.return_value = page_repo

    controller = VaultController(
        vault_path=vault_path,
        vault_repository=vault_repo,
        database_repository=db_repo,
        page_repository_factory=page_repo_factory,
    )

    return {
        "controller": controller,
        "vault_path": vault_path,
        "vault_repo": vault_repo,
        "db_repo": db_repo,
        "page_repo_factory": page_repo_factory,
        "page_repo": page_repo,
    }


def test_ui_to_property_value_dtos_with_type_key_method(vault_controller):
    """Test conversion with DTOs that have callable type_key()."""
    controller = vault_controller["controller"]

    ui_props = [
        MockPropertyDTOWithTypeKey("prop1", "Name", "string", "value1"),
        MockPropertyDTOWithTypeKey("prop2", "Done", "boolean", True),
    ]

    result = controller._ui_to_property_value_dtos(ui_props)

    assert len(result) == 2
    assert result[0] == PropertyValueDTO(
        property_id="prop1", name="Name", type_key="string", value="value1"
    )
    assert result[1] == PropertyValueDTO(
        property_id="prop2", name="Done", type_key="boolean", value=True
    )


def test_ui_to_property_value_dtos_with_type_attribute(vault_controller):
    """Test conversion with DTOs that use type attribute (legacy pattern)."""
    controller = vault_controller["controller"]

    ui_props = [
        MockPropertyDTOWithTypeAttr("prop1", "Name", "string", "value1"),
        MockPropertyDTOWithTypeAttr("prop2", "Done", "boolean", True),
    ]

    result = controller._ui_to_property_value_dtos(ui_props)

    assert len(result) == 2
    assert result[0].property_id == "prop1"
    assert result[0].type_key == "string"
    assert result[0].value == "value1"
    assert result[1].property_id == "prop2"
    assert result[1].type_key == "boolean"
    assert result[1].value is True


def test_ui_to_property_value_dtos_skips_id_and_title(vault_controller):
    """Test that id and title properties are filtered out."""
    controller = vault_controller["controller"]

    ui_props = [
        MockPropertyDTOWithTypeKey("id", "ID", "id", 1),
        MockPropertyDTOWithTypeKey("title", "Title", "title", "Hello"),
        MockPropertyDTOWithTypeKey("prop1", "Name", "string", "value1"),
    ]

    result = controller._ui_to_property_value_dtos(ui_props)

    assert len(result) == 1
    assert result[0].property_id == "prop1"


def test_ui_to_property_value_dtos_handles_none(vault_controller):
    """Test that None input returns None."""
    controller = vault_controller["controller"]
    result = controller._ui_to_property_value_dtos(None)
    assert result is None


def test_ui_to_property_value_dtos_handles_empty_list(vault_controller):
    """Test that empty list returns empty list."""
    controller = vault_controller["controller"]
    result = controller._ui_to_property_value_dtos([])
    assert result == []


def test_ui_to_property_value_dtos_missing_type_raises(vault_controller):
    """Test that DTO without type raises ValueError."""
    controller = vault_controller["controller"]

    class BadDTO:
        def __init__(self):
            self.id = "bad"
            self.name = "Bad"

    ui_props = [BadDTO()]

    with pytest.raises(ValueError, match="Property .* has no type"):
        controller._ui_to_property_value_dtos(ui_props)


def test_build_property_dto_boolean(vault_controller):
    """Test _build_property_dto creates BooleanPropertyInputDTO."""
    controller = vault_controller["controller"]
    result = controller._build_property_dto("done", "Done", "boolean", None)
    assert isinstance(result, BooleanPropertyInputDTO)
    assert result.property_id == "done"
    assert result.name == "Done"


def test_build_property_dto_string(vault_controller):
    """Test _build_property_dto creates StringPropertyInputDTO."""
    controller = vault_controller["controller"]
    result = controller._build_property_dto("name", "Name", "string", None)
    assert isinstance(result, StringPropertyInputDTO)
    assert result.property_id == "name"
    assert result.name == "Name"


def test_build_property_dto_status_with_choices(vault_controller):
    """Test _build_property_dto creates StatusPropertyInputDTO with choices."""
    controller = vault_controller["controller"]

    choices = [
        {"name": "Todo", "category": "cat1", "color": "#ff0000"},
        {"name": "Done", "category": "cat2", "color": "#00ff00"},
    ]
    result = controller._build_property_dto("status", "Status", "status", choices)

    assert isinstance(result, StatusPropertyInputDTO)
    assert result.property_id == "status"
    assert result.name == "Status"
    assert len(result.choices) == 2
    assert result.choices[0].name == "Todo"
    assert result.choices[1].name == "Done"


def test_build_property_dto_status_without_choices_raises(vault_controller):
    """Test _build_property_dto raises ValueError for status without choices."""
    controller = vault_controller["controller"]

    with pytest.raises(ValueError, match="status property requires choices"):
        controller._build_property_dto("status", "Status", "status", None)


def test_build_property_dto_unknown_type_raises(vault_controller):
    """Test _build_property_dto raises ValueError for unknown type."""
    controller = vault_controller["controller"]

    with pytest.raises(ValueError, match="Unknown property type"):
        controller._build_property_dto("x", "X", "unknown", None)


def test_save_page_property_conversion(vault_controller):
    """Test save_page correctly converts UI properties to DTOs."""
    controller = vault_controller["controller"]
    page_repo = vault_controller["page_repo"]

    ui_props = [
        MockPropertyDTOWithTypeKey("done", "Done", "boolean", True),
        MockPropertyDTOWithTypeKey("status", "Status", "status", "In Progress"),
    ]

    controller.save_page(
        database_name="Inbox",
        page_id=1,
        title="Test",
        content="Content",
        properties=ui_props,
    )

    page_repo.update.assert_called_once()
    call_args = page_repo.update.call_args
    assert call_args[0][0] == 1  # page_id
    assert call_args[0][1] == "Test"  # title
    assert call_args[0][2] == "Content"  # content

    properties_arg = call_args[1]["properties"]
    assert len(properties_arg) == 2
    # Domain Property objects have 'id' attribute, not 'property_id'
    assert properties_arg[0].id == "done"
    assert properties_arg[0].name == "Done"
    assert properties_arg[0].type_key() == "boolean"
    assert properties_arg[0].value is True
    assert properties_arg[1].id == "status"
    assert properties_arg[1].name == "Status"
    assert properties_arg[1].type_key() == "status"
    assert properties_arg[1].value == "In Progress"


def test_add_property_error_translation(vault_controller):
    """Test add_property translates AppPropertyAlreadyExistsError to controller error."""
    controller = vault_controller["controller"]
    db_repo = vault_controller["db_repo"]

    db_repo.get_schema.return_value = ([], [])
    db_repo.save_schema.side_effect = AppPropertyAlreadyExistsError(
        property_id="exists", database_name="Inbox"
    )

    with pytest.raises(PropertyAlreadyExistsError) as exc_info:
        controller.add_property(
            database_name="Inbox",
            property_id="exists",
            name="Exists",
            property_type="string",
        )

    assert exc_info.value.property_id == "exists"
    assert exc_info.value.database_name == "Inbox"
    assert "already exists" in str(exc_info.value).lower()


def test_delete_page_error_translation(vault_controller):
    """Test delete_page translates AppPageNotFoundError to PageNotFoundError."""
    controller = vault_controller["controller"]
    vault_controller["page_repo"]

    # Mock the DeletePageUseCase to raise an error
    from fern.application.use_cases.delete_page import DeletePageUseCase


    def mock_init(self, repo):
        self._page_repository = repo
        self.execute = MagicMock(
            side_effect=AppPageNotFoundError(
                page_id=123,
                database_name="Inbox",
                vault_path=vault_controller["vault_path"],
            )
        )

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(DeletePageUseCase, "__init__", mock_init)
        with pytest.raises(PageNotFoundError) as exc_info:
            controller.delete_page(database_name="Inbox", page_id=123)

        # PageNotFoundError expects page_id, database_name, vault_path
        assert exc_info.value.page_id == 123
        assert exc_info.value.database_name == "Inbox"
        assert exc_info.value.vault_path == vault_controller["vault_path"]


def test_open_vault_error_translation(vault_controller):
    """Test open_vault translates AppVaultNotFoundError to VaultNotFoundError."""
    controller = vault_controller["controller"]
    vault_repo = vault_controller["vault_repo"]

    vault_repo.get.return_value = None

    with pytest.raises(VaultNotFoundError) as exc_info:
        controller.open_vault()

    assert exc_info.value.path == vault_controller["vault_path"]


def test_db_dir_method(vault_controller):
    """Test _db_dir correctly constructs database path."""
    controller = vault_controller["controller"]
    vault_path = vault_controller["vault_path"]

    result = controller._db_dir("Inbox")
    assert result == vault_path / "Inbox"

    result = controller._db_dir("Projects/Tasks")
    assert result == vault_path / "Projects" / "Tasks"


def test_database_marker_name_property(vault_controller):
    """Test database_marker_name property returns correct constant."""
    controller = vault_controller["controller"]
    result = controller.database_marker_name
    assert result == "database.json"


def test_is_database_folder_method(vault_controller):
    """Test is_database_folder method exists and is callable."""
    controller = vault_controller["controller"]
    assert callable(controller.is_database_folder)
