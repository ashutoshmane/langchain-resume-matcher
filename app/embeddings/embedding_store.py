"""Embedding store abstraction over Chroma and FAISS.

Provides a unified interface for:
- Creating embeddings for resume chunks
- Semantic similarity search
- Storing and retrieving document chunks
"""

from __future__ import annotations

import logging
from typing import Literal

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.core.llm_factory import create_embeddings

logger = logging.getLogger(__name__)


class EmbeddingStore:
    """Manages embeddings and vector storage for resume chunks."""

    def __init__(
        self,
        store_type: Literal["chroma", "faiss"] | None = None,
    ) -> None:
        store_type = store_type or settings.vector_store

        self.embeddings: Embeddings = create_embeddings()

        self.store_type = store_type
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        self._vectorstore = None

    async def index_resume(self, resume_doc: Document) -> None:
        """Chunk and embed a resume document into the vector store."""
        chunks = self.text_splitter.split_documents([resume_doc])
        logger.info("Split resume into %d chunks", len(chunks))

        if self.store_type == "chroma":
            await self._index_chroma(chunks)
        else:
            self._index_faiss(chunks)

    async def similarity_search(self, query: str, k: int = 5) -> list[Document]:
        """Semantic search over indexed resume chunks."""
        if self._vectorstore is None:
            logger.warning("Vector store not initialized; returning empty results")
            return []
        return self._vectorstore.similarity_search(query, k=k)

    async def similarity_search_with_score(
        self, query: str, k: int = 5
    ) -> list[tuple[Document, float]]:
        """Semantic search with relevance scores."""
        if self._vectorstore is None:
            return []
        return self._vectorstore.similarity_search_with_score(query, k=k)

    async def _index_chroma(self, chunks: list[Document]) -> None:
        from langchain_chroma import Chroma

        self._vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=settings.chroma_persist_dir,
        )

    def _index_faiss(self, chunks: list[Document]) -> None:
        from langchain_community.vectorstores import FAISS

        self._vectorstore = FAISS.from_documents(
            documents=chunks,
            embedding=self.embeddings,
        )

    def compute_similarity(self, text_a: str, text_b: str) -> float:
        """Compute cosine similarity between two text strings via embeddings."""
        import numpy as np

        emb_a = np.array(self.embeddings.embed_query(text_a))
        emb_b = np.array(self.embeddings.embed_query(text_b))

        dot = np.dot(emb_a, emb_b)
        norm = np.linalg.norm(emb_a) * np.linalg.norm(emb_b)
        if norm == 0:
            return 0.0
        return float(dot / norm)
