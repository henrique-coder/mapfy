"""Google Maps client."""

from math import atan2, cos, degrees, radians, sin
from re import search
from typing import Self
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit, urlunsplit

from curl_cffi import requests

from mapfy.common import (
    ANTI_CACHE_HEADERS,
    BASE_URL,
    CHROME_IMPERSONATE,
    PB_MINIMAL,
    QueryBuilder,
    SearchLocation,
)
from mapfy.models import PlaceResult, SearchParams
from mapfy.parser import GoogleMapsParser


STREETVIEW_SEARCH_URL = "https://maps.googleapis.com/maps/api/js/GeoPhotoService.SingleImageSearch"
STREETVIEW_BASE_URL = "https://streetviewpixels-pa.googleapis.com/v1"
FULL_CIRCLE_DEGREES = 360.0


class Mapfy:
    """Query Google Maps and return normalized location results with images."""

    __slots__ = ("_parser", "_session")

    def __init__(self) -> None:
        """Create a browser-impersonating HTTP session for Maps requests."""
        self._parser = GoogleMapsParser()
        self._session: requests.Session = requests.Session(impersonate=CHROME_IMPERSONATE)
        self._session.headers.update(ANTI_CACHE_HEADERS)

    def search(
        self,
        query: str,
        near: SearchLocation | None = None,
        language: str | None = None,
        country: str | None = None,
        limit: int | None = None,
    ) -> list[PlaceResult]:
        """Resolve an address, coordinate pair, or free-text location query."""
        return self._results(query, near, language, country, limit)

    def search_places(
        self,
        query: str,
        near: SearchLocation | None = None,
        language: str | None = None,
        country: str | None = None,
        limit: int | None = None,
    ) -> list[PlaceResult]:
        """Find Maps places by establishment name, category, or type."""
        return self._results(query, near, language, country, limit)

    def _results(
        self,
        query: str,
        near: SearchLocation | None,
        language: str | None,
        country: str | None,
        limit: int | None,
    ) -> list[PlaceResult]:
        if limit is not None and limit < 1:
            message = "limit must be None or greater than or equal to 1"
            raise ValueError(message)

        results = self._search(query, near, language, country)

        results = results if limit is None else results[:limit]

        return [self._with_image(place) for place in results]

    def _with_image(self, place: PlaceResult) -> PlaceResult:
        if place.image_url:
            image_url = self._streetview_url(source_url=place.image_url)

            return place.model_copy(update={"image_url": image_url})

        if place.latitude is None or place.longitude is None:
            return place

        panorama = self._panorama(place.latitude, place.longitude)

        if panorama is None:
            return place

        panoid, yaw = panorama
        image_url = self._streetview_url(panoid=panoid, yaw=yaw)

        return place.model_copy(update={"image_url": image_url})

    @staticmethod
    def _streetview_url(
        panoid: str | None = None,
        source_url: str | None = None,
        yaw: float | None = None,
    ) -> str:
        if source_url:
            parsed = urlsplit(unquote(source_url))
            query = dict(parse_qsl(parsed.query, keep_blank_values=True))
            query["w"] = "1920"
            query["h"] = "1080"

            return unquote(urlunsplit(parsed._replace(query=urlencode(query))))

        if panoid is None or yaw is None:
            message = "panoid and yaw are required when source_url is absent"
            raise ValueError(message)

        camera_yaw = Mapfy._number(yaw)

        return (
            f"{STREETVIEW_BASE_URL}/thumbnail?panoid={panoid}"
            "&cb_client=search.gws-prod.gps&w=1920&h=1080"
            f"&yaw={camera_yaw}&pitch=0&thumbfov=100"
        )

    def _panorama(self, latitude: float, longitude: float) -> tuple[str, float] | None:
        pb = (
            f"!1m5!1sapiv3!5sUS!11m2!1m1!1b0!2m4!1m2!3d{latitude}!4d{longitude}!2d50"
            "!3m10!2m2!1sen!2sUS!9m1!1e2!11m4!1m3!1e2!2b1!3e2"
            "!4m10!1e1!1e2!1e3!1e4!1e8!1e6!5m1!1e2!6m1!1e2"
        )
        response = self._session.get(
            STREETVIEW_SEARCH_URL,
            params={"pb": pb, "callback": "_xdc_._v2mub5"},
        )
        response.raise_for_status()
        panoid = search(r'\[\d+,"([A-Za-z0-9_-]{16,64})"\]', response.text)
        coordinates = search(
            r"\[null,null,(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)\]",
            response.text,
        )

        if panoid is None or coordinates is None:
            return None

        panorama_latitude = float(coordinates.group(1))
        panorama_longitude = float(coordinates.group(2))
        yaw = self._bearing(
            panorama_latitude,
            panorama_longitude,
            latitude,
            longitude,
        )

        return panoid.group(1), yaw

    @staticmethod
    def _bearing(
        origin_latitude: float,
        origin_longitude: float,
        target_latitude: float,
        target_longitude: float,
    ) -> float:
        origin = radians(origin_latitude)
        target = radians(target_latitude)
        longitude_delta = radians(target_longitude - origin_longitude)
        y = sin(longitude_delta) * cos(target)
        x = cos(origin) * sin(target) - sin(origin) * cos(target) * cos(longitude_delta)

        return (degrees(atan2(y, x)) + FULL_CIRCLE_DEGREES) % FULL_CIRCLE_DEGREES

    @staticmethod
    def _number(value: float) -> str:
        return f"{value:.6f}".rstrip("0").rstrip(".")

    def _search(
        self,
        query: str,
        near: SearchLocation | None,
        language: str | None,
        country: str | None,
    ) -> list[PlaceResult]:
        params = SearchParams(
            query=QueryBuilder.query(query, near),
            language=language,
            country=country,
        )
        response = self._session.get(self._url(params))
        response.raise_for_status()

        return self._parser.parse(response.text)

    @staticmethod
    def _url(params: SearchParams) -> str:
        values = {"tbm": "map", "pb": PB_MINIMAL, "q": params.query}

        if params.language:
            values["hl"] = params.language

        if params.country:
            values["gl"] = params.country

        return f"{BASE_URL}?{urlencode(values)}"

    def _close(self) -> None:
        """Close the HTTP session."""
        self._session.close()

    def __enter__(self) -> Self:
        """Return this client for context-manager usage."""
        return self

    def __exit__(self, *args: object) -> None:
        """Close the underlying session after context-manager usage."""
        self._close()
