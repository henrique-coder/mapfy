from mapfy import Mapfy, PlaceResult
from mapfy.common import QueryBuilder
from mapfy.parser import GoogleMapsParser


def test_query_builder_accepts_coordinates() -> None:
    assert QueryBuilder.query("cafeteria", (-23.5, -46.6)) == ("cafeteria near -23.5,-46.6")


def test_place_result_builds_maps_url() -> None:
    place = PlaceResult(
        place_id="abc123",
        name="Central Cafe",
        address="10 Main St, Springfield",
    )

    assert "query_place_id=abc123" in place.maps_url
    assert "Central" in place.maps_url


def test_parser_accepts_empty_results() -> None:
    assert GoogleMapsParser().parse("[]") == []


def test_client_exposes_only_search_operations() -> None:
    public_methods = {name for name in dir(Mapfy) if not name.startswith("_")}

    assert public_methods == {"search", "search_places"}
