"""
Environment-aware configuration management.

Centralizes application settings with automatic environment variable bindings.
Orchestrates the LLM provider fallback hierarchy (Gemini -> OpenRouter -> NVIDIA)
to ensure high availability based on credential presence.
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings sourced from environment variables or .env file."""

    # Gemini
    gemini_api_key: str = Field(default="", description="Google Gemini API key")
    gemini_model: str = Field(default="gemini-3.6-flash", description="Gemini model name")

    # OpenRouter
    openrouter_api_key: str = Field(default="", description="OpenRouter API key")
    openrouter_model: str = Field(default="google/gemini-2.5-flash", description="OpenRouter model name")

    # NVIDIA NIM
    nvidia_api_key: str = Field(default="", description="NVIDIA NIM API key")
    nvidia_model: str = Field(default="mistralai/mistral-nemo-instruct-2407", description="NVIDIA NIM model name")

    # Agent
    max_agent_iterations: int = Field(default=15, ge=1, le=50)
    default_origin: str = Field(default="Ahmedabad")

    # Auth
    api_bearer_token: str = Field(default="tripcraft-dev-token")

    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


settings = Settings()
