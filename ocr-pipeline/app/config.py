"""Application configuration loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration sourced from environment / .env file."""

    # --- Sarvam (primary LLM) ---
    SARVAM_API_KEY: str = ""
    SARVAM_API_BASE: str = "https://api.sarvam.ai/v1"

    # --- Groq (secondary LLM) ---
    GROQ_API_KEY: str = ""

    # --- Google Gemini (fallback LLM) ---
    GOOGLE_API_KEY: str = ""

    # --- Cloudinary ---
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # --- Backend ---
    BACKEND_CALLBACK_URL: str = "http://localhost:8000"
    INTERNAL_API_TOKEN: str = ""
    REDIS_URL: str = "redis://localhost:6379/0"
    OCR_QUEUE_NAME: str = "bimalens:ocr:jobs"
    MAX_PDF_BYTES: int = 25 * 1024 * 1024
    SARVAM_MODEL: str = "sarvam-105b"
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GOOGLE_MODEL: str = "gemini-2.0-flash"
    # OCR uses Gemini as primary (larger context window, structured output)
    OCR_PRIMARY_PROVIDER: str = "gemini"

    # --- Service ---
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    LOG_LEVEL: str = "INFO"

    # --- Rate limiting ---
    PAGE_CLASSIFICATION_CONCURRENCY: int = 1

    # --- Sarvam tuning ---
    SARVAM_MAX_TOKENS: int = 32768
    SARVAM_CONTEXT_LIMIT: int = 24000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
