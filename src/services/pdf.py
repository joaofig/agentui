import re
from pathlib import Path
from collections import Counter

import pymupdf as fitz  # PyMuPDF
from beartype import beartype
from haystack import Document, component
from pymupdf import pymupdf

from services.text import clean_block


@component
class PyMuPDFParagraphConverter:
    """Convert PDFs to one Document per page, with paragraphs separated by
    blank lines.
    """

    def __init__(self, min_chars: int = 20):
        self.min_chars = min_chars

    @component.output_types(documents=list[Document])
    def run(self, sources: list[str | Path]):
        documents = []
        for source in sources:
            with fitz.open(source) as pdf:
                for page in pdf:
                    paragraphs = []
                    for *_, text, _, block_type in page.get_text("blocks", sort=True):
                        if block_type != 0:
                            continue
                        text = re.sub(r"-\n(\w)", r"\1", text)  # dehyphenate
                        text = re.sub(r"\s*\n\s*", " ", text).strip()
                        if len(text) >= self.min_chars:
                            paragraphs.append(text)
                    if paragraphs:
                        documents.append(
                            Document(
                                content="\n\n".join(paragraphs),
                                meta={
                                    "file_path": str(source),
                                    "page_number": page.number + 1,
                                },
                            )
                        )
        return {"documents": documents}


@beartype
def extract_paragraphs(
    doc: pymupdf.Document, min_chars: int = 20
) -> list[dict[str, int | str]]:
    paragraphs = []
    for page in doc:
        for *_, text, _, block_type in page.get_text("blocks", sort=True):
            if block_type != 0:
                continue
            para = clean_block(text)
            if len(para) >= min_chars:
                paragraphs.append({
                    "page": page.number + 1,
                    "text": para,
                })
    return paragraphs
