from typing import Any, Optional


class Fixed(Exception):
    message: Optional[str] = None

    def __init__(self, *args: Any) -> None:
        super().__init__(self.message, *args)


class SearchQueriesNotFetched(Fixed):
    message = "HTTP: Bulk search query fetching failed."
