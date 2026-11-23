from datetime import datetime
from typing import Any, Self

from pydantic import Field

from dtos.base import BaseDTO


class RagDocumentDTO(BaseDTO):
    """Transfer object for a row in the `rag_document` table."""

    rag_doc_id: int = 0
    org_id: int = 0
    title: str = ""
    description: str = ""
    file_name: str = ""
    content_type: str = ""
    status: str = "pending"
    content: bytes | None = None
    page_count: int | None = None
    chunk_count: int | None = None
    language: str = "EN"
    created_on: datetime = Field(default_factory=lambda: datetime.now().astimezone())
    created_by: str = ""
    updated_on: datetime = Field(default_factory=lambda: datetime.now().astimezone())
    updated_by: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create a document DTO from a database row mapping.

        Args:
            data: Mapping containing `rag_document` table columns.

        Returns:
            A DTO populated from the supplied columns.
        """
        return cls(
            rag_doc_id=data.get("rag_doc_id", 0),
            org_id=data.get("org_id", 0),
            title=data.get("title", ""),
            description=data.get("description", ""),
            file_name=data.get("file_name", ""),
            content_type=data.get("content_type", ""),
            content=data.get("content"),
            status=data.get("status", "pending"),
            page_count=data.get("page_count"),
            chunk_count=data.get("chunk_count"),
            language=data.get("language", "EN"),
            created_on=data.get("created_on", datetime.now().astimezone()),
            created_by=data.get("created_by", ""),
            updated_on=data.get("updated_on", datetime.now().astimezone()),
            updated_by=data.get("updated_by", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert the DTO to a mapping using the table's column names.

        Returns:
            A dictionary suitable for PostgreSQL query parameters.
        """
        return {
            "rag_doc_id": self.rag_doc_id,
            "org_id": self.org_id,
            "title": self.title,
            "description": self.description,
            "file_name": self.file_name,
            "content_type": self.content_type,
            "content": self.content,
            "status": self.status,
            "page_count": self.page_count,
            "chunk_count": self.chunk_count,
            "language": self.language,
            "created_on": self.created_on,
            "created_by": self.created_by,
            "updated_on": self.updated_on,
            "updated_by": self.updated_by,
        }
