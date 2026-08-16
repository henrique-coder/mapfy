# Mapfy

Mapfy queries public Google Maps results, normalizes each candidate as a
`PlaceResult`, and builds ready-to-use Street View image links.

## What it returns

Each result can include `place_id`, `name`, `category`, `address`, `website`,
`streetview`, `rating`, `reviews_count`, `latitude`, and `longitude`.

Mapfy uses an internal Maps endpoint that Google does not document. Changes to
the response format may require a parser update.

## Public API

The client exposes two searches:

- `search()`: resolves an address, coordinates, or free-text location query.
- `search_places()`: finds establishments by name, category, or type.

## Installation

```bash
uv add mapfy
```

## Usage

```python
from mapfy import Mapfy

with Mapfy() as client:
    places = client.search_places(
        query="coffee shop",
        near="Seattle, WA",
        limit=10,
    )

for place in places:
    print(place.name, place.maps_url, place.streetview)
```

`near` is optional and accepts an address, a coordinate string (`"47.61,-122.33"`),
or a coordinate tuple (`(47.61, -122.33)`). `language` and `country` are optional;
when omitted, Google determines the request context.

`limit=None` returns every result received. A positive integer returns up to that
many results while preserving the order returned by Maps.

`search()` preserves every candidate returned by Maps, so ambiguous addresses do
not get reduced to an arbitrary first result.

```python
addresses = client.search("47.61, -122.33")
```

## Structure

```text
src/mapfy/
├── client.py
├── models.py
├── parser.py
├── common.py
└── __init__.py
```

## Development

```bash
uv sync --all-groups
uv run ruff format
uv run ruff check
uv run ty check
```
