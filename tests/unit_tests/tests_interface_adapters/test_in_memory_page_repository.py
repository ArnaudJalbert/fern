"""Unit tests for InMemoryPageRepository. No mocks; pure in-memory behavior."""

from fern.domain.entities import BooleanProperty, Page
from fern.interface_adapters.repositories.in_memory_page_repository import (
    InMemoryPageRepository,
)


def test_get_by_id_empty_returns_none() -> None:
    repo = InMemoryPageRepository()
    assert repo.get_by_id(1) is None


def test_list_all_empty() -> None:
    repo = InMemoryPageRepository()
    assert repo.list_all() == []


def test_create_returns_page_with_id() -> None:
    repo = InMemoryPageRepository()
    page = repo.create("Title", "Content")
    assert page.id == 1
    assert page.title == "Title"
    assert page.content == "Content"
    assert page.properties == []


def test_create_increments_id() -> None:
    repo = InMemoryPageRepository()
    p1 = repo.create("A", "")
    p2 = repo.create("B", "")
    assert p1.id == 1
    assert p2.id == 2


def test_get_by_id_after_create() -> None:
    repo = InMemoryPageRepository()
    created = repo.create("T", "C")
    found = repo.get_by_id(created.id)
    assert found is not None
    assert found.id == created.id
    assert found.title == "T"


def test_list_all_after_create() -> None:
    repo = InMemoryPageRepository()
    repo.create("A", "")
    repo.create("B", "")
    pages = repo.list_all()
    assert len(pages) == 2


def test_update_existing_page() -> None:
    repo = InMemoryPageRepository()
    repo.create("Old", "old content")
    repo.update(1, "New", "new content")
    page = repo.get_by_id(1)
    assert page is not None
    assert page.title == "New"
    assert page.content == "new content"


def test_update_with_properties() -> None:
    repo = InMemoryPageRepository()
    prop = BooleanProperty(id="p1", name="Done", value=True)
    repo.create("T", "")
    repo.update(1, "T", "", properties=[prop])
    page = repo.get_by_id(1)
    assert page is not None
    assert len(page.properties) == 1
    assert page.properties[0].id == "p1"
    assert page.properties[0].value is True


def test_update_nonexistent_no_op() -> None:
    repo = InMemoryPageRepository()
    repo.create("T", "")
    repo.update(999, "X", "Y")
    assert repo.get_by_id(999) is None
    assert repo.get_by_id(1).title == "T"


def test_delete_existing() -> None:
    repo = InMemoryPageRepository()
    repo.create("T", "")
    repo.delete(1)
    assert repo.get_by_id(1) is None
    assert repo.list_all() == []


def test_delete_nonexistent_no_error() -> None:
    repo = InMemoryPageRepository()
    repo.delete(999)  # no raise


def test_init_with_initial_pages() -> None:
    page = Page(id=1, title="Initial", content="", properties=[])
    repo = InMemoryPageRepository(pages={1: page})
    assert repo.get_by_id(1) is not None
    assert repo.get_by_id(1).title == "Initial"
