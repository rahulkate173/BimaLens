from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Service configuration. Secrets are supplied only through environment variables."""

    MONGODB_URI: str = ""
    MONGODB_DATABASE: str = "bimalens"

    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    SESSION_SECRET: str = ""
    INTERNAL_API_TOKEN: str = ""
    SESSION_COOKIE_SECURE: bool = False

    SARVAM_API_KEY: str = ""
    SARVAM_API_BASE: str = "https://api.sarvam.ai/v1"
    SARVAM_MODEL: str = "sarvam-105b-conversations"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "qwen/qwen3.8-27b"
    GOOGLE_API_KEY: str = ""
    GOOGLE_MODEL: str = "gemini-3.5-flash"

    OCR_PIPELINE_URL: str = "http://localhost:8001"
    PUBLIC_BACKEND_URL: str = "http://localhost:8000"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    MAX_UPLOAD_BYTES: int = 25 * 1024 * 1024
    LOG_LEVEL: str = "INFO"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
