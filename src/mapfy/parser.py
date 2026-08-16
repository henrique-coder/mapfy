"""Parser for Google's internal Maps response format."""

from typing import Final
from urllib.parse import parse_qs, unquote, urlsplit

from orjson import loads as load_json

from mapfy.common import QueryBuilder
from mapfy.models import PlaceResult


PREFIXES: Final[tuple[str, ...]] = (")]}'", ")]}'\n")
MIN_PLACE_FIELDS: Final[int] = 15
PLACE_NAME_INDEX: Final[int] = 11


class GoogleMapsParser:
    """Decode raw Maps responses into validated place models."""

    def parse(self, raw_data: str) -> list[PlaceResult]:
        """Parse a raw response and return all place cards found in it."""
        decoded = load_json(self._payload(raw_data))
        data = decoded if isinstance(decoded, list) else []

        return [place for info in self._cards(data) if (place := self._place(info)) is not None]

    @staticmethod
    def _payload(raw_data: str) -> str:
        if raw_data.startswith(")]"):
            return GoogleMapsParser._strip(raw_data)

        if '{"c":' not in raw_data:
            return raw_data

        start = raw_data.find('{"c":')
        end = raw_data.rfind("}")

        if start == -1 or end == -1:
            return raw_data

        outer = load_json(raw_data[start : end + 1])

        return GoogleMapsParser._strip(outer.get("d", ""))

    @staticmethod
    def _strip(data: str) -> str:
        for prefix in PREFIXES:
            if data.startswith(prefix):
                return data[len(prefix) :]

        return data

    @classmethod
    def _place(cls, info: list[object]) -> PlaceResult | None:
        if len(info) < MIN_PLACE_FIELDS:
            return None

        name = cls._string(QueryBuilder.nested(info, PLACE_NAME_INDEX))

        if name is None:
            return None

        formatted_address = cls._string(QueryBuilder.nested(info, 18))
        address = [value for value in cls._list(QueryBuilder.nested(info, 2)) if isinstance(value, str)]
        reviews = cls._list(QueryBuilder.nested(info, 4))
        coordinates = cls._list(QueryBuilder.nested(info, 9))
        categories = cls._list(QueryBuilder.nested(info, 13))
        website = cls._list(QueryBuilder.nested(info, 7))

        return PlaceResult(
            place_id=str(QueryBuilder.nested(info, 10, default="")),
            name=name,
            category=cls._string(categories[0]) if categories else None,
            address=formatted_address or ", ".join(address) or None,
            rating=cls._float(QueryBuilder.nested(reviews, 7)),
            reviews_count=cls._integer(QueryBuilder.nested(reviews, 8)),
            latitude=cls._float(QueryBuilder.nested(coordinates, 2)),
            longitude=cls._float(QueryBuilder.nested(coordinates, 3)),
            website=cls._url(QueryBuilder.nested(website, 0)),
            streetview=cls._streetview(info),
        )

    @classmethod
    def _cards(cls, data: list[object]) -> list[list[object]]:
        candidates = [QueryBuilder.nested(data, 0, 1, default=[])] + [item for item in data if isinstance(item, list)]

        for candidate in candidates:
            if not isinstance(candidate, list):
                continue

            cards = [info for item in candidate if isinstance(item, list) and (info := cls._info(item)) is not None]

            if cards:
                return cards

        return []

    @classmethod
    def _info(cls, item: list[object]) -> list[object] | None:
        for index in (14, 1):
            info = QueryBuilder.nested(item, index)

            if (
                isinstance(info, list)
                and len(info) > PLACE_NAME_INDEX
                and cls._string(QueryBuilder.nested(info, PLACE_NAME_INDEX))
            ):
                return info

        return None

    @staticmethod
    def _list(value: object) -> list[object]:
        return value if isinstance(value, list) else []

    @staticmethod
    def _string(value: object) -> str | None:
        return value if isinstance(value, str) and value else None

    @classmethod
    def _url(cls, value: object) -> str | None:
        result = cls._string(value)
        return unquote(result) if result is not None else None

    @classmethod
    def _streetview(cls, info: list[object]) -> dict[str, str]:
        for value in cls._strings(info):
            if "streetviewpixels-pa.googleapis.com/v1/thumbnail" not in value:
                continue

            parsed = urlsplit(unquote(value))
            query = parse_qs(parsed.query)
            panoid = query.get("panoid", [""])[0]

            if panoid:
                return {
                    "panoid": panoid,
                    "url": unquote(value),
                }

        return {}

    @classmethod
    def _strings(cls, value: object) -> list[str]:
        if isinstance(value, str):
            return [value]

        if isinstance(value, list):
            values: list[str] = []

            for item in value:
                values.extend(cls._strings(item))

            return values

        return []

    @staticmethod
    def _float(value: object) -> float | None:
        if isinstance(value, (int, float, str)) and not isinstance(value, bool):
            try:
                return float(value)
            except ValueError:
                return None

        return None

    @staticmethod
    def _integer(value: object) -> int | None:
        if isinstance(value, (int, str)) and not isinstance(value, bool):
            try:
                return int(value)
            except ValueError:
                return None

        return None
