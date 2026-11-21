import re
from pathlib import Path

import fitz  # PyMuPDF
from haystack import Document, Pipeline, component
from haystack.components.preprocessors import DocumentSplitter


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
