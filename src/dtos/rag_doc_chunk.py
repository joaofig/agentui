from typing import Self

from dtos.base import ReadOnlyDTO


class RagDocumentChunkDTO(ReadOnlyDTO):
    """A single chunk of a document stored in document_chunk."""

    rag_chunk_id: int = 0
    rag_doc_id: int = 0
    org_id: int = 0
    page_ini: int = 0
    page_end: int = 0
    ordinal: int = 0
    content: str = ""
    word_count: int = 0
    embedding: list[float] | None = None

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return cls(**data)

    def merge(self, other: RagDocumentChunkDTO) -> RagDocumentChunkDTO:
        return RagDocumentChunkDTO(
            rag_chunk_id=0,
            rag_doc_id=self.rag_doc_id,
            org_id=self.org_id,
            page_ini=min(self.page_ini, other.page_ini),
            page_end=max(self.page_end, other.page_end),
            ordinal=self.ordinal,
            content=self.content + " " + other.content,
            word_count=self.word_count + other.word_count,
            embedding=None,
        )
