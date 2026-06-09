"""Centralized LLM factory supporting OpenAI and DeepSeek providers.

DeepSeek's API is OpenAI-compatible (base_url=https://api.deepseek.com/v1),
so we use langchain-openai's ChatOpenAI for both providers with different config.
"""

from __future__ import annotations

from typing import Literal

from langchain_core.embeddings import Embeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.core.config import settings

DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"

DEFAULT_MODELS: dict[str, str] = {
    "openai": "gpt-4o-mini",
    "deepseek": "deepseek-chat",
}


def get_active_provider() -> str:
    """Return the active LLM provider: 'deepseek' if configured, else 'openai'."""
    if settings.deepseek_api_key:
        return "deepseek"
    if settings.openai_api_key:
        return "openai"
    return "openai"


def create_chat_llm(
    model_name: str | None = None,
    temperature: float = 0.0,
    provider: Literal["openai", "deepseek"] | None = None,
) -> ChatOpenAI:
    """Create a ChatOpenAI instance for the given provider.

    Args:
        model_name: Override the default model for the active provider.
        temperature: Sampling temperature.
        provider: Force a specific provider. If None, auto-detects from settings.
    """
    provider = provider or get_active_provider()

    if provider == "deepseek":
        if not settings.deepseek_api_key:
            raise ValueError("DEEPSEEK_API_KEY is not set")
        model = model_name or settings.deepseek_model or DEFAULT_MODELS["deepseek"]
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=settings.deepseek_api_key,
            base_url=DEEPSEEK_BASE_URL,
        )
    else:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set")
        model = model_name or settings.openai_model or DEFAULT_MODELS["openai"]
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=settings.openai_api_key,
        )


def create_embeddings() -> Embeddings:
    """Create an embeddings instance.

    Priority:
    1. OpenAI embeddings (if OPENAI_API_KEY is set)
    2. Local HuggingFace sentence-transformers (always available as fallback)

    Note: DeepSeek does not currently offer a dedicated embeddings API,
    so we always use OpenAI or local embeddings regardless of LLM provider.
    """
    if settings.openai_api_key:
        return OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=settings.openai_api_key,
        )

    from langchain_community.embeddings import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(
        model_name=settings.local_embedding_model,
    )
