import asyncio

import pymupdf
from beartype import beartype
from loguru import logger

from repositories.postgres.rag_document import RagDocumentRepository
from src.dtos.rag_doc_chunk import RagDocumentChunkDTO
from src.dtos.rag_document import RagDocumentDTO
from src.dtos.search_hit import SearchHit
from src.repositories.postgres.rag_doc_chunk import RagDocumentChunkRepository
from src.services.embeddings import embed_query, embed_texts_async
from src.services.pdf import extract_paragraphs


class RagService:
    """High-level service providing RAG operations against PostgreSQL knowledge base."""

    def __init__(self) -> None:
        self.repository = RagDocumentChunkRepository()

    async def _index_pdf(self, document: RagDocumentDTO):
        doc: pymupdf.PdfDocument = pymupdf.open(stream=document.content, filetype="pdf")
        paragraphs = extract_paragraphs(doc)

        embeddings = await embed_texts_async(
            [str(paragraph["text"]) for paragraph in paragraphs]
        )

        chunks = [
            RagDocumentChunkDTO(
                rag_chunk_id=0,
                rag_doc_id=document.rag_doc_id,
                org_id=document.org_id,
                page_number=int(paragraph.get("page", 0)),
                ordinal=ordinal,
                content=str(paragraph.get("text", "")),
                embedding=embedding,
            )
            for ordinal, (paragraph, embedding) in enumerate(
                zip(paragraphs, embeddings, strict=True)
            )
        ]
        ids = await self.repository.insert(chunks)
        logger.info(f"Inserted {len(ids)} chunks")

    async def index_document(self, document: RagDocumentDTO) -> None:
        match document.content_type:
            case "application/pdf":
                await self._index_pdf(document)
        pass

    @beartype
    async def search(self, org_id: int, query: str, limit: int = 5) -> list[SearchHit]:
        """Perform hybrid search with fallback to keyword search."""
        logger.info(f"Searching for '{query}'")
        if not query or not query.strip():
            return []

        cleaned_query = query.strip()
        query_embedding: list[float] | None = None

        try:
            query_embedding = embed_query(cleaned_query)
        except Exception as exc:  # noqa: BLE001 - degrade gracefully to keyword search
            logger.warning(
                f"Failed to generate embedding for query '{cleaned_query}': {exc}. "
                "Falling back to keyword search."
            )

        try:
            return await self.repository.hybrid_search(
                org_id=org_id,
                query=cleaned_query,
                query_embedding=query_embedding,
                limit=limit,
            )
        except Exception as exc:  # noqa: BLE001 - degrade gracefully to keyword search
            logger.error(
                f"Hybrid search failed: {exc}. Attempting keyword-only search."
            )
            return await self.repository.search_keyword(
                org_id=org_id,
                query=cleaned_query, limit=limit
            )

    @beartype
    def search_and_format(self, org_id: int, query: str, limit: int = 5) -> str:
        """Search the knowledge base and format findings as structured LLM context."""
        hits = asyncio.run(self.search(org_id, query, limit=limit))
        if not hits:
            return (
                "No relevant documents found in the knowledge base for "
                f"query: '{query}'."
            )

        formatted_results = [
            f"Found {len(hits)} relevant passage(s) in PostgreSQL Knowledge Base:\n"
        ]
        for i, hit in enumerate(hits, start=1):
            source_info = (
                f"Document #{hit.document_id}: '{hit.title or hit.file_name}' "
                f"(File: {hit.file_name}, Page: {hit.page})"
            )
            formatted_results.append(
                f"[{i}] {source_info}\n"
                f"Relevance Score: {hit.score:.4f} (Type: {hit.search_type})\n"
                f"Content:\n{hit.content.strip()}\n"
            )

        return "\n---\n".join(formatted_results)

    @beartype
    async def get_document_details_formatted(self, document_id: int) -> str:
        """Retrieve and format all chunks of a document."""
        chunks = await self.repository.list(document_id)
        if not chunks:
            return f"No chunks found for Document ID {document_id}."

        lines = [f"Document ID {document_id} Chunks ({len(chunks)}):"]
        for c in chunks:
            lines.append(
                f"\n[Page {c.page_number}, Chunk #{c.ordinal}]:\n{c.content.strip()}"
            )
        return "\n".join(lines)

    @beartype
    async def list_documents_formatted(self, org_id: int, limit: int = 50) -> str:
        """Format the list of indexed documents in the database."""
        repository = RagDocumentRepository()
        docs = await repository.list(org_id)
        if not docs:
            return (
                "No documents are currently indexed in the PostgreSQL knowledge base."
            )
        docs = docs[:limit]

        lines = [f"Indexed Documents ({len(docs)}):"]
        for d in docs:
            lines.append(
                f"- ID: {d.rag_doc_id} | Title: '{d.title}' | File: '{d.file_name}' | "
                f"Pages: {d.page_count} | Chunks: {d.chunk_count} | Status: {d.status}"
            )
        return "\n".join(lines)
