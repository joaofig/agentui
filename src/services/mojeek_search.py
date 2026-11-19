import os
from typing import Annotated

import httpx
from haystack.tools import tool

MOJEEK_SEARCH_URL = "https://api.mojeek.com/search"
MAX_RESULTS = 20


@tool
async def mojeek_search(
    query: Annotated[str, "The web search query"],
    count: Annotated[int, f"Number of results to return (1-{MAX_RESULTS})"] = 5,
) -> str:
    """Search the web with Mojeek and return the top results.

    Args:
        query: The web search query.
        count: Number of results to return, clamped to 1..MAX_RESULTS.

    Returns:
        The results as a numbered list of title, URL and snippet.

    Raises:
        RuntimeError: If the API key is missing or Mojeek reports an error.
        httpx.HTTPError: If the HTTP request fails.
    """
    try:
        api_key = os.environ["MOJEEK_API_KEY"]
    except KeyError as exc:
        raise RuntimeError("MOJEEK_API_KEY is not configured") from exc

    params = {
        "q": query,
        "api_key": api_key,
        "fmt": "json",
        "t": max(1, min(count, MAX_RESULTS)),
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(MOJEEK_SEARCH_URL, params=params)
        response.raise_for_status()

    payload = response.json()["response"]
    if payload["status"] != "OK":
        raise RuntimeError(f"Mojeek search failed: {payload['status']}")

    results = payload.get("results", [])
    if not results:
        return f"No results found for '{query}'."
    return "\n\n".join(
        f"{i}. {r.get('title', '')}\n{r['url']}\n{r.get('desc', '')}"
        for i, r in enumerate(results, start=1)
    )
