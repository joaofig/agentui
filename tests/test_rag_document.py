from __future__ import annotations

import unittest
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock

from dtos.rag_document import RagDocumentDTO
from repositories.postgres.rag_document import RagDocumentRepository


class FakeCursor:
    def __init__(
        self, rows: list[dict[str, Any]] | None = None, inserted_id: int = 0
    ) -> None:
        self.rows = rows or []
        self.inserted_id = inserted_id
        self.calls: list[tuple[str, Any]] = []
        self.fetchone_result: dict[str, int] | None = None

    async def __aenter__(self) -> FakeCursor:
        return self

    async def __aexit__(self, *args: Any) -> None:
        return None

    async def execute(self, query: str, params: Any = None) -> FakeCursor:
        self.calls.append((query, params))
        if query.lstrip().startswith("INSERT"):
            self.fetchone_result = {"rag_doc_id": self.inserted_id}
        return self

    async def fetchall(self) -> list[dict[str, Any]]:
        return self.rows

    async def fetchone(self) -> dict[str, int] | None:
        return self.fetchone_result


class FakeConnection:
    def __init__(self, cursor: FakeCursor) -> None:
        self.closed = False
        self._cursor = cursor

    def cursor(self) -> FakeCursor:
        return self._cursor

    async def commit(self) -> None:
        return None


class RagDocumentDTOTests(unittest.TestCase):
    def test_round_trips_binary_nullable_fields_and_timestamps(self) -> None:
        """Preserve document bytes, nullable fields, and audit timestamps."""
        timestamp = datetime(2026, 11, 21, 14, 50, tzinfo=UTC)
        document = RagDocumentDTO(
            rag_doc_id=4,
            org_id=2,
            title="A document",
            file_name="document.pdf",
            content_type="application/pdf",
            content=b"\x00\x01document",
            page_count=None,
            chunk_count=7,
            language="EN",
            created_on=timestamp,
            created_by="creator",
            updated_on=timestamp,
            updated_by="editor",
        )

        mapped = RagDocumentDTO.from_dict(document.to_dict())

        self.assertEqual(mapped, document)
        self.assertEqual(mapped.content, b"\x00\x01document")
        self.assertIsNone(mapped.page_count)
        self.assertEqual(mapped.created_on, timestamp)
        self.assertEqual(mapped.updated_on, timestamp)
        self.assertEqual(document.to_dict()["created_on"], timestamp)
        self.assertEqual(document.to_dict()["updated_on"], timestamp)
        self.assertNotIn("created_at", document.to_dict())
        self.assertNotIn("updated_at", document.to_dict())

    def test_defaults_match_table_defaults_and_nullable_columns(self) -> None:
        """Provide DTO defaults matching the document table's defaults."""
        document = RagDocumentDTO(org_id=1, title="A document")

        self.assertEqual(document.file_name, "")
        self.assertEqual(document.content_type, "")
        self.assertIsNone(document.content)
        self.assertIsNone(document.page_count)
        self.assertIsNone(document.chunk_count)
        self.assertEqual(document.language, "EN")
        self.assertIsNotNone(document.created_on.utcoffset())
        self.assertIsNotNone(document.updated_on.utcoffset())


class RagDocumentRepositoryTests(unittest.IsolatedAsyncioTestCase):
    def create_repository(self, cursor: FakeCursor) -> RagDocumentRepository:
        """Create a repository wired to an in-memory async connection."""
        repository = RagDocumentRepository()
        connection = FakeConnection(cursor)
        repository.conn = connection  # type: ignore[assignment]
        repository.connect = AsyncMock(return_value=connection)  # type: ignore[method-assign]
        return repository

    def make_document(self, rag_doc_id: int = 0) -> RagDocumentDTO:
        """Create a document with representative values for repository tests."""
        return RagDocumentDTO(
            rag_doc_id=rag_doc_id,
            org_id=3,
            title="A document",
            file_name="document.pdf",
            content_type="application/pdf",
            content=b"document bytes",
            page_count=2,
            chunk_count=5,
            language="EN",
            created_by="creator",
            updated_by="editor",
        )

    async def test_list_filters_by_organization_and_maps_rows(self) -> None:
        """List documents for one organization and map each database row."""
        document = self.make_document(rag_doc_id=8)
        row = document.to_dict()
        row["content"] = None
        cursor = FakeCursor(rows=[row])
        repository = self.create_repository(cursor)

        result = await repository.list(3)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].rag_doc_id, document.rag_doc_id)
        self.assertEqual(result[0].title, document.title)
        self.assertIsNone(result[0].content)
        query, params = cursor.calls[0]
        normalized_query = " ".join(query.split())
        self.assertIn("FROM public.rag_document", normalized_query)
        self.assertIn("WHERE org_id = %s", normalized_query)
        self.assertNotIn(", content,", normalized_query)
        self.assertNotIn(", content\n", normalized_query)
        self.assertNotIn(", content FROM", normalized_query)
        self.assertEqual(params, (3,))

    async def test_list_returns_empty_list_when_no_documents(self) -> None:
        """Return an empty list when an organization has no documents."""
        repository = self.create_repository(FakeCursor())

        self.assertEqual(await repository.list(3), [])

    async def test_load_returns_document_and_uses_document_id(self) -> None:
        """Load a document by its primary key."""
        document = self.make_document(rag_doc_id=8)
        cursor = FakeCursor(rows=[document.to_dict()])
        repository = self.create_repository(cursor)

        result = await repository.load(8)

        self.assertEqual(result, document)
        query, params = cursor.calls[0]
        normalized_query = " ".join(query.split())
        self.assertIn("WHERE rag_doc_id = %s", normalized_query)
        self.assertEqual(params, (8,))

    async def test_load_returns_none_when_document_is_missing(self) -> None:
        """Return None when the requested document does not exist."""
        cursor = FakeCursor()
        repository = self.create_repository(cursor)

        self.assertIsNone(await repository.load(99))

    async def test_save_inserts_and_returns_generated_document_id(self) -> None:
        """Insert a document and include its generated primary key in the result."""
        document = self.make_document()
        cursor = FakeCursor(inserted_id=12)
        repository = self.create_repository(cursor)

        result = await repository.save(document)

        self.assertEqual(result["rag_doc_id"], 12)
        query, params = cursor.calls[0]
        self.assertEqual(query.lstrip().split(maxsplit=1)[0], "INSERT")
        self.assertIn("rag_document", query)
        self.assertIn("RETURNING rag_doc_id", query)
        self.assertNotIn("rag_doc_id", query.split("VALUES", maxsplit=1)[0])
        self.assertNotIn("content", params)
        self.assertEqual(params["org_id"], 3)

    async def test_save_updates_existing_document(self) -> None:
        """Update an existing row using its explicit document primary key."""
        document = self.make_document(rag_doc_id=12)
        cursor = FakeCursor()
        repository = self.create_repository(cursor)

        result = await repository.save(document)

        self.assertEqual(result["rag_doc_id"], 12)
        query, params = cursor.calls[0]
        self.assertIn("UPDATE public.rag_document", query)
        self.assertIn("WHERE rag_doc_id = %(rag_doc_id)s", query)
        self.assertEqual(params["rag_doc_id"], 12)
        self.assertIn("updated_on", query)
        self.assertNotIn("created_on =", query)
        self.assertNotIn("content =", query)

    async def test_load_content_returns_bytes_for_existing_document(self) -> None:
        """Load only the binary content for an existing document."""
        cursor = FakeCursor(rows=[{"content": b"secret bytes"}])
        repository = self.create_repository(cursor)

        result = await repository.load_content(8)

        self.assertEqual(result, b"secret bytes")
        query, params = cursor.calls[0]
        normalized_query = " ".join(query.split())
        self.assertIn("SELECT content", normalized_query)
        self.assertIn("WHERE rag_doc_id = %s", normalized_query)
        self.assertEqual(params, (8,))

    async def test_load_content_returns_none_when_missing(self) -> None:
        """Return None when the requested document does not exist."""
        cursor = FakeCursor()
        repository = self.create_repository(cursor)

        self.assertIsNone(await repository.load_content(99))


if __name__ == "__main__":
    unittest.main()
