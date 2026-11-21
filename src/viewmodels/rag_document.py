from datetime import datetime
from typing import Any

from nicegui import binding
from nicemvvm.tools.user import get_user_name
from nicemvvm.viewmodels.view_model import ViewModel

from src.dtos.rag_document import RagDocumentDTO
from src.repositories.postgres.rag_document import RagDocumentRepository


@binding.bindable_dataclass
class RagDocumentViewModel(ViewModel):
    """View model for a single RAG document."""

    rag_doc_id: int = 0
    org_id: int = 0
    title: str = ""
    file_name: str = ""
    content_type: str = ""
    content: bytes | None = None
    page_count: int | None = None
    chunk_count: int | None = None
    language: str = "EN"
    created_on: datetime = datetime.now()
    created_by: str = ""
    updated_on: datetime = datetime.now()
    updated_by: str = ""

    def __post_init__(self):
        super().__init__()

    async def _on_call(self, msg: str, **kwargs) -> Any:
        """Handle incoming calls from the view.

        Args:
            msg: Action message (copy, save, load).
            **kwargs: Additional context such as rag_doc_id or org_id.

        Returns:
            None.
        """
        match msg:
            case "copy":
                self.copy(kwargs.get("document"))

            case "save":
                await self.save()

            case "load":
                if "rag_doc_id" in kwargs:
                    repo = RagDocumentRepository()
                    doc = await repo.load(rag_doc_id=kwargs.get("rag_doc_id", 0))
                    if doc:
                        self.copy(doc)
        return None

    def copy(self, document: RagDocumentDTO):
        """Copy fields from a DTO into this view model.

        Args:
            document: Source DTO to copy from.
        """
        self.rag_doc_id = document.rag_doc_id
        self.org_id = document.org_id
        self.title = document.title
        self.file_name = document.file_name
        self.content_type = document.content_type
        self.content = document.content
        self.page_count = document.page_count
        self.chunk_count = document.chunk_count
        self.language = document.language
        self.created_on = document.created_on
        self.created_by = document.created_by
        self.updated_on = document.updated_on
        self.updated_by = document.updated_by

    def to_dto(self) -> RagDocumentDTO:
        """Convert this view model to a DTO for persistence.

        Returns:
            A RagDocumentDTO populated from the current state.
        """
        is_old = self.rag_doc_id > 0
        return RagDocumentDTO(
            rag_doc_id=self.rag_doc_id,
            org_id=self.org_id,
            title=self.title,
            file_name=self.file_name,
            content_type=self.content_type,
            content=self.content,
            page_count=self.page_count,
            chunk_count=self.chunk_count,
            language=self.language,
            created_on=self.created_on if is_old else datetime.now().astimezone(),
            created_by=self.created_by if is_old else get_user_name(),
            updated_on=datetime.now().astimezone(),
            updated_by=get_user_name(),
        )

    async def save(self):
        """Persist the current document state to the database."""
        document = self.to_dto()
        repo = RagDocumentRepository()
        await repo.save(document)
        if document.rag_doc_id:
            self.rag_doc_id = document.rag_doc_id
