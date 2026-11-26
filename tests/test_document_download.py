from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, Mock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import Response

from dtos.rag_document import RagDocumentDTO
from routes import document_thumbnail


class RagDocumentDownloadRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        """Create a test client for the document routes."""
        app = FastAPI()
        app.include_router(document_thumbnail.router)
        self.client = TestClient(app)

    def tearDown(self) -> None:
        """Close the test client's underlying connections."""
        self.client.close()

    def make_document(
        self,
        *,
        org_id: int = 3,
        file_name: str = "report.pdf",
        content_type: str = "application/pdf",
    ) -> RagDocumentDTO:
        """Create representative metadata for a downloadable document."""
        return RagDocumentDTO(
            rag_doc_id=4,
            org_id=org_id,
            title="A report",
            file_name=file_name,
            content_type=content_type,
        )

    def download(
        self, document: RagDocumentDTO | None, content: bytes | None
    ) -> tuple[Response, Mock]:
        """Request a download while replacing the database repository."""
        repository = Mock()
        repository.load = AsyncMock(return_value=document)
        repository.load_content = AsyncMock(return_value=content)
        repository_factory = document_thumbnail.RagDocumentRepository
        with patch.object(
            document_thumbnail, repository_factory.__name__, return_value=repository
        ):
            response = self.client.get("/api/organizations/3/rag-documents/4/download")
        return response, repository

    def test_download_returns_bytes_and_attachment_headers(self) -> None:
        """Return the original bytes with the stored MIME type and filename."""
        document = self.make_document()
        content = b"%PDF\x00document bytes"

        response, repository = self.download(document, content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, content)
        self.assertEqual(response.headers["content-type"], "application/pdf")
        self.assertEqual(
            response.headers["content-disposition"],
            "attachment; filename=\"report.pdf\"; filename*=UTF-8''report.pdf",
        )
        repository.load.assert_awaited_once_with(4)
        repository.load_content.assert_awaited_once_with(4, 3)

    def test_download_safely_encodes_unicode_and_header_sensitive_filename(
        self,
    ) -> None:
        """Keep Unicode filenames while preventing response header injection."""
        file_name = 'résumé\r\nX-Injected: yes; "final".pdf'
        document = self.make_document(file_name=file_name)

        response, _ = self.download(document, b"document")

        self.assertEqual(response.status_code, 200)
        content_disposition = response.headers["content-disposition"]
        self.assertIn(
            "filename*=UTF-8''r%C3%A9sum%C3%A9%0D%0AX-Injected%3A%20yes%3B%20%22final%22.pdf",
            content_disposition,
        )
        self.assertNotIn("x-injected", response.headers)

    def test_download_uses_defaults_and_accepts_empty_files(self) -> None:
        """Accept zero-byte files and use safe defaults for missing metadata."""
        document = self.make_document(file_name="", content_type="")

        response, _ = self.download(document, b"")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")
        self.assertEqual(response.headers["content-type"], "application/octet-stream")
        self.assertEqual(
            response.headers["content-disposition"],
            "attachment; filename=\"document\"; filename*=UTF-8''document",
        )

    def test_download_returns_not_found_for_missing_document(self) -> None:
        """Return 404 when the requested document does not exist."""
        response, repository = self.download(None, None)

        self.assertEqual(response.status_code, 404)
        repository.load_content.assert_not_awaited()

    def test_download_returns_not_found_for_another_organization(self) -> None:
        """Hide documents owned by another organization."""
        response, repository = self.download(self.make_document(org_id=9), None)

        self.assertEqual(response.status_code, 404)
        repository.load_content.assert_not_awaited()

    def test_download_rejects_missing_content(self) -> None:
        """Return 422 when document metadata exists but its content is absent."""
        response, repository = self.download(self.make_document(), None)

        self.assertEqual(response.status_code, 422)
        repository.load_content.assert_awaited_once_with(4, 3)


if __name__ == "__main__":
    unittest.main()
