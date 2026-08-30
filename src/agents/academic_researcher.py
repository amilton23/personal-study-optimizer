from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from src.llm_providers.gemini import get_gemini_llm
from src.tools.web_search import format_results, search_web
from src.utils.logs import get_logger

logger = get_logger(__name__)
_llm = get_gemini_llm()

INSTRUCTIONS = (
    "You are an academic tutor creating didactic study notes for a student. "
    "Prioritize clear definitions, first principles, and main concepts. "
    "Use provided sources when available. If sources are weak or missing, still provide useful foundational notes from standard knowledge. "
    "Never output placeholders like 'unavailable'. "
    "Keep language simple and concise."
)


def academic_researcher_node(state: dict) -> dict:
    query = state["query"]
    logger.info("academic_researcher start | query=%r", query)
    sources = search_web(
        f"{query} (site:google.com)",
        max_results=8,
        recent=False,
        verify_urls=False,
    )
    logger.info("academic_researcher sources=%s", len(sources))

    prompt = (
        f"Topic: {query}\n\n"
        "Academic web findings:\n"
        f"{format_results(sources)}\n\n"
        "Task: write 8-12 concise academic study notes.\n"
        "For each note include: concept name, what it is, why it matters, one memory tip, and source [title - url] when available.\n"
        "If web findings are insufficient, still provide the best foundational notes for learning this topic."
    )

    response = _llm.invoke(
        [SystemMessage(content=INSTRUCTIONS), HumanMessage(content=prompt)]
    )
    logger.debug("academic_researcher response chars=%s", len(str(response.content)))
    return {
        "messages": [HumanMessage(content=f"Academic notes:\n{response.content}")],
        "sources": [item.url for item in sources],
    }
