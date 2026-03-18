"""Unit tests for application error classes (constructor branches)."""


from fern.application.errors.page_errors import PageNotFoundError
from fern.application.errors.property_errors import (
    PropertyAlreadyExistsError,
    PropertyAlreadyExistsOnPageError,
    PropertyNotFoundError,
    PropertyNotFoundOnPageError,
)
from fern.application.errors.vault_errors import VaultNotFoundError


# --- PageNotFoundError ---


def test_page_not_found_error_with_message() -> None:
    error = PageNotFoundError(message="Custom message")
    assert str(error) == "Custom message"
    assert error.message == "Custom message"


def test_page_not_found_error_with_page_id() -> None:
    error = PageNotFoundError(page_id=42)
    assert "42" in str(error)
    assert "not found" in str(error)
    assert error.message == "Page with id 42 not found."


def test_page_not_found_error_without_message_or_page_id() -> None:
    error = PageNotFoundError()
    assert str(error) == "Page not found."
    assert error.message == "Page not found."


# --- PropertyNotFoundError ---


def test_property_not_found_error_with_message() -> None:
    error = PropertyNotFoundError(message="Custom")
    assert str(error) == "Custom"
    assert error.message == "Custom"


def test_property_not_found_error_with_property_id_and_database_name() -> None:
    error = PropertyNotFoundError(property_id="p1", database_name="DB")
    assert "p1" in str(error)
    assert "DB" in str(error)
    assert error.message == "Property 'p1' not found in database 'DB'."


def test_property_not_found_error_with_property_id_only() -> None:
    error = PropertyNotFoundError(property_id="p1")
    assert "p1" in str(error)
    assert error.message == "Property 'p1' not found in the schema."


def test_property_not_found_error_without_args() -> None:
    error = PropertyNotFoundError()
    assert str(error) == "Property not found."
    assert error.message == "Property not found."


# --- PropertyAlreadyExistsError ---


def test_property_already_exists_error_with_message() -> None:
    error = PropertyAlreadyExistsError(message="Custom")
    assert str(error) == "Custom"
    assert error.message == "Custom"


def test_property_already_exists_error_with_property_id_and_database_name() -> None:
    error = PropertyAlreadyExistsError(property_id="p1", database_name="DB")
    assert "p1" in str(error)
    assert "DB" in str(error)
    assert "already exists" in str(error)


def test_property_already_exists_error_with_property_id_only() -> None:
    error = PropertyAlreadyExistsError(property_id="p1")
    assert "p1" in str(error)
    assert error.message == "A property with id 'p1' already exists in the schema."


def test_property_already_exists_error_without_args() -> None:
    error = PropertyAlreadyExistsError()
    assert "already exists" in str(error)
    assert error.message == "A property with that id already exists."


# --- PropertyAlreadyExistsOnPageError ---


def test_property_already_exists_on_page_error_with_message() -> None:
    error = PropertyAlreadyExistsOnPageError(message="Custom")
    assert str(error) == "Custom"
    assert error.message == "Custom"


def test_property_already_exists_on_page_error_with_property_id_and_page_id() -> None:
    error = PropertyAlreadyExistsOnPageError(property_id="p1", page_id=7)
    assert "p1" in str(error)
    assert "7" in str(error)
    assert error.message == "Property 'p1' already exists on page (id 7)."


def test_property_already_exists_on_page_error_with_property_id_only() -> None:
    error = PropertyAlreadyExistsOnPageError(property_id="p1")
    assert "p1" in str(error)
    assert error.message == "Property 'p1' already exists on this page."


def test_property_already_exists_on_page_error_without_args() -> None:
    error = PropertyAlreadyExistsOnPageError()
    assert "already exists" in str(error)
    assert error.message == "A property with that id already exists on this page."


# --- PropertyNotFoundOnPageError ---


def test_property_not_found_on_page_error_with_message() -> None:
    error = PropertyNotFoundOnPageError(message="Custom")
    assert str(error) == "Custom"
    assert error.message == "Custom"


def test_property_not_found_on_page_error_with_property_id_and_page_id() -> None:
    error = PropertyNotFoundOnPageError(property_id="p1", page_id=7)
    assert "p1" in str(error)
    assert "7" in str(error)
    assert error.message == "Property 'p1' not found on page (id 7)."


def test_property_not_found_on_page_error_with_property_id_only() -> None:
    error = PropertyNotFoundOnPageError(property_id="p1")
    assert "p1" in str(error)
    assert error.message == "Property 'p1' not found on this page."


def test_property_not_found_on_page_error_without_args() -> None:
    error = PropertyNotFoundOnPageError()
    assert "not found" in str(error)
    assert error.message == "Property not found on this page."


# --- VaultNotFoundError ---


def test_vault_not_found_error_with_message() -> None:
    error = VaultNotFoundError(message="Custom")
    assert str(error) == "Custom"
    assert error.message == "Custom"


def test_vault_not_found_error_with_path() -> None:
    error = VaultNotFoundError(path="/some/path")
    assert "/some/path" in str(error)
    assert error.message == "Vault not found or invalid: /some/path"


def test_vault_not_found_error_without_args() -> None:
    error = VaultNotFoundError()
    assert str(error) == "Invalid or missing vault."
    assert error.message == "Invalid or missing vault."
