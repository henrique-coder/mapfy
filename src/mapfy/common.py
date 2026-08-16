"""Shared query types and constants."""

from collections.abc import Mapping, Sequence
from typing import Final, TypeAlias, cast


BASE_URL: Final[str] = "https://www.google.com/search"
CHROME_IMPERSONATE: Final[str] = "chrome"
PB_MINIMAL: Final[str] = "!7i20!10b1"
ANTI_CACHE_HEADERS: Final[dict[str, str]] = {
    "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}
Coordinate: TypeAlias = tuple[float, float]
SearchLocation: TypeAlias = str | Coordinate


class QueryBuilder:
    """Build normalized Google Maps search queries."""

    @staticmethod
    def location(value: SearchLocation) -> str:
        """Convert an address or coordinate pair to query text."""
        if isinstance(value, tuple):
            latitude, longitude = value

            return f"{latitude},{longitude}"

        return value.strip()

    @classmethod
    def query(cls, text: str, near: SearchLocation | None = None) -> str:
        """Combine a search term with an optional location."""
        query = text.strip()

        if not query:
            message = "query must not be empty"

            raise ValueError(message)

        location = cls.location(near) if near is not None else ""

        return f"{query} near {location}" if location else query

    @staticmethod
    def nested(data: object, *keys: int | str, default: object = None) -> object:
        """Read a nested JSON value without raising for missing keys."""
        current = data

        for key in keys:
            try:
                if isinstance(current, Sequence) and not isinstance(current, str) and isinstance(key, int):
                    current = current[key]
                elif isinstance(current, Mapping):
                    current = cast("Mapping[int | str, object]", current).get(key, default)
                else:
                    return default
            except (IndexError, KeyError, TypeError):
                return default

        return current if current is not None else default
