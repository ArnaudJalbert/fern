import json
from pathlib import Path

import fern.interface_adapters.repositories.json_recent_vaults_repository as mod


def _patch_storage(monkeypatch, tmp_path: Path) -> Path:
    """Redirect ~/.fern/recent_vaults.json into tmp_path for tests."""
    config_dir = tmp_path / ".fern"
    recent_file = config_dir / "recent_vaults.json"

    monkeypatch.setattr(mod, "_config_dir", lambda: config_dir)
    monkeypatch.setattr(mod, "_recent_file", lambda: recent_file)
    return recent_file


def test_get_missing_file_returns_empty(tmp_path: Path, monkeypatch) -> None:
    recent_file = _patch_storage(monkeypatch, tmp_path)
    repo = mod.JsonRecentVaultsRepository()

    assert repo.get() == []
    assert not recent_file.exists()


def test_get_invalid_json_returns_empty(tmp_path: Path, monkeypatch) -> None:
    recent_file = _patch_storage(monkeypatch, tmp_path)
    recent_file.parent.mkdir(parents=True, exist_ok=True)
    recent_file.write_text("{not json", encoding="utf-8")

    repo = mod.JsonRecentVaultsRepository()
    assert repo.get() == []


def test_add_persists_and_deduplicates(tmp_path: Path, monkeypatch) -> None:
    recent_file = _patch_storage(monkeypatch, tmp_path)
    repo = mod.JsonRecentVaultsRepository()

    vault_a = (tmp_path / "VaultA").resolve()
    vault_b = (tmp_path / "VaultB").resolve()

    repo.add(vault_a)
    repo.add(vault_b)

    # Most recent first
    assert repo.get() == [vault_b, vault_a]

    data = json.loads(recent_file.read_text(encoding="utf-8"))
    assert data == [str(vault_b), str(vault_a)]

    # Adding an existing path moves it to the front (dedupe)
    repo.add(vault_a)
    assert repo.get() == [vault_a, vault_b]
    data = json.loads(recent_file.read_text(encoding="utf-8"))
    assert data == [str(vault_a), str(vault_b)]


def test_remove_updates_persisted_list(tmp_path: Path, monkeypatch) -> None:
    recent_file = _patch_storage(monkeypatch, tmp_path)
    repo = mod.JsonRecentVaultsRepository()

    vault_a = (tmp_path / "VaultA").resolve()
    vault_b = (tmp_path / "VaultB").resolve()

    repo.add(vault_a)
    repo.add(vault_b)
    assert recent_file.exists()

    repo.remove(vault_a)
    assert repo.get() == [vault_b]

    data = json.loads(recent_file.read_text(encoding="utf-8"))
    assert data == [str(vault_b)]


def test_add_caps_at_max_recent(tmp_path: Path, monkeypatch) -> None:
    _patch_storage(monkeypatch, tmp_path)
    repo = mod.JsonRecentVaultsRepository()

    # Add more than MAX_RECENT; repo should keep only the newest ones.
    added_vaults = [
        (tmp_path / f"Vault{i}").resolve() for i in range(mod.MAX_RECENT + 3)
    ]
    for vault_path in added_vaults:
        repo.add(vault_path)

    expected = list(reversed(added_vaults))[: mod.MAX_RECENT]
    assert repo.get() == expected


def test_helpers_use_home_directory(tmp_path: Path, monkeypatch) -> None:
    """Cover _config_dir() and _recent_file() helpers by patching Path.home()."""
    fake_home = tmp_path / "home"
    fake_home.mkdir(parents=True)

    # The module imports Path directly, so patch its Path.home.
    monkeypatch.setattr(
        mod.Path,
        "home",
        classmethod(lambda cls: fake_home),
    )

    repo = mod.JsonRecentVaultsRepository()

    vault_path = fake_home / "Vault"
    repo.add(vault_path)

    expected_file = fake_home / ".fern" / "recent_vaults.json"
    assert expected_file.exists()
    assert repo.get() == [vault_path.resolve()]
