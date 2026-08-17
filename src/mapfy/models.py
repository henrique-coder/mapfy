"""Models exposed by the library."""

from urllib.parse import unquote, urlencode

from pydantic import BaseModel, ConfigDict, Field, computed_field


class PlaceResult(BaseModel):
    """A single location candidate returned by Google Maps."""

    model_config = ConfigDict(frozen=True)

    place_id: str = Field(description="Google identifier for the place.")
    name: str = Field(description="Displayed place name.")
    category: str | None = Field(default=None, description="Primary category.")
    address: str | None = Field(default=None, description="Formatted address.")
    rating: float | None = Field(default=None, description="Average rating.")
    reviews_count: int | None = Field(default=None, description="Review count.")
    latitude: float | None = Field(default=None, description="Latitude in degrees.")
    longitude: float | None = Field(default=None, description="Longitude in degrees.")
    website: str | None = Field(default=None, description="Place website URL.")
    image_url: str | None = Field(default=None, description="Street View image URL.")

    @computed_field
    @property
    def maps_url(self) -> str:
        """Return a link that opens this place directly in Google Maps."""
        query = unquote(self.name)

        if self.address:
            query = f"{query}, {unquote(self.address)}"

        params = urlencode(
            {
                "api": "1",
                "query": query,
                "query_place_id": unquote(self.place_id),
            }
        )

        return f"https://www.google.com/maps/search/?{params}"


class SearchParams(BaseModel):
    """Normalized options used to build a Maps request."""

    model_config = ConfigDict(frozen=True)

    query: str = Field(description="Normalized Maps query.")
    language: str | None = Field(default=None, description="Optional BCP-47 language.")
    country: str | None = Field(default=None, description="Optional country code.")
