"""Unit tests for OpenVaultUseCase."""

from unittest.mock import MagicMock

from fern.application.use_cases.open_vault import OpenVaultUseCase
from fern.domain.entities import (
    Database,
    Page,
    Property,
    PropertyType,
    Vault,
)


def test_open_vault_success() -> None:
    page = Page(id=1, title="P", content="c", properties=[])
    prop = Property(id="id", name="ID", type=PropertyType.ID, mandatory=True)
    title_prop = Property(
        id="title", name="Title", type=PropertyType.TITLE, mandatory=True
    )
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

    assert out.success is True
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
    out = use_case.execute(OpenVaultUseCase.Input())

    assert out.success is False
    assert out.vault_name == ""
    assert out.databases == ()


def test_open_vault_includes_schema_and_property_order() -> None:
    prop = Property(id="p1", name="Status", type=PropertyType.STRING, value="")
    id_prop = Property(id="id", name="ID", type=PropertyType.ID, mandatory=True)
    title_prop = Property(
        id="title", name="Title", type=PropertyType.TITLE, mandatory=True
    )
    page = Page(id=1, title="P", content="", properties=[prop])
    db = Database(
        name="D",
        pages=[page],
        properties=[
            id_prop,
            title_prop,
            Property(id="p1", name="Status", type=PropertyType.STRING),
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
    id_prop = Property(id="id", name="ID", type=PropertyType.ID, mandatory=True)
    title_prop = Property(
        id="title", name="Title", type=PropertyType.TITLE, mandatory=True
    )
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
    id_prop = Property(id="id", name="ID", type=PropertyType.ID, mandatory=True)
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
