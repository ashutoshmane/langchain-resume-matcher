"""Application configuration loaded from environment variables."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- LLM Provider ---
    # Set DEEPSEEK_API_KEY to use DeepSeek; otherwise OpenAI is used.
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"
    embedding_model: str = "text-embedding-3-small"
    local_embedding_model: str = "all-MiniLM-L6-v2"

    # --- Vector Store ---
    vector_store: Literal["chroma", "faiss"] = "chroma"
    chroma_persist_dir: str = "./data/chroma"
    faiss_index_dir: str = "./data/faiss"

    # --- Chunking ---
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # --- Scoring Weights ---
    weight_skills: float = 35.0
    weight_experience: float = 25.0
    weight_seniority: float = 15.0
    weight_domain: float = 10.0
    weight_education: float = 5.0
    weight_keywords: float = 10.0

    # --- LinkedIn / Web ---
    linkedin_user_agent: str = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    )
    linkedin_fallback_paste: bool = True

    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # --- Uploads ---
    upload_dir: str = "./data/uploads"
    max_upload_mb: int = 10

    @property
    def upload_path(self) -> Path:
        p = Path(self.upload_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()
