"""Property-related use case errors."""


class PropertyNotFoundError(Exception):
    """Raised when a property with the given id is not in the schema."""

    def __init__(
        self,
        message: str | None = None,
        *,
        property_id: str | None = None,
        database_name: str | None = None,
    ) -> None:
        if message is not None:
            detail = message
        elif property_id is not None and database_name is not None:
            detail = (
                f"Property '{property_id}' not found in database '{database_name}'."
            )
        elif property_id is not None:
            detail = f"Property '{property_id}' not found in the schema."
        else:
            detail = "Property not found."
        super().__init__(detail)
        self.message = detail


class PropertyAlreadyExistsError(Exception):
    """Raised when adding a property whose id already exists in the schema."""

    def __init__(
        self,
        message: str | None = None,
        *,
        property_id: str | None = None,
        database_name: str | None = None,
    ) -> None:
        if message is not None:
            detail = message
        elif property_id is not None and database_name is not None:
            detail = f"A property with id '{property_id}' already exists in database '{database_name}'."
        elif property_id is not None:
            detail = f"A property with id '{property_id}' already exists in the schema."
        else:
            detail = "A property with that id already exists."
        super().__init__(detail)
        self.message = detail


class PropertyAlreadyExistsOnPageError(Exception):
    """Raised when adding a property to a page that already has that property id."""

    def __init__(
        self,
        message: str | None = None,
        *,
        property_id: str | None = None,
        page_id: int | None = None,
    ) -> None:
        if message is not None:
            detail = message
        elif property_id is not None and page_id is not None:
            detail = f"Property '{property_id}' already exists on page (id {page_id})."
        elif property_id is not None:
            detail = f"Property '{property_id}' already exists on this page."
        else:
            detail = "A property with that id already exists on this page."
        super().__init__(detail)
        self.message = detail


class PropertyNotFoundOnPageError(Exception):
    """Raised when updating a property that does not exist on the given page."""

    def __init__(
        self,
        message: str | None = None,
        *,
        property_id: str | None = None,
        page_id: int | None = None,
    ) -> None:
        if message is not None:
            detail = message
        elif property_id is not None and page_id is not None:
            detail = f"Property '{property_id}' not found on page (id {page_id})."
        elif property_id is not None:
            detail = f"Property '{property_id}' not found on this page."
        else:
            detail = "Property not found on this page."
        super().__init__(detail)
        self.message = detail
