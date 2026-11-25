from dataclasses import dataclass
from typing import Self

from dtos.base import ReadOnlyDTO


@dataclass
class RagDocumentChunkDTO(ReadOnlyDTO):
    """A single chunk of a document stored in document_chunk."""

    rag_chunk_id: int = 0
    rag_doc_id: int = 0
    org_id: int = 0
    page_number: int = 1
    ordinal: int = 0
    content: str = ""
    embedding: list[float] | None = None

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return cls(**data)
