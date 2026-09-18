import os
from typing import Optional

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict

    class Settings(BaseSettings):
        PROJECT_NAME: str = "AI Knowledge Assistant AI Service"
        API_V1_STR: str = "/api/v1"
        DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/knowledge_assistant"
        REDIS_URL: str = "redis://localhost:6379/0"
        OPENAI_API_KEY: Optional[str] = None
        GEMINI_API_KEY: Optional[str] = None
        DEFAULT_EMBEDDING_PROVIDER: str = "gemini"
        EMBEDDING_MODEL: str = "text-embedding-004" # 768 dimensions
        LLM_MODEL: str = "gemini-2.5-flash"
        VISION_MODEL: str = "gemini-2.5-flash"
        INGESTION_STRATEGY: str = "standard"
        SHARED_STORAGE_PATH: str = "./storage"

        model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    settings = Settings()

except ImportError:
    class SettingsFallback:
        PROJECT_NAME: str = os.getenv("PROJECT_NAME", "AI Knowledge Assistant AI Service")
        API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")
        DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/knowledge_assistant")
        REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)
        GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
        DEFAULT_EMBEDDING_PROVIDER: str = os.getenv("DEFAULT_EMBEDDING_PROVIDER", "gemini")
        EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-004")
        LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-2.5-flash")
        VISION_MODEL: str = os.getenv("VISION_MODEL", "gemini-2.5-flash")
        INGESTION_STRATEGY: str = os.getenv("INGESTION_STRATEGY", "standard")
        SHARED_STORAGE_PATH: str = os.getenv("SHARED_STORAGE_PATH", "./storage")

    settings = SettingsFallback()
