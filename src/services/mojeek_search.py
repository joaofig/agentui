"""
Mojeek web search for Haystack Agents.

Provides:
  * ``MojeekWebSearch``   – a Haystack component (usable in pipelines or wrapped as a tool)
  * ``create_mojeek_search_tool`` – returns a ``ComponentTool`` ready to inject into ``Agent(tools=[...])``

API reference: https://www.mojeek.com/support/api/search/request_parameters.html
"""

from __future__ import annotations

import logging
from typing import Any

import requests
from haystack import Document, component
from haystack.tools import ComponentTool
from haystack.utils import Secret, deserialize_secrets_inplace

try:  # Haystack 2.x / 3.x both expose these at top level; keep a fallback path just in case.
    from haystack import default_from_dict, default_to_dict
except ImportError:  # pragma: no cover
    from haystack.core.serialization import default_from_dict, default_to_dict

logger = logging.getLogger(__name__)

MOJEEK_API_URL = "https://api.mojeek.com/search"
MAX_DOMAIN_FILTERS = 25  # Mojeek limit for `fi` / `fe`


class MojeekError(RuntimeError):
    """Raised when the Mojeek API returns an error or an unexpected payload."""


@component
class MojeekWebSearch:
    """
    Searches the web with the Mojeek Search API and returns results as Haystack Documents.

    Usage:
    ```python
    search = MojeekWebSearch(top_k=5, search_params={"lb": "EN", "lbb": 100})
    result = search.run(query="What is mojeek?")
    result["documents"], result["links"]
    ```
    """

    def __init__(
        self,
        api_key: Secret = Secret.from_env_var("MOJEEK_API_KEY"),
        top_k: int = 10,
        allowed_domains: list[str] | None = None,
        excluded_domains: list[str] | None = None,
        search_params: dict[str, Any] | None = None,
        api_url: str = MOJEEK_API_URL,
        timeout: float = 15.0,
        *,
        raise_on_failure: bool = True,
    ) -> None:
        """
        :param api_key: Mojeek API key. Defaults to the ``MOJEEK_API_KEY`` environment variable.
        :param top_k: Default number of results to return (Mojeek ``t``).
        :param allowed_domains: Restrict results to these domains (Mojeek ``fi``, max 25).
            Prefix a domain with ``.`` to include its subdomains.
        :param excluded_domains: Exclude these domains (Mojeek ``fe``, max 25).
        :param search_params: Extra Mojeek request parameters, e.g. ``{"lb": "EN", "lbb": 100,
            "rb": "PT", "rbb": 10, "safe": 1, "since": "month", "dlen": 300}``.
        :param api_url: Mojeek search endpoint.
        :param timeout: HTTP timeout in seconds.
        :param raise_on_failure: If ``False``, API/network errors are logged and an empty result is
            returned instead of raising (handy for agents that should keep going).
        """
        for name, domains in (("allowed_domains", allowed_domains), ("excluded_domains", excluded_domains)):
            if domains and len(domains) > MAX_DOMAIN_FILTERS:
                raise ValueError(f"Mojeek supports at most {MAX_DOMAIN_FILTERS} {name}, got {len(domains)}.")

        self.api_key = api_key
        self.top_k = top_k
        self.allowed_domains = allowed_domains
        self.excluded_domains = excluded_domains
        self.search_params = search_params or {}
        self.api_url = api_url
        self.timeout = timeout
        self.raise_on_failure = raise_on_failure
        self._session: requests.Session | None = None

    def warm_up(self) -> None:
        """Create the HTTP session (idempotent)."""
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({"Accept": "application/json"})

    # ----------------------------------------------------------------- serialization
    def to_dict(self) -> dict[str, Any]:
        return default_to_dict(
            self,
            api_key=self.api_key.to_dict(),
            top_k=self.top_k,
            allowed_domains=self.allowed_domains,
            excluded_domains=self.excluded_domains,
            search_params=self.search_params,
            api_url=self.api_url,
            timeout=self.timeout,
            raise_on_failure=self.raise_on_failure,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MojeekWebSearch":
        data = {**data, "init_parameters": dict(data.get("init_parameters", {}))}
        deserialize_secrets_inplace(data["init_parameters"], keys=["api_key"])
        return default_from_dict(cls, data)

    # ----------------------------------------------------------------- run
    @component.output_types(documents=list[Document], links=list[str])
    def run(self, query: str, top_k: int | None = None) -> dict[str, Any]:
        """
        Search the web with Mojeek.

        :param query: The web search query. Use concise keywords; search operators such as
            `site:example.com` are supported.
        :param top_k: Optional number of results to return (1-20). Defaults to the configured value.
        :returns: A dict with `documents` (one per result, snippet as content) and `links` (result URLs).
        """
        print(query)
        if not query or not query.strip():
            return {"documents": [], "links": []}

        self.warm_up()
        params = self._build_params(query.strip(), top_k)

        try:
            payload = self._request(params)
        except MojeekError:
            if self.raise_on_failure:
                raise
            logger.warning("Mojeek search failed for query %r", query, exc_info=True)
            return {"documents": [], "links": []}

        documents = [self._to_document(r, rank) for rank, r in enumerate(payload.get("results", []), start=1)]
        documents = [d for d in documents if d is not None]
        return {"documents": documents, "links": [d.meta["url"] for d in documents]}

    # ----------------------------------------------------------------- helpers
    def _build_params(self, query: str, top_k: int | None) -> dict[str, Any]:
        params: dict[str, Any] = {**self.search_params, "t": max(1, int(top_k or self.top_k))}
        if self.allowed_domains:
            params["fi"] = ",".join(self.allowed_domains)
        if self.excluded_domains:
            params["fe"] = ",".join(self.excluded_domains)
        # Always enforced, cannot be overridden by search_params.
        params.update({"q": query, "fmt": "json", "api_key": self.api_key.resolve_value()})
        return params

    def _request(self, params: dict[str, Any]) -> dict[str, Any]:
        assert self._session is not None
        try:
            resp = self._session.get(self.api_url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            body = resp.json()
        except requests.Timeout as e:
            raise MojeekError(f"Mojeek request timed out after {self.timeout}s") from e
        except requests.HTTPError as e:
            # Never leak the api_key that sits in the query string.
            raise MojeekError(f"Mojeek HTTP {e.response.status_code}: {e.response.text[:200]}") from None
        except (requests.RequestException, ValueError) as e:
            raise MojeekError(f"Mojeek request failed: {type(e).__name__}") from e

        response = body.get("response") if isinstance(body, dict) else None
        if not isinstance(response, dict):
            raise MojeekError("Unexpected Mojeek payload: missing 'response' object")
        status = str(response.get("status", ""))
        if status != "OK":
            # e.g. "ERROR: Daily Limit Reached"
            raise MojeekError(f"Mojeek API error: {status or 'unknown status'}")
        return response

    @staticmethod
    def _to_document(result: dict[str, Any], rank: int) -> Document | None:
        url = result.get("url")
        if not url:
            return None
        meta: dict[str, Any] = {"url": url, "title": result.get("title", ""), "rank": rank, "source": "mojeek"}
        for key in ("date", "cdate", "score", "cfs", "size"):
            if result.get(key) is not None:
                meta[key] = result[key]
        return Document(content=result.get("desc") or result.get("title") or "", meta=meta)


# --------------------------------------------------------------------------- tool
def format_results_for_llm(documents: list[Document]) -> str:
    """Compact, citation-friendly rendering of search results for the LLM's context."""
    if not documents:
        return "No results found."
    blocks = []
    for doc in documents:
        m = doc.meta
        line = f"[{m.get('rank', '?')}] {m.get('title') or '(untitled)'}\nURL: {m.get('url')}"
        if m.get("date"):
            line += f"\nDate: {m['date']}"
        line += f"\n{(doc.content or '').strip()}"
        blocks.append(line)
    return "\n\n".join(blocks)


def create_mojeek_search_tool(
    name: str = "web_search",
    description: str | None = None,
    search: MojeekWebSearch | None = None,
    **search_kwargs: Any,
) -> ComponentTool:
    """
    Build a ``ComponentTool`` around ``MojeekWebSearch`` for a Haystack ``Agent``.

    :param name: Tool name the LLM sees.
    :param description: Tool description the LLM sees (a sensible default is provided).
    :param search: An existing ``MojeekWebSearch``; otherwise one is built from ``search_kwargs``.
    :param search_kwargs: Forwarded to ``MojeekWebSearch`` (e.g. ``top_k=5, search_params={...}``).
    """
    component_instance = search or MojeekWebSearch(**search_kwargs)
    return ComponentTool(
        component=component_instance,
        name=name,
        description=description
        or (
            "Search the public web with the Mojeek search engine. Use it for current events, facts that may "
            "have changed, or anything you are unsure about. Input a concise keyword query. Returns numbered "
            "results with title, URL and snippet; cite URLs when using them."
        ),
        outputs_to_string={"source": "documents", "handler": format_results_for_llm},
    )