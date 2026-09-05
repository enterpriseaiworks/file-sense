"""Thin Streamlit presentation layer for the FastAPI chat contract."""

import json
import os
from pathlib import Path

import httpx
import streamlit as st

logo_path = Path(__file__).with_name("assets") / "bot-avatar.png"

st.set_page_config(
    page_title="FileSense",
    page_icon=str(logo_path),
    layout="centered",
    initial_sidebar_state="collapsed",
)
st.markdown(
    """
    <style>
    :root {
        --chat-border: rgba(128, 128, 128, 0.24);
        --chat-surface: rgba(128, 128, 128, 0.08);
        --chat-muted: rgba(128, 128, 128, 0.82);
    }

    [data-testid="stHeader"],
    [data-testid="stToolbar"] {
        display: none;
    }

    [data-testid="stAppViewContainer"] > .main {
        background: radial-gradient(circle at 50% -20%, rgba(76, 139, 245, 0.08), transparent 42%);
    }

    .block-container {
        max-width: 820px;
        padding-top: 1.5rem;
        padding-bottom: 8rem;
    }

    .app-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        min-height: 3rem;
    }

    .app-header h1 {
        font-size: 1.05rem;
        font-weight: 650;
        letter-spacing: -0.01em;
        margin: 0;
    }

    .app-header p {
        color: var(--chat-muted);
        font-size: 0.78rem;
        margin: 0.12rem 0 0;
    }

    .header-rule {
        border-bottom: 1px solid var(--chat-border);
        margin: 0.8rem 0 1.8rem;
    }

    .welcome {
        display: flex;
        flex-direction: column;
        justify-content: center;
        min-height: 42vh;
        text-align: center;
    }

    .welcome h2 {
        font-size: clamp(1.8rem, 5vw, 2.5rem);
        letter-spacing: -0.035em;
        margin-bottom: 0.55rem;
    }

    .welcome p {
        color: var(--chat-muted);
        font-size: 1rem;
        margin: 0 auto;
        max-width: 32rem;
    }

    [data-testid="stChatMessage"] {
        background: transparent;
        border: 0;
        padding: 1.15rem 0;
        gap: 0.85rem;
    }

    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background: var(--chat-surface);
        border: 1px solid var(--chat-border);
        border-radius: 1.25rem;
        margin: 0.7rem 0 0.7rem auto;
        padding: 0.8rem 1rem;
        width: fit-content;
        max-width: 82%;
    }

    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"])
    [data-testid="stChatMessageAvatarUser"] {
        display: none;
    }

    [data-testid="stChatMessageContent"] p {
        line-height: 1.65;
    }

    [data-testid="stBottom"] {
        background: linear-gradient(transparent, var(--background-color) 28%);
        padding-bottom: 1.1rem;
    }

    [data-testid="stChatInput"] {
        background: var(--background-color);
        border: 1px solid var(--chat-border);
        border-radius: 1.5rem;
        box-shadow: 0 8px 28px rgba(0, 0, 0, 0.11);
        min-height: 3.7rem;
        overflow: hidden;
    }

    [data-testid="stChatInput"]:focus-within {
        border-color: rgba(76, 139, 245, 0.6);
        box-shadow: 0 8px 30px rgba(76, 139, 245, 0.13);
    }

    [data-testid="stChatInput"] textarea {
        padding-left: 0.45rem;
    }

    [data-testid="stSelectbox"] label {
        color: var(--chat-muted);
        font-size: 0.75rem;
    }

    @media (max-width: 640px) {
        .block-container {
            padding: 1rem 1rem 7rem;
        }

        .app-header p {
            display: none;
        }

        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
            max-width: 92%;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

header_logo, header_title, header_model = st.columns([0.55, 4.25, 2.2], vertical_alignment="center")
with header_logo:
    st.image(str(logo_path), width=42)
with header_title:
    st.markdown(
        """
        <div class="app-header">
            <div>
                <h1>FileSense</h1>
                <p>Grounded answers from your documents</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
api_base_url = os.getenv("API_BASE_URL", "http://api-gateway")
api_headers = {"X-API-Key": os.getenv("APP_API_KEY", "")}
try:
    response = httpx.get(f"{api_base_url}/v1/models", headers=api_headers, timeout=2.0)
    response.raise_for_status()
except httpx.HTTPError:
    st.error("The API service is unavailable. Check the local stack status.")
else:
    models = response.json()["models"]
    with header_model:
        selected_model = st.selectbox("Model", models, label_visibility="collapsed")
    st.markdown('<div class="header-rule"></div>', unsafe_allow_html=True)
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = None
    if not st.session_state.messages:
        st.markdown(
            """
            <div class="welcome">
                <h2>What can I help you find?</h2>
                <p>
                    Ask a question about your indexed documents. Answers stay
                    grounded in the content you provided.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    for message in st.session_state.messages:
        avatar = str(logo_path) if message["role"] == "assistant" else None
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])
            for file in message.get("files", []):
                st.link_button(f"Open {file['name']}", file["url"])
    if question := st.chat_input("Message your FileSense agent"):
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant", avatar=str(logo_path)):
            try:
                answer = ""
                files: list[dict[str, str]] = []
                current_event = ""
                placeholder = st.empty()
                with httpx.stream(
                    "POST",
                    f"{api_base_url}/v1/chat/stream",
                    headers=api_headers,
                    json={
                        "question": question,
                        "model": selected_model,
                        "conversation_id": st.session_state.conversation_id,
                    },
                    timeout=90.0,
                ) as answer_response:
                    answer_response.raise_for_status()
                    for line in answer_response.iter_lines():
                        if line.startswith("event: "):
                            current_event = line.removeprefix("event: ")
                        elif line.startswith("data: "):
                            payload = json.loads(line.removeprefix("data: "))
                            if current_event == "token":
                                answer += payload["text"]
                                placeholder.markdown(answer + "▌")
                            elif current_event == "files":
                                files = [
                                    {"name": str(item["name"]), "url": str(item["url"])}
                                    for item in payload["items"]
                                ]
                            elif current_event == "done":
                                st.session_state.conversation_id = payload["conversation_id"]
                            elif current_event == "error":
                                raise RuntimeError(payload["detail"])
            except httpx.HTTPError:
                answer = "The answer service failed safely. Check API and gateway logs."
            except (RuntimeError, ValueError, KeyError, TypeError):
                answer = "The answer stream ended unexpectedly. Check API logs."
            placeholder.markdown(answer)
            for file in files:
                st.link_button(f"Open {file['name']}", file["url"])
            st.session_state.messages.append(
                {"role": "assistant", "content": answer, "files": files}
            )
