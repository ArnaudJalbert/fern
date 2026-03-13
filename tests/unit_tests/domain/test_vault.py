"""Unit tests for Vault entity."""

from fern.domain.entities import Database, Vault


def test_vault_create_minimal() -> None:
    v = Vault(name="My Vault")
    assert v.name == "My Vault"
    assert v.databases == []


def test_vault_create_with_databases() -> None:
    db = Database(name="Inbox")
    v = Vault(name="V", databases=[db])
    assert len(v.databases) == 1
    assert v.databases[0].name == "Inbox"
