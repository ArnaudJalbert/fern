"""Unit tests for OpenVaultUseCase."""

import pytest
from unittest.mock import MagicMock

from fern.application.errors import VaultNotFoundError
from fern.application.use_cases.open_vault import OpenVaultUseCase
from fern.domain.entities import (
    Database,
    IdProperty,
    Page,
    StatusProperty,
    StringProperty,
    TitleProperty,
    Vault,
)


def test_open_vault_success() -> None:
    page = Page(id=1, title="P", content="c", properties=[])
    prop = IdProperty(id="id", name="ID")
    title_prop = TitleProperty(id="title", name="Title")
    db = Database(
        name="Inbox",
        pages=[page],
        properties=[prop, title_prop],
        property_order=["id", "title"],
    )
    vault = Vault(name="My Vault", databases=[db])
    repo = MagicMock()
    repo.get.return_value = vault

    use_case = OpenVaultUseCase(vault_repository=repo)
    out = use_case.execute(OpenVaultUseCase.Input())

    assert out.vault_name == "My Vault"
    assert len(out.databases) == 1
    assert out.databases[0].name == "Inbox"
    assert len(out.databases[0].pages) == 1
    assert out.databases[0].pages[0].id == 1
    repo.get.assert_called_once()


def test_open_vault_failure_no_vault() -> None:
    repo = MagicMock()
    repo.get.return_value = None

    use_case = OpenVaultUseCase(vault_repository=repo)
    with pytest.raises(VaultNotFoundError):
        use_case.execute(OpenVaultUseCase.Input())


def test_open_vault_includes_schema_and_property_order() -> None:
    prop = StringProperty(id="p1", name="Status", value="")
    id_prop = IdProperty(id="id", name="ID")
    title_prop = TitleProperty(id="title", name="Title")
    page = Page(id=1, title="P", content="", properties=[prop])
    db = Database(
        name="D",
        pages=[page],
        properties=[
            id_prop,
            title_prop,
            StringProperty(id="p1", name="Status"),
        ],
        property_order=["id", "title", "p1"],
    )
    vault = Vault(name="V", databases=[db])
    repo = MagicMock()
    repo.get.return_value = vault

    use_case = OpenVaultUseCase(vault_repository=repo)
    out = use_case.execute(OpenVaultUseCase.Input())

    schema_ids = [s.id for s in out.databases[0].schema]
    assert "p1" in schema_ids
    assert "id" in schema_ids
    assert out.databases[0].property_order == ("id", "title", "p1")
    page_out = out.databases[0].pages[0]
    page_prop_ids = [p.id for p in page_out.properties]
    assert "id" in page_prop_ids
    assert "title" in page_prop_ids


def test_open_vault_default_order_when_empty() -> None:
    id_prop = IdProperty(id="id", name="ID")
    title_prop = TitleProperty(id="title", name="Title")
    db = Database(
        name="D", pages=[], properties=[id_prop, title_prop], property_order=[]
    )
    vault = Vault(name="V", databases=[db])
    repo = MagicMock()
    repo.get.return_value = vault

    use_case = OpenVaultUseCase(vault_repository=repo)
    out = use_case.execute(OpenVaultUseCase.Input())

    assert out.databases[0].property_order == ("id", "title")


def test_open_vault_page_output_includes_mandatory_props() -> None:
    page = Page(id=5, title="Hello", content="world", properties=[])
    id_prop = IdProperty(id="id", name="ID")
    db = Database(name="D", pages=[page], properties=[id_prop], property_order=["id"])
    vault = Vault(name="V", databases=[db])
    repo = MagicMock()
    repo.get.return_value = vault

    out = OpenVaultUseCase(vault_repository=repo).execute(OpenVaultUseCase.Input())
    page_out = out.databases[0].pages[0]
    id_page_prop = next(p for p in page_out.properties if p.id == "id")
    assert id_page_prop.value == 5
    assert id_page_prop.mandatory is True
    title_page_prop = next(p for p in page_out.properties if p.id == "title")
    assert title_page_prop.value == "Hello"
    assert title_page_prop.mandatory is True


def test_open_vault_schema_includes_title_and_status_with_choices_output() -> None:
    """Schema output includes TitlePropertyOutput and StatusPropertyOutput with choices."""
    from fern.domain.entities import Choice
    from fern.domain.entities.properties.choice_category import ChoiceCategory

    choice = Choice(name="Done", category=ChoiceCategory(name="cat1"), color="#0f0")
    status_prop = StatusProperty(id="status", name="Status", choices=[choice])
    id_prop = IdProperty(id="id", name="ID")
    title_prop = TitleProperty(id="title", name="Title")
    page = Page(id=1, title="P", content="", properties=[])
    database = Database(
        name="D",
        pages=[page],
        properties=[id_prop, title_prop, status_prop],
        property_order=["id", "title", "status"],
    )
    vault = Vault(name="V", databases=[database])
    repo = MagicMock()
    repo.get.return_value = vault

    use_case = OpenVaultUseCase(vault_repository=repo)
    out = use_case.execute(OpenVaultUseCase.Input())

    schema = out.databases[0].schema
    assert len(schema) == 3
    title_schema = next(s for s in schema if s.id == "title")
    assert title_schema.name == "Title"
    status_schema = next(s for s in schema if s.id == "status")
    assert status_schema.name == "Status"
    assert len(status_schema.choices) == 1
    assert status_schema.choices[0].name == "Done"
    assert status_schema.choices[0].category.name == "cat1"
    assert status_schema.choices[0].color == "#0f0"


def test_open_vault_schema_includes_boolean_output() -> None:
    """Schema output includes BooleanPropertyOutput for boolean properties."""
    from fern.domain.entities import BooleanProperty

    boolean_prop = BooleanProperty(id="done", name="Done", value=False)
    id_prop = IdProperty(id="id", name="ID")
    title_prop = TitleProperty(id="title", name="Title")
    db = Database(
        name="D",
        pages=[],
        properties=[id_prop, title_prop, boolean_prop],
        property_order=["id", "title", "done"],
    )
    vault = Vault(name="V", databases=[db])

    repo = MagicMock()
    repo.get.return_value = vault

    out = OpenVaultUseCase(vault_repository=repo).execute(OpenVaultUseCase.Input())
    schema = out.databases[0].schema

    boolean_schema = next(s for s in schema if s.id == "done")
    assert boolean_schema.name == "Done"
    assert boolean_schema.mandatory is False
