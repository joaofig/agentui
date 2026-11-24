from dataclasses import dataclass, field
from typing import Any


@dataclass
class SearchHit:
    """Result of a search in the document repository."""

    chunk_id: int
    document_id: int
    file_name: str
    title: str
    page: int
    ordinal: int
    content: str
    score: float = 0.0
    search_type: str = "hybrid"  # "vector", "keyword", or "hybrid"
    metadata: dict[str, Any] = field(default_factory=dict)
