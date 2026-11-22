from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import pymupdf as fitz

MAX_THUMBNAIL_DIMENSION = 1024
OFFICE_CONVERSION_TIMEOUT_SECONDS = 30
OFFICE_EXTENSIONS = {
    "application/msword": ".doc",
    "application/vnd.ms-word.document.macroenabled.12": ".docm",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.ms-excel.sheet.binary.macroenabled.12": ".xlsb",
    "application/vnd.ms-excel.sheet.macroenabled.12": ".xlsm",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.ms-powerpoint": ".ppt",
    "application/vnd.ms-powerpoint.presentation.macroenabled.12": ".pptm",
    "application/vnd.openxmlformats-officedocument."
    "presentationml.presentation": ".pptx",
    "application/vnd.oasis.opendocument.text": ".odt",
    "application/vnd.oasis.opendocument.spreadsheet": ".ods",
    "application/vnd.oasis.opendocument.presentation": ".odp",
}


class ThumbnailRenderError(ValueError):
    """Raised when a supported document cannot be rendered as a thumbnail."""


class UnsupportedDocumentTypeError(ThumbnailRenderError):
    """Raised when a document's media type is not supported."""


class ThumbnailConversionError(ThumbnailRenderError):
    """Raised when LibreOffice cannot convert an Office document to PDF."""


class LibreOfficeUnavailableError(RuntimeError):
    """Raised when LibreOffice is required but is not installed."""


class LibreOfficeTimeoutError(RuntimeError):
    """Raised when LibreOffice exceeds its conversion time limit."""


def render_document_thumbnail(
    content: bytes,
    content_type: str,
    image_format: str = "jpg",
    width: int = 64,
    height: int = 64,
) -> bytes:
    """Render the first page of a supported document as a padded image.

    Args:
        content: Complete document bytes.
        content_type: HTTP media type identifying the document format.
        image_format: Output image format, either ``jpg``, ``jpeg``, or ``png``.
        width: Thumbnail canvas width in pixels.
        height: Thumbnail canvas height in pixels.

    Returns:
        Encoded image bytes with the requested canvas dimensions.

    Raises:
        UnsupportedDocumentTypeError: If the media type is not supported.
        ThumbnailRenderError: If the document is empty, malformed, or invalid.
        LibreOfficeUnavailableError: If an Office format needs missing LibreOffice.
        LibreOfficeTimeoutError: If document conversion exceeds the time limit.
    """
    output_format = image_format.lower()
    if output_format not in {"jpg", "jpeg", "png"}:
        raise ThumbnailRenderError("Image format must be jpg, jpeg, or png.")
    if not 1 <= width <= MAX_THUMBNAIL_DIMENSION:
        raise ThumbnailRenderError(
            f"Image width must be between 1 and {MAX_THUMBNAIL_DIMENSION} pixels."
        )
    if not 1 <= height <= MAX_THUMBNAIL_DIMENSION:
        raise ThumbnailRenderError(
            f"Image height must be between 1 and {MAX_THUMBNAIL_DIMENSION} pixels."
        )

    media_type = content_type.split(";", maxsplit=1)[0].strip().lower()
    if media_type in {"application/pdf", "application/x-pdf"}:
        pdf_content = content
    else:
        extension = OFFICE_EXTENSIONS.get(media_type)
        if extension is None:
            raise UnsupportedDocumentTypeError(
                f"Document media type is not supported: {media_type or 'unknown'}."
            )
        pdf_content = _convert_office_document(content, extension)

    try:
        with fitz.open(stream=pdf_content, filetype="pdf") as document:
            if document.page_count == 0:
                raise ThumbnailRenderError("The document does not contain any pages.")
            page = document.load_page(0)
            scale = min(width / page.rect.width, height / page.rect.height)
            rendered = page.get_pixmap(
                matrix=fitz.Matrix(scale, scale), colorspace=fitz.csRGB, alpha=False
            )
            canvas = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, width, height), False)
            canvas.clear_with(255)
            rendered.set_origin(
                (width - rendered.width) // 2, (height - rendered.height) // 2
            )
            canvas.copy(rendered, rendered.irect)
            return canvas.tobytes(output="png" if output_format == "png" else "jpeg")
    except ThumbnailRenderError:
        raise
    except (fitz.FileDataError, RuntimeError, ValueError) as error:
        raise ThumbnailRenderError("Document content could not be rendered.") from error


def _convert_office_document(content: bytes, extension: str) -> bytes:
    """Convert an Office or OpenDocument file to PDF in an isolated profile."""
    executable = shutil.which("soffice")
    if executable is None:
        macos_executable = Path("/Applications/LibreOffice.app/Contents/MacOS/soffice")
        try:
            macos_executable.stat()
        except FileNotFoundError as error:
            raise LibreOfficeUnavailableError(
                "LibreOffice is required to render Office document thumbnails."
            ) from error
        executable = str(macos_executable)

    with tempfile.TemporaryDirectory(
        prefix="rag-document-thumbnail-"
    ) as temporary_directory:
        working_directory = Path(temporary_directory)
        profile_directory = working_directory / "profile"
        profile_directory.mkdir()
        source_path = working_directory / f"document{extension}"
        source_path.write_bytes(content)
        command = [
            executable,
            "--headless",
            "--nologo",
            "--nodefault",
            "--nofirststartwizard",
            f"-env:UserInstallation={profile_directory.as_uri()}",
            "--convert-to",
            "pdf",
            "--outdir",
            str(working_directory),
            str(source_path),
        ]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                check=False,
                text=True,
                timeout=OFFICE_CONVERSION_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as error:
            raise LibreOfficeTimeoutError(
                "LibreOffice document conversion timed out."
            ) from error

        pdf_path = working_directory / "document.pdf"
        if result.returncode != 0 or not pdf_path.is_file():
            detail = (result.stderr or result.stdout).strip()
            message = "LibreOffice could not convert the document to PDF."
            if detail:
                message = f"{message} {detail[:300]}"
            raise ThumbnailConversionError(message)
        return pdf_path.read_bytes()
