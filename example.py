"""Mapfy usage example."""

from rich.console import Console

from mapfy import Mapfy


console = Console(soft_wrap=True)

client = Mapfy()

result1 = client.search(
    query="1600 Pennsylvania Avenue NW, Washington, DC",
    language="en-US",
    limit=1,
)
console.print(result1)

result2 = client.search_places(
    query="coffee shop",
    near="Seattle, WA",
    language="en-US",
    limit=1,
)
console.print(result2)
