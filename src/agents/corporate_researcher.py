from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from src.llm_providers.openai import get_openai_llm
from src.tools.web_search import format_results, search_web
from src.utils.logs import get_logger

logger = get_logger(__name__)
_llm = get_openai_llm()

INSTRUCTIONS = (
    "You are a practical tutor creating didactic study notes for a student. "
    "Prioritize simple real-world examples, use cases, and common mistakes. "
    "Use provided sources when available. If sources are weak or missing, still provide useful practical notes from standard knowledge. "
    "Never output placeholders like 'unavailable'. "
    "Keep language simple and concise."
)


def practical_researcher_node(state: dict) -> dict:
    query = state["query"]
    logger.info("practical_researcher start | query=%r", query)
    sources = search_web(
        f"{query} (site:google.com)",
        max_results=8,
        recent=False,
        verify_urls=False,
    )

    logger.info("practical_researcher sources=%s", len(sources))
    prompt = (
        f"Topic: {query}\n\n"
        "Practical web findings:\n"
        f"{format_results(sources)}\n\n"
        "Task: write 8-12 concise practical study notes.\n"
        "For each note include: concept/use case, simple example, when to use, common mistake, and source [title - url] when available.\n"
        "If web findings are insufficient, still provide the best practical notes for learning this topic."
    )

    response = _llm.invoke(
        [SystemMessage(content=INSTRUCTIONS), HumanMessage(content=prompt)]
    )
    logger.debug("practical_researcher response chars=%s", len(str(response.content)))
    return {
        "messages": [HumanMessage(content=f"Practical notes:\n{response.content}")],
        "sources": [item.url for item in sources],
    }


corporate_researcher_node = practical_researcher_node
