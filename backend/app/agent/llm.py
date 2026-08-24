"""
LangChain LLM factory — multi-provider with automatic fallback.

Providers tried in order:  Gemini → OpenRouter → NVIDIA NIM
Any provider with a non-empty API key is included.

To switch provider: just change the API key + model in .env.
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


def create_llm(tools: list[Any]) -> BaseChatModel:
    """
    Build a LangChain chat model bound with tools and automatic fallbacks.

    Provider priority: Gemini → OpenRouter → NVIDIA NIM
    Any provider whose API key is set in .env is automatically included.
    If the primary provider fails, LangChain transparently tries the next one.

    Args:
        tools: LangChain StructuredTool objects to bind.

    Returns:
        A LangChain chat model with tools bound and fallbacks configured.
    """
    providers: list[BaseChatModel] = []

    if settings.gemini_api_key:
        providers.append(ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key,  # type: ignore[arg-type]
            temperature=0.2,
            max_retries=0,
            timeout=30,
        ))
        logger.info("Provider added: Gemini (%s)", settings.gemini_model)

    if settings.openrouter_api_key:
        providers.append(ChatOpenAI(
            model=settings.openrouter_model,
            api_key=settings.openrouter_api_key,  # type: ignore[arg-type]
            base_url="https://openrouter.ai/api/v1",
            temperature=0.2,
            max_retries=0,
            timeout=30,
        ))
        logger.info("Provider added: OpenRouter (%s)", settings.openrouter_model)

    if settings.nvidia_api_key:
        providers.append(ChatOpenAI(
            model=settings.nvidia_model,
            api_key=settings.nvidia_api_key,  # type: ignore[arg-type]
            base_url="https://integrate.api.nvidia.com/v1",
            temperature=0.2,
            max_retries=0,
            timeout=30,
        ))
        logger.info("Provider added: NVIDIA NIM (%s)", settings.nvidia_model)

    if not providers:
        raise RuntimeError(
            "No LLM provider configured. Set at least one of: "
            "GEMINI_API_KEY, OPENROUTER_API_KEY, NVIDIA_API_KEY in .env"
        )

    # Bind tools to the primary provider
    primary = providers[0].bind_tools(tools)

    # Chain fallbacks — each also needs tools bound
    if len(providers) > 1:
        fallbacks = [p.bind_tools(tools) for p in providers[1:]]
        return primary.with_fallbacks(fallbacks)  # type: ignore[return-value]

    return primary  # type: ignore[return-value]
