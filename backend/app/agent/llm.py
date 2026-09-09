"""
LangChain LLM factory supporting multi-provider setups with automatic failover.

We cascade providers (Gemini -> OpenRouter -> NVIDIA NIM) to maximize reliability.
The factory automatically instantiates clients for any provider with configured credentials.
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
    Constructs a LangChain chat model with bound tools and built-in redundancy.

    Provider cascade: Gemini -> OpenRouter -> NVIDIA NIM.
    This failover strategy ensures the system remains functional even if our primary
    LLM provider experiences an outage or rate limiting.

    Args:
        tools: A list of LangChain StructuredTool instances to expose to the LLM.

    Returns:
        A robust LangChain chat model equipped with tool calling and automatic failovers.
    """
    providers: list[BaseChatModel] = []

    if settings.gemini_api_key:
        providers.append(ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key,  # type: ignore[arg-type]
            temperature=0.2,
            max_retries=2,
            timeout=60,
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

    # Primary model is the first available provider; bind the tools to it directly
    primary = providers[0].bind_tools(tools)

    # Configure subsequent providers as automatic failovers, ensuring each also has access to the tools
    if len(providers) > 1:
        fallbacks = [p.bind_tools(tools) for p in providers[1:]]
        return primary.with_fallbacks(fallbacks)  # type: ignore[return-value]

    return primary  # type: ignore[return-value]
