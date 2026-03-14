"""Page-related use case errors."""


class PageNotFoundError(Exception):
    """Raised when a page with the given id does not exist."""

    def __init__(
        self,
        message: str | None = None,
        *,
        page_id: int | None = None,
    ) -> None:
        if message is not None:
            detail = message
        elif page_id is not None:
            detail = f"Page with id {page_id} not found."
        else:
            detail = "Page not found."
        super().__init__(detail)
        self.message = detail
