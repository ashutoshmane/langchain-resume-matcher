"""Text file loader for job descriptions and other plain-text inputs."""

from __future__ import annotations

from pathlib import Path

from langchain_core.documents import Document


class TextFileLoader:
    """Load a plain-text file (.txt, .md) into a LangChain Document."""

    async def load(self, file_path: Path | str) -> Document:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Text file not found: {path}")

        text = path.read_text(encoding="utf-8")
        return Document(
            page_content=text,
            metadata={
                "source": str(path),
                "file_name": path.name,
            },
        )

    @staticmethod
    def from_string(text: str, source: str = "pasted_text") -> Document:
        """Create a Document directly from a string (e.g. pasted JD text)."""
        return Document(
            page_content=text,
            metadata={"source": source},
        )
