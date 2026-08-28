from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from src.llm_providers.gemini import get_gemini_llm
from src.tools.web_search import format_results, search_web
from src.utils.logs import get_logger

logger = get_logger(__name__)
_llm = get_gemini_llm()

INSTRUCTIONS = (
    "You are a senior academic researcher. "
    "Use only the provided sources, prioritizing recent and reachable sources; "
    "if using a source older than 3 years, add one sentence justifying its continued relevance. "
    "Extract 8-12 candidate insights. For each, provide: "
    "Technique, What is new, Evidence/benchmark, Practical impact, Limitation, Source [title - url]. "
    "If fewer than 8 sources support a distinct insight, return fewer rather than duplicating or inventing one. "
    "Do not draw on outside knowledge not present in the provided sources."
)


def academic_researcher_node(state: dict) -> dict:
    query = state["query"]
    logger.info("academic_researcher start | query=%r", query)
    sources = search_web(
        f"{query} (site:arxiv.org OR site:nature.com OR site:nih.gov OR site:thelancet.com OR site:nejm.org OR site:bmj.com "
        "OR site:stanford.edu OR site:ai.stanford.edu OR site:cs.stanford.edu "
        "OR site:mit.edu OR site:news.mit.edu OR site:csail.mit.edu "
        "OR site:harvard.edu OR site:hms.harvard.edu OR site:seas.harvard.edu)",
        max_results=14,
        recent=True,
        verify_urls=True,
    )

    logger.info("academic_researcher sources=%s", len(sources))
    prompt = (
        f"Research question: {query}\n\n"
        "Academic web findings:\n"
        f"{format_results(sources)}\n\n"
        "Task: extract 8-12 candidate insights using only these sources. "
        "For each insight provide: Technique, What is new, Evidence/benchmark, Practical impact, Limitation, Source [title - url]."
    )

    response = _llm.invoke(
        [SystemMessage(content=INSTRUCTIONS), HumanMessage(content=prompt)]
    )
    logger.debug("academic_researcher response chars=%s", len(str(response.content)))
    return {
        "messages": [response],
        "sources": [item.url for item in sources],
    }
