"""Small deterministic acceptance dataset for the retrieval/abstention contract."""

from collections.abc import Sequence

from desktop_agent_connectors import InMemoryVectorStore
from desktop_agent_rag_core import GroundedChat, Message, Passage


class KeywordEmbedder:
    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[1.0 if "policy" in text.lower() else 0.0, 1.0] for text in texts]


class ExtractiveChat:
    def rewrite(self, *, model: str, question: str, history: Sequence[Message]) -> str:
        return question

    def complete(self, *, model: str, question: str, passages: tuple[Passage, ...]) -> str:
        return passages[0].text


def test_relevant_question_is_grounded_and_unknown_question_abstains() -> None:
    vectors = InMemoryVectorStore()
    vectors.upsert([Passage("p", "d", "policy.md", "Policy requires approval.", 0)], [[1, 1]])
    workflow = GroundedChat(KeywordEmbedder(), vectors, ExtractiveChat(), relevance_threshold=0.8)
    grounded = workflow.answer("What does the policy require?", "test")
    assert not grounded.abstained
    assert grounded.citations[0].source == "policy.md"

    unknown = workflow.answer("What is the cafeteria menu?", "test")
    assert unknown.abstained
