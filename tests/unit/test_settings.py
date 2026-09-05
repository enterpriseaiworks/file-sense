import pytest
from desktop_agent_configuration import Settings
from pydantic import ValidationError


def valid_environment() -> dict[str, str]:
    return {
        "DATABASE_URL": "postgresql+psycopg://user:secret@postgres/db",
        "REDIS_URL": "redis://redis:6379/0",
        "PINECONE_API_KEY": "pinecone-secret",
        "PINECONE_INDEX": "filesense",
        "PINECONE_HOST": "https://example.svc.pinecone.io",
        "EMBEDDING_MODEL_ALIAS": "embedding-default",
        "EMBEDDING_DIMENSION": "1536",
        "CHAT_MODEL_ALIASES": "chat-fast, chat-quality",
        "LLM_GATEWAY_URL": "http://llm-gateway:4000",
        "LLM_GATEWAY_API_KEY": "gateway-secret",
        "APP_API_KEY": "app-secret",
    }


def test_settings_parse_model_aliases(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in valid_environment().items():
        monkeypatch.setenv(key, value)

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.chat_model_aliases == ("chat-fast", "chat-quality")
    assert "gateway-secret" not in repr(settings.llm_gateway_api_key)


def test_settings_reject_overlap_larger_than_chunk(monkeypatch: pytest.MonkeyPatch) -> None:
    environment = valid_environment() | {
        "CHUNK_SIZE_TOKENS": "100",
        "CHUNK_OVERLAP_TOKENS": "100",
    }
    for key, value in environment.items():
        monkeypatch.setenv(key, value)

    with pytest.raises(ValidationError, match="chunk overlap must be smaller"):
        Settings(_env_file=None)  # type: ignore[call-arg]
