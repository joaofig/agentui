import re
from pathlib import Path

import pymupdf as fitz  # PyMuPDF
from haystack import Document, Pipeline, component
from pymupdf import pymupdf


@component
class PyMuPDFParagraphConverter:
    """Converts PDFs to one Document per page, with paragraphs separated by blank lines."""

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


# pipeline = Pipeline()
# pipeline.add_component("converter", PyMuPDFParagraphConverter())
# pipeline.add_component("splitter", DocumentSplitter(split_by="passage", split_length=1))
# pipeline.connect("converter", "splitter")
#
# result = pipeline.run({"converter": {"sources": ["document.pdf"]}})
# paragraphs = [d.content.strip() for d in result["splitter"]["documents"] if d.content.strip()]


def clean_block(text: str) -> str:
    text = re.sub(r"-\n(\w)", r"\1", text)
    text = re.sub(r"\s*\n\s*", " ", text)
    return re.sub(r"\s{2,}", " ", text).strip()


def extract_paragraphs(doc: pymupdf.Document, min_chars: int = 20) -> list[dict[str, int|str]]:
    paragraphs = []
    for page in doc:
        for *_, text, _, block_type in page.get_text("blocks", sort=True):
            if block_type != 0:
                continue
            para = clean_block(text)
            if len(para) >= min_chars:
                paragraphs.append({"page": page.number + 1, "text": para})
    return paragraphs
