from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from src.llm_providers.openai import get_openai_llm
from src.tools.web_search import format_results, search_web
from src.utils.logs import get_logger

logger = get_logger(__name__)
_llm = get_openai_llm()

INSTRUCTIONS = (
    "You are a senior practical analyst. "
    "Use only the provided sources, prioritizing recent and reachable ones; "
    "if using an older reference, add one sentence on why it still applies today. "
    "Extract 8-12 candidate insights framed as real-world problems or applications a learner "
    "could practice against. For each, provide: Scenario, Why it matters, How it's applied, "
    "Common pitfall, Source [title - url]. "
    "Prioritize didactic, hands-on value over theoretical completeness. "
    "If fewer than 8 sources support a distinct insight, return fewer rather than inventing one."
)


def practical_researcher_node(state: dict) -> dict:
    query = state["query"]
    logger.info("practical_researcher start | query=%r", query)
    sources = search_web(
        f"{query} (site:microsoft.com OR site:google.com OR site:ibm.com OR site:who.int OR site:fda.gov OR site:ema.europa.eu OR site:healthcareitnews.com)",
        max_results=12,
        recent=True,
        verify_urls=True,
    )

    logger.info("practical_researcher sources=%s", len(sources))
    prompt = (
        f"Research question: {query}\n\n"
        "Corporate/industry web findings:\n"
        f"{format_results(sources)}\n\n"
        "Task: extract 8-12 candidate practical insights using only these sources. "
        "For each insight provide: Scenario, Why it matters, How it's applied, Common pitfall, Source [title - url]."
    )

    response = _llm.invoke(
        [SystemMessage(content=INSTRUCTIONS), HumanMessage(content=prompt)]
    )
    logger.debug("practical_researcher response chars=%s", len(str(response.content)))
    return {
        "messages": [response],
        "sources": [item.url for item in sources],
    }


corporate_researcher_node = practical_researcher_node
