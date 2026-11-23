import pymupdf

from src.repositories.postgres.rag_doc_chunk import RagDocumentChunkRepository
from src.dtos.rag_doc_chunk import RagDocumentChunkDTO
from src.services.embeddings import embed_texts_async
from src.services.pdf import extract_paragraphs
from src.dtos.rag_document import RagDocumentDTO


class RagService:
    """High-level service providing RAG operations against PostgreSQL knowledge base."""

    def __init__(self) -> None:
        self.repository = RagDocumentChunkRepository()

    async def _index_pdf(self, document: RagDocumentDTO):
        doc: pymupdf.PdfDocument = pymupdf.open(stream=document.content, filetype="pdf")
        paragraphs = extract_paragraphs(doc)

        embeddings = await embed_texts_async([str(paragraph["text"]) for paragraph in paragraphs])

        chunks = [
            RagDocumentChunkDTO(
                rag_doc_id=document.rag_doc_id,
                org_id=document.org_id,
                page_number=int(paragraph.get("page", 0)),
                ordinal=ordinal,
                content=str(paragraph.get("text", "")),
                embedding=embedding,
            )
            for ordinal, (paragraph, embedding)
            in enumerate(zip(paragraphs, embeddings))
        ]
        await self.repository.insert(chunks)

    async def index_document(self, document: RagDocumentDTO) -> None:
        match document.content_type:
            case "application/pdf":
                await self._index_pdf(document)
        pass
