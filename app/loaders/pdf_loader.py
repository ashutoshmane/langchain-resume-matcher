"""PDF document loader for resumes.

Supports multiple parsing strategies:
- pypdf (fast, simple PDFs)
- pdfplumber (better text extraction for formatted PDFs)
- unstructured (best for complex layouts, scanned PDFs)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from langchain_core.documents import Document

from app.core.config import settings

logger = logging.getLogger(__name__)


class PDFLoader:
    """Load a resume PDF and return a LangChain Document.

    Tries multiple backends in order of increasing complexity, stopping
    once usable text is obtained.
    """

    BACKENDS = ("pdfplumber", "pypdf", "unstructured")

    def __init__(self, preferred_backend: str = "pdfplumber") -> None:
        self.preferred_backend = preferred_backend

    async def load(self, file_path: Path | str) -> Document:
        """Load PDF from *file_path*."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {path}")

        backends = [self.preferred_backend] + [b for b in self.BACKENDS if b != self.preferred_backend]

        last_error: Optional[Exception] = None
        for backend in backends:
            try:
                text = await self._parse_with(path, backend)
                if text and len(text.strip()) > 50:
                    logger.info("Successfully parsed PDF with backend=%s", backend)
                    return Document(
                        page_content=text,
                        metadata={
                            "source": str(path),
                            "parser": backend,
                            "file_name": path.name,
                        },
                    )
            except Exception as exc:
                logger.warning("PDF backend %s failed: %s", backend, exc)
                last_error = exc
                continue

        raise RuntimeError(
            f"All PDF backends failed for {path}. Last error: {last_error}"
        )

    async def load_from_url(self, url: str) -> Document:
        """Download a PDF from *url* then parse it."""
        import tempfile

        import httpx

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(response.content)
                tmp_path = Path(tmp.name)

        try:
            return await self.load(tmp_path)
        finally:
            tmp_path.unlink(missing_ok=True)

    # ------------------------------------------------------------------
    # Backend parsers
    # ------------------------------------------------------------------

    async def _parse_with(self, path: Path, backend: str) -> str:
        if backend == "pypdf":
            return self._parse_pypdf(path)
        elif backend == "pdfplumber":
            return self._parse_pdfplumber(path)
        elif backend == "unstructured":
            return await self._parse_unstructured(path)
        else:
            raise ValueError(f"Unknown PDF backend: {backend}")

    @staticmethod
    def _parse_pypdf(path: Path) -> str:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages)

    @staticmethod
    def _parse_pdfplumber(path: Path) -> str:
        import pdfplumber

        with pdfplumber.open(str(path)) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        return "\n\n".join(pages)

    @staticmethod
    async def _parse_unstructured(path: Path) -> str:
        from langchain_community.document_loaders import UnstructuredPDFLoader

        loader = UnstructuredPDFLoader(str(path))
        docs = loader.load()
        return "\n\n".join(d.page_content for d in docs)
