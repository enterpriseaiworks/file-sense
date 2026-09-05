"""Validated runtime configuration with secret-safe diagnostics."""

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import AnyHttpUrl, Field, PositiveInt, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration shared by API, indexer, and UI-facing status checks."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    documents_path: Path = Path("./documents")

    database_url: SecretStr
    redis_url: SecretStr

    pinecone_api_key: SecretStr
    pinecone_index: str = Field(min_length=1)
    pinecone_host: AnyHttpUrl
    pinecone_namespace: str = Field(default="documents-v1", min_length=1)

    embedding_model_alias: str = Field(min_length=1)
    embedding_dimension: PositiveInt
    embedding_provider_model: str | None = None
    chat_model_aliases: Annotated[tuple[str, ...], NoDecode]
    chat_provider_model: str | None = None

    llm_gateway_url: AnyHttpUrl
    llm_gateway_api_key: SecretStr
    app_api_key: SecretStr
    api_base_url: AnyHttpUrl = AnyHttpUrl("http://api-gateway")
    public_api_base_url: AnyHttpUrl = AnyHttpUrl("http://localhost:8000")
    otel_exporter_otlp_endpoint: AnyHttpUrl | None = None

    max_file_size_mb: PositiveInt = 50
    max_request_size_kb: PositiveInt = 64
    retrieval_candidate_count: PositiveInt = 20
    retrieval_final_count: PositiveInt = 6
    relevance_threshold: float = Field(default=0.2, ge=-1, le=1)
    chunk_size_tokens: PositiveInt = 800
    chunk_overlap_tokens: int = Field(default=120, ge=0)
    index_sync_interval_seconds: PositiveInt = 300
    index_retry_attempts: PositiveInt = 3

    @field_validator("chat_model_aliases", mode="before")
    @classmethod
    def parse_model_aliases(cls, value: object) -> object:
        """Accept a comma-separated environment value while storing an immutable tuple."""
        if isinstance(value, str):
            return tuple(item.strip() for item in value.split(",") if item.strip())
        return value

    @field_validator("chat_model_aliases")
    @classmethod
    def require_model_alias(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value:
            raise ValueError("configure at least one chat model alias")
        return value

    @field_validator("chunk_overlap_tokens")
    @classmethod
    def overlap_must_be_smaller_than_chunk(cls, value: int, info: object) -> int:
        data = getattr(info, "data", {})
        chunk_size = data.get("chunk_size_tokens")
        if isinstance(chunk_size, int) and value >= chunk_size:
            raise ValueError("chunk overlap must be smaller than chunk size")
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and cache validated process configuration."""
    return Settings()  # type: ignore[call-arg]
