"""Grounded chat workflow with relevance gating and verified citations."""

from collections.abc import Sequence
from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from .models import Answer, Citation, Message, Passage
from .ports import ChatModel, Embedder, VectorStore


class ChatState(TypedDict, total=False):
    question: str
    standalone_question: str
    model: str
    history: tuple[Message, ...]
    candidates: tuple[Passage, ...]
    passages: tuple[Passage, ...]
    answer: str
    abstained: bool


class GroundedChat:
    """Orchestrate retrieval and generation independently of the UI and providers."""

    def __init__(
        self,
        embedder: Embedder,
        vectors: VectorStore,
        chat: ChatModel,
        *,
        candidate_count: int = 20,
        final_count: int = 6,
        relevance_threshold: float = 0.2,
    ) -> None:
        self._embedder = embedder
        self._vectors = vectors
        self._chat = chat
        self._candidate_count = candidate_count
        self._final_count = final_count
        self._threshold = relevance_threshold
        builder = StateGraph(ChatState)
        builder.add_node("rewrite", self._rewrite)
        builder.add_node("retrieve", self._retrieve)
        builder.add_node("grade", self._grade)
        builder.add_node("generate", self._generate)
        builder.add_node("abstain", self._abstain)
        builder.add_edge(START, "rewrite")
        builder.add_edge("rewrite", "retrieve")
        builder.add_edge("retrieve", "grade")
        builder.add_conditional_edges("grade", self._route, ["generate", "abstain"])
        builder.add_edge("generate", END)
        builder.add_edge("abstain", END)
        self._graph = builder.compile()

    def answer(self, question: str, model: str, history: Sequence[Message] = ()) -> Answer:
        cleaned = question.strip()
        if not cleaned:
            raise ValueError("question must not be empty")
        result = self._graph.invoke(
            ChatState(question=cleaned, model=model, history=tuple(history))
        )
        passages = result.get("passages", ())
        citations = tuple(
            Citation(item.passage_id, item.source, item.position) for item in passages
        )
        return Answer(result["answer"], citations, model, result.get("abstained", False))

    def _rewrite(self, state: ChatState) -> ChatState:
        history = state.get("history", ())
        standalone = (
            self._chat.rewrite(model=state["model"], question=state["question"], history=history)
            if history
            else state["question"]
        )
        return ChatState(standalone_question=standalone.strip())

    def _retrieve(self, state: ChatState) -> ChatState:
        vector = self._embedder.embed([state["standalone_question"]])[0]
        candidates = self._vectors.query(vector, self._candidate_count)
        return ChatState(candidates=tuple(candidates))

    def _grade(self, state: ChatState) -> ChatState:
        selected = self._select_diverse(state.get("candidates", ()), self._final_count)
        relevant = tuple(item for item in selected if item.score >= self._threshold)
        return ChatState(passages=relevant)

    @staticmethod
    def _route(state: ChatState) -> Literal["generate", "abstain"]:
        return "generate" if state.get("passages") else "abstain"

    def _generate(self, state: ChatState) -> ChatState:
        answer = self._chat.complete(
            model=state["model"], question=state["question"], passages=state["passages"]
        )
        return ChatState(answer=answer, abstained=False)

    @staticmethod
    def _abstain(state: ChatState) -> ChatState:
        return ChatState(
            answer="I could not find enough relevant evidence in the indexed documents.",
            passages=(),
            abstained=True,
        )

    @staticmethod
    def _select_diverse(passages: Sequence[Passage], limit: int) -> tuple[Passage, ...]:
        """Prefer high scores while preventing one document from consuming all results."""
        ordered = sorted(passages, key=lambda item: item.score, reverse=True)
        selected: list[Passage] = []
        seen: set[str] = set()
        for item in ordered:
            if item.document_id not in seen:
                selected.append(item)
                seen.add(item.document_id)
            if len(selected) == limit:
                return tuple(selected)
        for item in ordered:
            if item not in selected:
                selected.append(item)
            if len(selected) == limit:
                break
        return tuple(selected)
