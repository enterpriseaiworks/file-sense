from types import SimpleNamespace
from typing import cast

import pytest
from desktop_agent_api import main
from desktop_agent_api.main import ChatResponse, app, authorize, settings_dependency
from desktop_agent_configuration import Settings
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr


async def test_liveness() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_key_authentication() -> None:
    settings = cast(Settings, SimpleNamespace(app_api_key=SecretStr("expected")))
    with pytest.raises(HTTPException, match="valid API key"):
        authorize(settings, "wrong")
    assert authorize(settings, "expected") is None


async def test_chat_stream_emits_tokens_and_completion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_process(request: object, settings: object) -> ChatResponse:
        return ChatResponse(
            answer="grounded answer",
            citations=[],
            model="test-model",
            abstained=False,
            conversation_id="conversation-1",
        )

    monkeypatch.setattr(main, "process_chat", fake_process)
    app.dependency_overrides[settings_dependency] = lambda: object()
    app.dependency_overrides[authorize] = lambda: None
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/v1/chat/stream",
                json={"question": "question", "model": "test-model"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "event: token" in response.text
    assert '"conversation_id": "conversation-1"' in response.text
