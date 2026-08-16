"""Google Maps client."""

import re
from typing import Self
from urllib.parse import urlencode

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


class Mapfy:
    """Query Google Maps and enrich matching locations with Street View data."""

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

        return [self._with_cover(place) for place in results]

    def _with_cover(self, place: PlaceResult) -> PlaceResult:
        if place.streetview.get("panoid"):
            return place.model_copy(update={"streetview": self._streetview_data(str(place.streetview["panoid"]))})

        if place.latitude is None or place.longitude is None:
            return place

        panoid = self._panoid(place.latitude, place.longitude)

        if panoid is None:
            return place

        return place.model_copy(update={"streetview": self._streetview_data(panoid)})

    @staticmethod
    def _streetview_data(panoid: str) -> dict[str, str]:
        return {
            "panoid": panoid,
            "image_url": (
                f"{STREETVIEW_BASE_URL}/thumbnail?panoid={panoid}"
                "&cb_client=search.gws-prod.gps&w=1920&h=1080"
                "&yaw=-10&pitch=0&thumbfov=100"
            ),
        }

    def _panoid(self, latitude: float, longitude: float) -> str | None:
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
        match = re.search(r'\[\d+,"([A-Za-z0-9_-]{16,64})"\]', response.text)

        return match.group(1) if match else None

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
