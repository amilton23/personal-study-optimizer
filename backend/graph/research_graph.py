from __future__ import annotations

import json
import operator
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from pydantic import ValidationError

from backend.agents.academic_researcher import academic_researcher_node
from backend.agents.corporate_researcher import practical_researcher_node
from backend.graph.deck_models import (
    Deck,
    pick_random_cards_per_category,
    pick_random_cards_per_category_from_payload,
    validate_deck,
)
from backend.services.llm_providers.openai import get_openai_llm
from backend.services.utils.logs import get_logger


class ResearchState(TypedDict):
    query: str
    sources: Annotated[list[str], operator.add]
    final_report: str
    messages: Annotated[list[BaseMessage], operator.add]
    deck: dict
    validation_errors: list[str]
    retry_count: int


logger = get_logger(__name__)
_summarizer = get_openai_llm()
_structured_summarizer = _summarizer.with_structured_output(Deck)
_MAX_SUMMARY_RETRIES = 1
_SUMMARY_INSTRUCTIONS = (
    "You are a professor building didactic flashcards for student memorization. "
    "You will receive academic notes and practical notes about same topic. "
    "Selection rules:\n"
    "- Create up to 20 cards total.\n"
    "- Keep category balanced when possible, but never exceed 10 cards per category.\n"
    "- Focus on main concepts, simple explanations, and high learning value.\n"
    "- Use short, clear questions and direct answers.\n"
    "- Never output placeholders like 'unavailable' or 'brief not provided'.\n"
    "- If a source is present in notes, include it as [title - url]; otherwise set source to null.\n\n"
    "IMPORTANT: Before creating the cards, make sure they relatively answer the following main questions:"
    "1. What is it?\n"
    "2. How does it work?\n"
    "3. Why is it important?\n"
    "4. Why does it work?\n"
    "5. What would be examples for it?\n"
    "6. What would happen if I changed something in it?\n"
    "Output: return only the structured deck object matching the required schema. "
    "Do not add commentary, markdown, or text outside the schema."
)


def start_query_node(state: ResearchState) -> dict:
    logger.info("graph.start_query | query=%r", state["query"])
    return {"messages": [HumanMessage(content=state["query"])], "sources": []}


def summarize_node(state: ResearchState) -> dict:
    logger.info(
        "graph.summarize | messages=%s sources=%s retry=%s",
        len(state["messages"]),
        len(state["sources"]),
        state.get("retry_count", 0),
    )

    prompt_messages: list[BaseMessage] = [
        SystemMessage(content=_SUMMARY_INSTRUCTIONS),
        *state["messages"],
    ]

    feedback = state.get("validation_errors") or []
    if feedback:
        prompt_messages.append(
            HumanMessage(
                content=(
                    "Validation errors in previous output: "
                    + "; ".join(feedback)
                    + ". Regenerate and fix exactly these issues."
                )
            )
        )

    deck = _structured_summarizer.invoke(prompt_messages)
    if isinstance(deck, Deck):
        deck_payload = deck.model_dump()
    else:
        deck_payload = dict(deck)

    return {"deck": deck_payload}


def validate_deck_node(state: ResearchState) -> dict:
    try:
        deck = Deck.model_validate(state["deck"])
    except ValidationError as exc:
        logger.info("graph.validate_deck schema failure")
        deck = pick_random_cards_per_category_from_payload(state.get("deck", {}))
        if deck is None:
            errors = [f"schema validation failed: {exc.errors()}"]
            return {
                "validation_errors": errors,
                "retry_count": state.get("retry_count", 0) + 1,
            }

    errors = validate_deck(deck)

    if errors:
        logger.info("graph.validate_deck failed | errors=%s", errors)
        deck = pick_random_cards_per_category(deck)
        errors = validate_deck(deck)
        if errors:
            return {
                "validation_errors": errors,
                "retry_count": state.get("retry_count", 0) + 1,
            }

    deduped = _dedupe(state["sources"])
    logger.info("graph.validate_deck success | final_sources=%s", len(deduped))
    return {
        "validation_errors": [],
        "final_report": json.dumps(deck.model_dump(), ensure_ascii=False, indent=2),
        "sources": deduped,
    }


def route_after_validation(state: ResearchState) -> str:
    if not state.get("validation_errors"):
        return END
    if state.get("retry_count", 0) >= _MAX_SUMMARY_RETRIES:
        logger.warning("graph.validate_deck max retries reached")
        return END
    return "summarize"


def _dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def build_research_graph():
    graph = StateGraph(ResearchState)

    graph.add_node("start_query", start_query_node)
    graph.add_node("academic_researcher", academic_researcher_node)
    graph.add_node("corporate_researcher", practical_researcher_node)
    graph.add_node("summarize", summarize_node)
    graph.add_node("validate_deck", validate_deck_node)

    graph.set_entry_point("start_query")

    # Prefer explicit static edges over dynamic Send fan-out for cleaner
    # visualization/debugging in LangGraph dev + LangSmith Studio.
    graph.add_edge("start_query", "academic_researcher")
    graph.add_edge("start_query", "corporate_researcher")
    graph.add_edge(["academic_researcher", "corporate_researcher"], "summarize")
    graph.add_edge("summarize", "validate_deck")
    graph.add_conditional_edges("validate_deck", route_after_validation)

    return graph.compile()


research_graph = build_research_graph()
