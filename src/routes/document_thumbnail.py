from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException
from starlette.responses import Response

from repositories.postgres.rag_document import RagDocumentRepository
from services.document_thumbnail import (
    MAX_THUMBNAIL_DIMENSION,
    LibreOfficeTimeoutError,
    LibreOfficeUnavailableError,
    ThumbnailRenderError,
    UnsupportedDocumentTypeError,
    render_document_thumbnail,
)

router = APIRouter()


@router.get("/api/rag-documents/{rag_doc_id}/thumbnail")
async def rag_document_thumbnail(
    rag_doc_id: int,
    format: str = "jpg",
    width: int = 64,
    height: int = 64,
) -> Response:
    """Return a JPEG or PNG thumbnail of a document's first page.

    Args:
        rag_doc_id: Database ID of the document to render.
        format: Output image format: ``jpg``, ``jpeg``, or ``png``.
        width: Thumbnail width in pixels, from 1 to 1024.
        height: Thumbnail height in pixels, from 1 to 1024.

    Returns:
        An image response containing the rendered first page.

    Raises:
        HTTPException: If the document is missing, invalid, unsupported, or
            cannot be converted by the configured LibreOffice runtime.
    """
    normalized_format = format.lower()
    if normalized_format not in {"jpg", "jpeg", "png"}:
        raise HTTPException(422, "Image format must be jpg, jpeg, or png.")
    if not 1 <= width <= MAX_THUMBNAIL_DIMENSION:
        raise HTTPException(
            422, f"Image width must be between 1 and {MAX_THUMBNAIL_DIMENSION} pixels."
        )
    if not 1 <= height <= MAX_THUMBNAIL_DIMENSION:
        raise HTTPException(
            422, f"Image height must be between 1 and {MAX_THUMBNAIL_DIMENSION} pixels."
        )

    document = await RagDocumentRepository().load(rag_doc_id)
    if document is None:
        raise HTTPException(404, "Document not found.")
    if not document.content:
        raise HTTPException(422, "Document has no content to render.")

    try:
        image = await asyncio.to_thread(
            render_document_thumbnail,
            document.content,
            document.content_type,
            image_format=normalized_format,
            width=width,
            height=height,
        )
    except UnsupportedDocumentTypeError as error:
        raise HTTPException(415, str(error)) from error
    except ThumbnailRenderError as error:
        raise HTTPException(422, str(error)) from error
    except LibreOfficeUnavailableError as error:
        raise HTTPException(503, str(error)) from error
    except LibreOfficeTimeoutError as error:
        raise HTTPException(504, str(error)) from error

    media_type = "image/png" if normalized_format == "png" else "image/jpeg"
    return Response(content=image, media_type=media_type)
