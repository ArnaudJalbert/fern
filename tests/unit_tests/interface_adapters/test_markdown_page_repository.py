"""Unit tests for MarkdownPageRepository. Uses tmp_path for real file I/O."""

from pathlib import Path

import frontmatter

from fern.domain.entities import Page, Property, PropertyType
from fern.interface_adapters.repositories.markdown_page_repository import (
    MarkdownPageRepository,
)


def test_list_all_empty(tmp_path: Path) -> None:
    repo = MarkdownPageRepository(tmp_path)
    assert repo.list_all() == []


def test_get_by_id_not_found(tmp_path: Path) -> None:
    repo = MarkdownPageRepository(tmp_path)
    assert repo.get_by_id(1) is None


def test_create_writes_md_file(tmp_path: Path) -> None:
    repo = MarkdownPageRepository(tmp_path)
    page = repo.create("My Page", "Hello world")
    assert page.id == 1
    assert page.title == "My Page"
    assert page.content == "Hello world"
    assert page.properties == []
    md_file = tmp_path / "My Page.md"
    assert md_file.exists()
    post = frontmatter.loads(md_file.read_text(encoding="utf-8"))
    assert post["id"] == 1
    assert post.content == "Hello world"


def test_create_increments_id(tmp_path: Path) -> None:
    repo = MarkdownPageRepository(tmp_path)
    p1 = repo.create("A", "")
    p2 = repo.create("B", "")
    assert p1.id == 1
    assert p2.id == 2


def test_list_all_returns_created_pages(tmp_path: Path) -> None:
    repo = MarkdownPageRepository(tmp_path)
    repo.create("First", "c1")
    repo.create("Second", "c2")
    pages = repo.list_all()
    assert len(pages) == 2
    titles = {p.title for p in pages}
    assert titles == {"First", "Second"}


def test_get_by_id_after_create(tmp_path: Path) -> None:
    repo = MarkdownPageRepository(tmp_path)
    repo.create("Target", "content")
    page = repo.get_by_id(1)
    assert page is not None
    assert page.title == "Target"
    assert page.content == "content"


def test_update_changes_title_and_content(tmp_path: Path) -> None:
    repo = MarkdownPageRepository(tmp_path)
    repo.create("Old Title", "old content")
    repo.update(1, "New Title", "new content")
    page = repo.get_by_id(1)
    assert page is not None
    assert page.title == "New Title"
    assert page.content == "new content"
    assert (tmp_path / "New Title.md").exists()
    assert not (tmp_path / "Old Title.md").exists()


def test_update_with_properties(tmp_path: Path) -> None:
    repo = MarkdownPageRepository(tmp_path)
    repo.create("P", "")
    props = [
        Property(id="p1", name="Done", type=PropertyType.BOOLEAN, value=True),
        Property(id="p2", name="Note", type=PropertyType.STRING, value="hi"),
    ]
    repo.update(1, "P", "body", properties=props)
    page = repo.get_by_id(1)
    assert page is not None
    assert len(page.properties) == 2
    assert page.properties[0].id == "p1"
    assert page.properties[0].value is True
    assert page.properties[1].value == "hi"


def test_delete_removes_file(tmp_path: Path) -> None:
    repo = MarkdownPageRepository(tmp_path)
    repo.create("To Delete", "")
    assert (tmp_path / "To Delete.md").exists()
    repo.delete(1)
    assert repo.get_by_id(1) is None
    assert not list(tmp_path.glob("*.md"))


def test_delete_nonexistent_no_error(tmp_path: Path) -> None:
    repo = MarkdownPageRepository(tmp_path)
    repo.delete(999)  # no raise


def test_skip_invalid_md_files(tmp_path: Path) -> None:
    (tmp_path / "valid.md").write_text("---\nid: 1\n---\nbody", encoding="utf-8")
    (tmp_path / "no_id.md").write_text("---\n---\nbody", encoding="utf-8")
    repo = MarkdownPageRepository(tmp_path)
    pages = repo.list_all()
    assert len(pages) == 1
    assert pages[0].title == "valid"


def test_skip_non_integer_id(tmp_path: Path) -> None:
    (tmp_path / "bad.md").write_text("---\nid: abc\n---\nbody", encoding="utf-8")
    repo = MarkdownPageRepository(tmp_path)
    assert repo.list_all() == []


def test_update_nonexistent_page_no_op(tmp_path: Path) -> None:
    repo = MarkdownPageRepository(tmp_path)
    repo.update(999, "X", "Y")


def test_update_same_title_overwrites_in_place(tmp_path: Path) -> None:
    repo = MarkdownPageRepository(tmp_path)
    repo.create("Same", "old")
    repo.update(1, "Same", "new")
    page = repo.get_by_id(1)
    assert page is not None
    assert page.content == "new"


def test_create_collision_appends_number(tmp_path: Path) -> None:
    repo = MarkdownPageRepository(tmp_path)
    repo.create("Dup", "first")
    repo.create("Dup", "second")
    pages = repo.list_all()
    assert len(pages) == 2
    titles = {p.title for p in pages}
    assert "Dup" in titles
    assert "Dup 1" in titles


def test_legacy_dict_properties(tmp_path: Path) -> None:
    content = "---\nid: 1\nproperties:\n  done: true\n  note: hello\n---\nbody"
    (tmp_path / "page.md").write_text(content, encoding="utf-8")
    repo = MarkdownPageRepository(tmp_path)
    page = repo.list_all()[0]
    assert len(page.properties) == 2
    prop_ids = {p.id for p in page.properties}
    assert "done" in prop_ids
    assert "note" in prop_ids


def test_properties_with_no_value_get_default(tmp_path: Path) -> None:
    content = '---\nid: 1\nproperties:\n- id: p1\n  name: Done\n  type: boolean\n---\nbody'
    (tmp_path / "page.md").write_text(content, encoding="utf-8")
    repo = MarkdownPageRepository(tmp_path)
    page = repo.list_all()[0]
    assert page.properties[0].value is False


def test_non_list_non_dict_properties_returns_empty(tmp_path: Path) -> None:
    content = '---\nid: 1\nproperties: "just a string"\n---\nbody'
    (tmp_path / "page.md").write_text(content, encoding="utf-8")
    repo = MarkdownPageRepository(tmp_path)
    page = repo.list_all()[0]
    assert page.properties == []


def test_safe_filename_strips_slashes(tmp_path: Path) -> None:
    repo = MarkdownPageRepository(tmp_path)
    page = repo.create("a/b\\c", "content")
    assert "/" not in page.title
    assert "\\" not in page.title


def test_list_skips_non_dict_items_in_property_list(tmp_path: Path) -> None:
    content = '---\nid: 1\nproperties:\n- id: p1\n  name: A\n  type: boolean\n  value: true\n- not_a_dict\n---\nbody'
    (tmp_path / "page.md").write_text(content, encoding="utf-8")
    repo = MarkdownPageRepository(tmp_path)
    page = repo.list_all()[0]
    assert len(page.properties) == 1


def test_list_all_skips_directory_matching_md_glob(tmp_path: Path) -> None:
    (tmp_path / "real.md").write_text("---\nid: 1\n---\nbody", encoding="utf-8")
    (tmp_path / "fake.md").mkdir()
    repo = MarkdownPageRepository(tmp_path)
    pages = repo.list_all()
    assert len(pages) == 1


def test_get_by_id_skips_directory_matching_md_glob(tmp_path: Path) -> None:
    (tmp_path / "real.md").write_text("---\nid: 1\n---\nbody", encoding="utf-8")
    (tmp_path / "fake.md").mkdir()
    repo = MarkdownPageRepository(tmp_path)
    assert repo.get_by_id(1) is not None


def test_update_skips_directory_matching_md_glob(tmp_path: Path) -> None:
    (tmp_path / "real.md").write_text("---\nid: 1\n---\nbody", encoding="utf-8")
    (tmp_path / "fake.md").mkdir()
    repo = MarkdownPageRepository(tmp_path)
    repo.update(1, "real", "updated")
    page = repo.get_by_id(1)
    assert page is not None
    assert page.content == "updated"


def test_delete_skips_directory_matching_md_glob(tmp_path: Path) -> None:
    (tmp_path / "real.md").write_text("---\nid: 1\n---\nbody", encoding="utf-8")
    (tmp_path / "fake.md").mkdir()
    repo = MarkdownPageRepository(tmp_path)
    repo.delete(1)
    assert repo.get_by_id(1) is None


def test_page_from_file_oserror_returns_none(tmp_path: Path) -> None:
    from unittest.mock import patch
    (tmp_path / "page.md").write_text("---\nid: 1\n---\nbody", encoding="utf-8")
    repo = MarkdownPageRepository(tmp_path)
    with patch.object(Path, "read_text", side_effect=OSError):
        pages = repo.list_all()
    assert pages == []
