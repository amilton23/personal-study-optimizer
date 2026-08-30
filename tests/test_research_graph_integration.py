import importlib
import json

from langchain_core.messages import AIMessage


class _FakeNotesLLM:
    def __init__(self, label: str) -> None:
        self.label = label

    def invoke(self, _messages):
        return AIMessage(
            content=(
                f"{self.label} note 1: clear explanation with simple memory tip.\n"
                f"{self.label} note 2: main concept and why it matters."
            )
        )


class _FakeDeckSummarizer:
    def __init__(self, deck_cls):
        self.deck_cls = deck_cls

    def invoke(self, _messages):
        cards = []
        for i in range(10):
            cards.append(
                {
                    "id": i + 1,
                    "category": "academic",
                    "subject": "Linear Regression",
                    "question": f"What is academic concept {i + 1}?",
                    "answer": f"Academic concept {i + 1} is a core idea in linear regression.",
                    "source": None,
                }
            )
        for i in range(10):
            cards.append(
                {
                    "id": i + 11,
                    "category": "practical",
                    "subject": "Linear Regression",
                    "question": f"How to apply practical concept {i + 1}?",
                    "answer": f"Apply practical concept {i + 1} in a simple prediction task.",
                    "source": None,
                }
            )
        return self.deck_cls(topic="Linear Regression", cards=cards)


def test_research_graph_handles_empty_search_without_unavailable(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    academic = importlib.import_module("src.agents.academic_researcher")
    practical = importlib.import_module("src.agents.corporate_researcher")
    graph_module = importlib.import_module("src.graph.research_graph")

    monkeypatch.setattr(academic, "search_web", lambda *args, **kwargs: [])
    monkeypatch.setattr(practical, "search_web", lambda *args, **kwargs: [])

    monkeypatch.setattr(academic, "_llm", _FakeNotesLLM("Academic"))
    monkeypatch.setattr(practical, "_llm", _FakeNotesLLM("Practical"))
    monkeypatch.setattr(
        graph_module,
        "_structured_summarizer",
        _FakeDeckSummarizer(graph_module.Deck),
    )

    result = graph_module.research_graph.invoke({"query": "Linear Regression"})

    assert result.get("validation_errors") == []

    payload = json.loads(result["final_report"])
    assert 1 <= len(payload["cards"]) <= 20

    for card in payload["cards"]:
        text = f"{card['question']} {card['answer']}".lower()
        assert "unavailable" not in text
        assert "not provided" not in text
