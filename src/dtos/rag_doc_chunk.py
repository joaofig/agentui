from dataclasses import dataclass


@dataclass
class RagDocumentChunkDTO:
    """A single chunk of a document stored in document_chunk."""

    rag_chunk_id: int = 0
    rag_doc_id: int = 0
    org_id: int = 0
    page_number: int = 1
    ordinal: int = 0
    content: str = ""
    company_id: int = 1
    embedding: list[float] | None = None

