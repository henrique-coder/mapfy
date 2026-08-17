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


def test_place_result_exposes_only_maps_url_for_navigation() -> None:
    place = PlaceResult(
        place_id="abc123",
        name="Central Cafe",
        image_url=(
            "https://streetviewpixels-pa.googleapis.com/v1/thumbnail"
            "?panoid=abc123&cb_client=search.gws-prod.gps&w=408&h=240&yaw=213.40585"
            "&pitch=0&thumbfov=100"
        ),
    )

    assert place.maps_url.startswith("https://www.google.com/maps/search/?")
    assert isinstance(place.image_url, str)
    assert "streetview" not in place.model_dump()
    assert "panoid" not in place.model_dump()


def test_image_url_changes_only_resolution() -> None:
    source_url = (
        "https://streetviewpixels-pa.googleapis.com/v1/thumbnail"
        "?panoid=abc123&cb_client=search.gws-prod.gps&w=408&h=240&yaw=213.40585"
        "&pitch=0&thumbfov=100"
    )

    image_url = Mapfy._streetview_url(source_url=source_url)

    assert image_url == (
        "https://streetviewpixels-pa.googleapis.com/v1/thumbnail"
        "?panoid=abc123&cb_client=search.gws-prod.gps&w=1920&h=1080&yaw=213.40585"
        "&pitch=0&thumbfov=100"
    )
