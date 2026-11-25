from __future__ import annotations

import io
import unittest
import zipfile
from typing import Any
from unittest.mock import AsyncMock, patch

import httpx
import pymupdf as fitz
from fastapi import FastAPI, HTTPException
from openpyxl import Workbook

from dtos.rag_document import RagDocumentDTO
from routes.document_thumbnail import rag_document_thumbnail, router
from services.document_thumbnail import (
    UnsupportedDocumentTypeError,
    render_document_thumbnail,
)


class ThumbnailServiceTests(unittest.TestCase):
    def create_pdf(self) -> bytes:
        """Create a two-page PDF with distinctive page colors."""
        document = fitz.open()
        first_page = document.new_page(width=100, height=200)
        first_page.draw_rect(first_page.rect, color=(1, 0, 0), fill=(1, 0, 0))
        second_page = document.new_page(width=100, height=200)
        second_page.draw_rect(second_page.rect, color=(0, 0, 1), fill=(0, 0, 1))
        return document.tobytes()

    def test_pdf_thumbnail_uses_first_page_and_pads_to_requested_size(self) -> None:
        """Render only page one and preserve its aspect ratio on a fixed canvas."""
        image_bytes = render_document_thumbnail(
            self.create_pdf(),
            "application/pdf",
            image_format="png",
            width=64,
            height=64,
        )

        pixmap = fitz.Pixmap(image_bytes)
        self.assertEqual((pixmap.width, pixmap.height), (64, 64))
        pixel_index = (32 * 64 + 32) * 3
        pixel = pixmap.samples_mv[pixel_index : pixel_index + 3]
        self.assertGreater(pixel[0], 240)
        self.assertLess(pixel[2], 15)
        padding_index = 32 * 64 * 3
        padding = pixmap.samples_mv[padding_index : padding_index + 3]
        self.assertGreater(min(padding), 240)

    def test_thumbnail_supports_jpeg_encoding(self) -> None:
        """Encode a requested JPEG thumbnail with the requested dimensions."""
        image_bytes = render_document_thumbnail(
            self.create_pdf(),
            "application/pdf",
            image_format="jpeg",
            width=32,
            height=48,
        )

        pixmap = fitz.Pixmap(image_bytes)
        self.assertEqual((pixmap.width, pixmap.height), (32, 48))

    def test_unsupported_content_type_is_rejected(self) -> None:
        """Reject documents whose content type is not supported."""
        with self.assertRaises(UnsupportedDocumentTypeError):
            render_document_thumbnail(b"content", "text/plain")

    def test_malformed_pdf_is_rejected(self) -> None:
        """Reject PDF data that cannot be opened or rendered."""
        with self.assertRaises(ValueError):
            render_document_thumbnail(b"not a pdf", "application/pdf")

    def test_office_and_open_document_samples_are_converted(self) -> None:
        """Convert generated Word, spreadsheet, presentation, and OpenDocument files."""
        samples = [
            (
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                self.create_docx(),
            ),
            (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                self.create_xlsx(),
            ),
            (
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                self.create_pptx(),
            ),
            ("application/vnd.oasis.opendocument.text", self.create_odf("text")),
            (
                "application/vnd.oasis.opendocument.spreadsheet",
                self.create_odf("spreadsheet"),
            ),
            (
                "application/vnd.oasis.opendocument.presentation",
                self.create_odf("presentation"),
            ),
        ]

        for content_type, content in samples:
            with self.subTest(content_type=content_type):
                image_bytes = render_document_thumbnail(
                    content, content_type, image_format="png", width=64, height=64
                )
                pixmap = fitz.Pixmap(image_bytes)
                self.assertEqual((pixmap.width, pixmap.height), (64, 64))

    def create_docx(self) -> bytes:
        """Create a minimal, valid Word Open XML fixture."""
        return self.create_zip(
            {
                "[Content_Types].xml": (
                    b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                    b'<Default Extension="rels" '
                    b'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                    b'<Default Extension="xml" ContentType="application/xml"/>'
                    b'<Override PartName="/word/document.xml" '
                    b'ContentType="application/vnd.openxmlformats-officedocument.'
                    b'wordprocessingml.document.main+xml"/>'
                    b"</Types>"
                ),
                "_rels/.rels": (
                    b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                    b'<Relationship Id="rId1" '
                    b'Type="http://schemas.openxmlformats.org/officeDocument/2006/'
                    b'relationships/officeDocument" '
                    b'Target="word/document.xml"/></Relationships>'
                ),
                "word/document.xml": (
                    b'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                    b"<w:body><w:p><w:r><w:t>thumbnail</w:t></w:r></w:p>"
                    b"<w:sectPr/></w:body></w:document>"
                ),
            }
        )

    def create_xlsx(self) -> bytes:
        """Create a spreadsheet containing visible sample text."""
        workbook = Workbook()
        workbook.active["A1"] = "thumbnail"
        output = io.BytesIO()
        workbook.save(output)
        return output.getvalue()

    def create_pptx(self) -> bytes:
        """Create a minimal presentation with one text slide."""
        return self.create_zip(
            {
                "[Content_Types].xml": (
                    b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                    b'<Default Extension="rels" '
                    b'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                    b'<Default Extension="xml" ContentType="application/xml"/>'
                    b'<Override PartName="/ppt/presentation.xml" '
                    b'ContentType="application/vnd.openxmlformats-officedocument.'
                    b'presentationml.presentation.main+xml"/>'
                    b'<Override PartName="/ppt/slides/slide1.xml" '
                    b'ContentType="application/vnd.openxmlformats-officedocument.'
                    b'presentationml.slide+xml"/></Types>'
                ),
                "_rels/.rels": (
                    b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                    b'<Relationship Id="rId1" '
                    b'Type="http://schemas.openxmlformats.org/officeDocument/2006/'
                    b'relationships/officeDocument" '
                    b'Target="ppt/presentation.xml"/></Relationships>'
                ),
                "ppt/presentation.xml": (
                    b'<p:presentation xmlns:a="'
                    b'http://schemas.openxmlformats.org/drawingml/2006/main" '
                    b'xmlns:r="'
                    b"http://schemas.openxmlformats.org/officeDocument/2006/"
                    b'relationships" '
                    b'xmlns:p="'
                    b'http://schemas.openxmlformats.org/presentationml/2006/main">'
                    b'<p:sldIdLst><p:sldId id="256" r:id="rId1"/></p:sldIdLst>'
                    b'<p:sldSz cx="9144000" cy="5143500"/></p:presentation>'
                ),
                "ppt/_rels/presentation.xml.rels": (
                    b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                    b'<Relationship Id="rId1" '
                    b'Type="http://schemas.openxmlformats.org/officeDocument/2006/'
                    b'relationships/slide" '
                    b'Target="slides/slide1.xml"/></Relationships>'
                ),
                "ppt/slides/slide1.xml": (
                    b'<p:sld xmlns:a="'
                    b'http://schemas.openxmlformats.org/drawingml/2006/main" '
                    b'xmlns:p="'
                    b'http://schemas.openxmlformats.org/presentationml/2006/main">'
                    b"<p:cSld><p:spTree><p:nvGrpSpPr>"
                    b'<p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/>'
                    b"</p:nvGrpSpPr><p:grpSpPr><a:xfrm>"
                    b'<a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
                    b'<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/>'
                    b"</a:xfrm></p:grpSpPr><p:sp><p:nvSpPr>"
                    b'<p:cNvPr id="2" name="TextBox 1"/><p:cNvSpPr/><p:nvPr/>'
                    b"</p:nvSpPr><p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/>"
                    b"<a:p><a:r><a:t>thumbnail</a:t></a:r></a:p>"
                    b"</p:txBody></p:sp></p:spTree></p:cSld></p:sld>"
                ),
            }
        )

    def create_odf(self, document_type: str) -> bytes:
        """Create a minimal OpenDocument text, spreadsheet, or presentation file."""
        namespaces = {
            "text": (
                "application/vnd.oasis.opendocument.text",
                "<office:text><text:p>thumbnail</text:p></office:text>",
            ),
            "spreadsheet": (
                "application/vnd.oasis.opendocument.spreadsheet",
                "<office:spreadsheet>"
                '<table:table table:name="Sheet1"><table:table-row>'
                '<table:table-cell office:value-type="string">'
                "<text:p>thumbnail</text:p></table:table-cell>"
                "</table:table-row></table:table></office:spreadsheet>",
            ),
            "presentation": (
                "application/vnd.oasis.opendocument.presentation",
                "<office:presentation>"
                '<draw:page draw:name="page1" draw:style-name="dp1">'
                '<draw:frame draw:style-name="gr1" svg:width="10cm" '
                'svg:height="2cm" svg:x="1cm" svg:y="1cm">'
                "<draw:text-box><text:p>thumbnail</text:p></draw:text-box>"
                "</draw:frame></draw:page></office:presentation>",
            ),
        }
        media_type, body = namespaces[document_type]
        content = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<office:document-content "
            'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
            'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
            'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
            'xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0" '
            'xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" '
            'office:version="1.2"><office:body>'
            f"{body}</office:body></office:document-content>"
        ).encode()
        manifest = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<manifest:manifest "
            'xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" '
            'manifest:version="1.2"><manifest:file-entry manifest:full-path="/" '
            f'manifest:media-type="{media_type}"/>'
            '<manifest:file-entry manifest:full-path="content.xml" '
            'manifest:media-type="text/xml"/></manifest:manifest>'
        ).encode()
        return self.create_zip(
            {
                "mimetype": media_type.encode(),
                "content.xml": content,
                "META-INF/manifest.xml": manifest,
            }
        )

    def create_zip(self, entries: dict[str, bytes]) -> bytes:
        """Package fixture entries into an in-memory ZIP archive."""
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, content in entries.items():
                archive.writestr(name, content)
        return output.getvalue()


class ThumbnailEndpointTests(unittest.IsolatedAsyncioTestCase):
    def create_document(
        self, content: bytes | None, content_type: str
    ) -> RagDocumentDTO:
        """Create a document record for endpoint tests."""
        return RagDocumentDTO(
            rag_doc_id=4,
            org_id=2,
            title="A document",
            content=content,
            content_type=content_type,
        )

    def create_pdf(self) -> bytes:
        """Create a one-page PDF with visible content."""
        document = fitz.open()
        document.new_page()
        return document.tobytes()

    async def request_thumbnail(
        self,
        document: RagDocumentDTO | None,
        org_id: int = 2,
        **params: Any,
    ) -> Any:
        """Call the endpoint with a mocked document repository."""
        content = document.content if document else None
        repository = type(
            "FakeRepository",
            (),
            {
                "load": AsyncMock(return_value=document),
                "load_content": AsyncMock(return_value=content),
            },
        )()
        with patch(
            "routes.document_thumbnail.RagDocumentRepository", return_value=repository
        ):
            return await rag_document_thumbnail(org_id, 4, **params)

    async def test_default_response_is_a_64_pixel_jpeg(self) -> None:
        """Return a default 64-by-64 JPEG image."""
        response = await self.request_thumbnail(
            self.create_document(self.create_pdf(), "application/pdf")
        )

        self.assertEqual(response.media_type, "image/jpeg")
        pixmap = fitz.Pixmap(response.body)
        self.assertEqual((pixmap.width, pixmap.height), (64, 64))

    async def test_query_parameters_select_png_and_dimensions(self) -> None:
        """Honor the requested PNG format and independent image dimensions."""
        response = await self.request_thumbnail(
            self.create_document(self.create_pdf(), "application/pdf"),
            format="png",
            width=80,
            height=40,
        )

        self.assertEqual(response.media_type, "image/png")
        pixmap = fitz.Pixmap(response.body)
        self.assertEqual((pixmap.width, pixmap.height), (80, 40))

    async def test_missing_document_returns_not_found(self) -> None:
        """Return HTTP 404 when the repository has no matching document."""
        with self.assertRaises(HTTPException) as error:
            await self.request_thumbnail(None)

        self.assertEqual(error.exception.status_code, 404)

    async def test_missing_content_returns_unprocessable_entity(self) -> None:
        """Reject records that do not contain document bytes."""
        with self.assertRaises(HTTPException) as error:
            await self.request_thumbnail(self.create_document(None, "application/pdf"))

        self.assertEqual(error.exception.status_code, 422)

    async def test_unsupported_document_returns_unsupported_media_type(self) -> None:
        """Return HTTP 415 for an unsupported document media type."""
        with self.assertRaises(HTTPException) as error:
            await self.request_thumbnail(self.create_document(b"bytes", "text/plain"))

        self.assertEqual(error.exception.status_code, 415)

    async def test_malformed_document_returns_unprocessable_entity(self) -> None:
        """Return HTTP 422 when document content cannot be rendered."""
        with self.assertRaises(HTTPException) as error:
            await self.request_thumbnail(
                self.create_document(b"bad PDF", "application/pdf")
            )

        self.assertEqual(error.exception.status_code, 422)

    async def test_invalid_format_and_dimensions_are_rejected(self) -> None:
        """Reject unsupported encodings and dimensions outside the allowed range."""
        document = self.create_document(self.create_pdf(), "application/pdf")
        for params in ({"format": "gif"}, {"width": 0}, {"height": 1025}):
            with self.subTest(params=params), self.assertRaises(HTTPException) as error:
                await self.request_thumbnail(document, **params)
            self.assertEqual(error.exception.status_code, 422)

    async def test_wrong_org_id_returns_not_found(self) -> None:
        """Return HTTP 404 when the document doesn't belong to the requested org."""
        document = self.create_document(self.create_pdf(), "application/pdf")
        document.org_id = 99
        with self.assertRaises(HTTPException) as error:
            await self.request_thumbnail(document, org_id=2)

        self.assertEqual(error.exception.status_code, 404)

    async def test_http_route_parses_query_parameters_and_rejects_bad_values(
        self,
    ) -> None:
        """Expose the expected URL and validate query strings through FastAPI."""
        application = FastAPI()
        application.include_router(router)
        document = self.create_document(self.create_pdf(), "application/pdf")
        repository = type(
            "FakeRepository",
            (),
            {
                "load": AsyncMock(return_value=document),
                "load_content": AsyncMock(return_value=document.content),
            },
        )()

        with patch(
            "routes.document_thumbnail.RagDocumentRepository", return_value=repository
        ):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=application), base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/organizations/2/rag-documents/4/thumbnail?format=png&width=80&height=40"
                )
                invalid_response = await client.get(
                    "/api/organizations/2/rag-documents/4/thumbnail?width=not-a-number"
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "image/png")
        pixmap = fitz.Pixmap(response.content)
        self.assertEqual((pixmap.width, pixmap.height), (80, 40))
        self.assertEqual(invalid_response.status_code, 422)
