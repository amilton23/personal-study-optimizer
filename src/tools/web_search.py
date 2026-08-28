"""Live internet search utilities for agent nodes."""

from __future__ import annotations

import datetime as dt
import html
import os
import re
from collections.abc import Iterable
from dataclasses import dataclass
from urllib.parse import parse_qs, unquote, urlparse

import requests
from dotenv import find_dotenv, load_dotenv

from src.utils.logs import get_logger

load_dotenv(find_dotenv())

logger = get_logger(__name__)

DUCKDUCKGO_LITE_URL = "https://lite.duckduckgo.com/lite/"
DUCKDUCKGO_HTML_URL = "https://html.duckduckgo.com/html/"
TAVILY_SEARCH_URL = "https://api.tavily.com/search"
USER_AGENT = "Mozilla/5.0 (compatible; personal-research-agent/0.3)"
RECENT_WINDOW_YEARS = 2


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str
    reachable: bool | None = None


def search_web(
    query: str,
    max_results: int = 8,
    timeout: int = 20,
    recent: bool = True,
    verify_urls: bool = True,
) -> list[SearchResult]:
    """Return deduplicated live-web results with freshness prioritization.

    Strategy:
    1) Tavily API (if configured) for robust live search
    2) DuckDuckGo lite/html fallback scraping
    3) dedupe + freshness ranking + strict recency preference
    4) optional reachability checks
    """
    logger.info(
        "search_web start | query=%r max_results=%s recent=%s verify_urls=%s",
        query,
        max_results,
        recent,
        verify_urls,
    )

    if not query.strip():
        logger.warning("search_web received empty query")
        return []

    query_variants = _build_query_variants(query, recent=recent)

    collected: list[SearchResult] = []
    for variant in query_variants:
        logger.debug("search_web variant=%r", variant)

        tavily_items = _fetch_tavily(variant, max_results=max_results, timeout=timeout)
        logger.debug(
            "tavily returned %s results for variant=%r", len(tavily_items), variant
        )
        collected.extend(tavily_items)

        if len(collected) < max_results:
            google_items = _fetch_google_news_rss(
                variant, max_results=max_results, timeout=timeout
            )
            logger.debug(
                "google_news returned %s results for variant=%r",
                len(google_items),
                variant,
            )
            collected.extend(google_items)

        if len(collected) < max_results:
            ddg_lite_items = _fetch_duckduckgo_lite(
                variant, max_results=max_results, timeout=timeout
            )
            logger.debug(
                "ddg_lite returned %s results for variant=%r",
                len(ddg_lite_items),
                variant,
            )
            collected.extend(ddg_lite_items)
        if len(collected) < max_results:
            ddg_html_items = _fetch_duckduckgo_html(
                variant, max_results=max_results, timeout=timeout
            )
            logger.debug(
                "ddg_html returned %s results for variant=%r",
                len(ddg_html_items),
                variant,
            )
            collected.extend(ddg_html_items)

    results = _dedupe_results(collected)
    logger.info("search_web collected=%s deduped=%s", len(collected), len(results))
    if not results:
        logger.warning("search_web found no results after dedupe")
        return []

    if recent:
        results = sorted(
            results, key=lambda r: _freshness_score(r, query), reverse=True
        )
        results = _prefer_recent_results(results, max_results=max_results)

    if verify_urls:
        checked = [_with_reachability(item, timeout=8) for item in results]
        logger.debug("search_web reachability checked for %s results", len(checked))
        reachable_items = [item for item in checked if item.reachable]
        results = reachable_items if reachable_items else checked

    final_results = results[:max_results]
    logger.info("search_web returning %s results", len(final_results))
    return final_results


def format_results(results: list[SearchResult]) -> str:
    if not results:
        return "No sources found."

    lines: list[str] = []
    for item in results:
        availability = (
            "reachable"
            if item.reachable is True
            else "unverified"
            if item.reachable is None
            else "unreachable"
        )
        lines.append(
            f"- {item.title}\n"
            f"  URL: {item.url}\n"
            f"  Availability: {availability}\n"
            f"  Snippet: {item.snippet}"
        )
    return "\n".join(lines)


def _build_query_variants(query: str, recent: bool) -> list[str]:
    if not recent:
        return [query]

    year = dt.datetime.now().year
    return [query, f"{query} latest", f"{query} {year}", f"{query} {year - 1}"]


def _fetch_tavily(query: str, max_results: int, timeout: int) -> list[SearchResult]:
    api_key = (os.getenv("TAVILY_API_KEY") or "").strip()
    if not api_key:
        logger.debug("TAVILY_API_KEY not set; skipping Tavily search")
        return []

    payload = {
        "api_key": api_key,
        "query": query,
        "max_results": max_results,
        "search_depth": "advanced",
        "topic": "general",
        "time_range": "year",
        "include_answer": False,
        "include_raw_content": False,
    }
    headers = {"Content-Type": "application/json", "User-Agent": USER_AGENT}

    try:
        response = requests.post(
            TAVILY_SEARCH_URL, json=payload, headers=headers, timeout=timeout
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        logger.debug("Tavily request failed for query=%r: %s", query, exc)
        return []

    items = data.get("results") or []
    output: list[SearchResult] = []
    for item in items:
        url = str(item.get("url") or "").strip()
        title = str(item.get("title") or "").strip()
        snippet = str(item.get("content") or item.get("snippet") or "").strip()
        if url and title:
            output.append(SearchResult(title=title, url=url, snippet=snippet))
    return output


def _fetch_google_news_rss(
    query: str, max_results: int, timeout: int
) -> list[SearchResult]:
    rss_url = "https://news.google.com/rss/search"
    params = {"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"}

    try:
        response = requests.get(
            rss_url, params=params, timeout=timeout, headers={"User-Agent": USER_AGENT}
        )
        response.raise_for_status()
        xml = response.text
    except requests.RequestException as exc:
        logger.debug("Google News RSS request failed for query=%r: %s", query, exc)
        return []

    items = re.findall(r"<item>(.*?)</item>", xml, flags=re.S | re.I)
    output: list[SearchResult] = []
    for block in items[:max_results]:
        title_match = re.search(
            r"<title><!\[CDATA\[(.*?)\]\]></title>|<title>(.*?)</title>",
            block,
            flags=re.S | re.I,
        )
        link_match = re.search(r"<link>(.*?)</link>", block, flags=re.S | re.I)
        desc_match = re.search(
            r"<description><!\[CDATA\[(.*?)\]\]></description>|<description>(.*?)</description>",
            block,
            flags=re.S | re.I,
        )
        if not title_match or not link_match:
            continue

        title = _clean_html(title_match.group(1) or title_match.group(2) or "")
        url = html.unescape((link_match.group(1) or "").strip())
        snippet = (
            _clean_html(desc_match.group(1) or desc_match.group(2) or "")
            if desc_match
            else ""
        )

        if title and url:
            output.append(SearchResult(title=title, url=url, snippet=snippet))

    return output


def _fetch_duckduckgo_lite(
    query: str, max_results: int, timeout: int
) -> list[SearchResult]:
    try:
        response = requests.get(
            DUCKDUCKGO_LITE_URL,
            params={"q": query},
            timeout=timeout,
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.debug("DuckDuckGo lite request failed for query=%r: %s", query, exc)
        return []

    return list(_parse_lite_html(response.text, max_results=max_results))


def _fetch_duckduckgo_html(
    query: str, max_results: int, timeout: int
) -> list[SearchResult]:
    try:
        response = requests.get(
            DUCKDUCKGO_HTML_URL,
            params={"q": query},
            timeout=timeout,
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.debug("DuckDuckGo html request failed for query=%r: %s", query, exc)
        return []

    return list(_parse_ddg_html(response.text, max_results=max_results))


def _parse_lite_html(page_html: str, max_results: int) -> Iterable[SearchResult]:
    rows = re.findall(r"<tr>(.*?)</tr>", page_html, flags=re.S | re.I)

    title: str | None = None
    url: str | None = None
    snippet: str = ""
    emitted = 0

    for row in rows:
        if emitted >= max_results:
            break

        link_match = re.search(
            r"<a[^>]*class=['\"]result-link['\"][^>]*href=['\"]([^'\"]+)['\"][^>]*>(.*?)</a>",
            row,
            flags=re.S | re.I,
        )
        if link_match:
            if title and url:
                yield SearchResult(title=title, url=url, snippet=snippet.strip())
                emitted += 1
                if emitted >= max_results:
                    break
            raw_href = html.unescape(link_match.group(1))
            title = _clean_html(link_match.group(2))
            url = _resolve_result_url(raw_href)
            snippet = ""
            continue

        snippet_match = re.search(
            r"<td[^>]*class=['\"]result-snippet['\"][^>]*>(.*?)</td>",
            row,
            flags=re.S | re.I,
        )
        if snippet_match and title:
            snippet = _clean_html(snippet_match.group(1))

    if emitted < max_results and title and url:
        yield SearchResult(title=title, url=url, snippet=snippet.strip())


def _parse_ddg_html(page_html: str, max_results: int) -> Iterable[SearchResult]:
    result_blocks = re.findall(
        r"<div class=\"result\".*?</div>\s*</div>", page_html, flags=re.S | re.I
    )

    emitted = 0
    for block in result_blocks:
        if emitted >= max_results:
            break

        title_match = re.search(
            r"<a[^>]*class=['\"]result__a['\"][^>]*href=['\"]([^'\"]+)['\"][^>]*>(.*?)</a>",
            block,
            flags=re.S | re.I,
        )
        if not title_match:
            continue

        snippet_match = re.search(
            r"<a[^>]*class=['\"]result__snippet['\"][^>]*>(.*?)</a>|<div[^>]*class=['\"]result__snippet['\"][^>]*>(.*?)</div>",
            block,
            flags=re.S | re.I,
        )

        raw_href = html.unescape(title_match.group(1))
        title = _clean_html(title_match.group(2))
        snippet_raw = (
            snippet_match.group(1)
            if snippet_match and snippet_match.group(1)
            else (snippet_match.group(2) if snippet_match else "")
        )

        yield SearchResult(
            title=title,
            url=_resolve_result_url(raw_href),
            snippet=_clean_html(snippet_raw),
        )
        emitted += 1


def _resolve_result_url(raw_href: str) -> str:
    if "uddg=" not in raw_href:
        return raw_href

    parsed = urlparse(raw_href)
    query_params = parse_qs(parsed.query)
    wrapped = query_params.get("uddg", [raw_href])[0]
    return unquote(wrapped)


def _clean_html(fragment: str) -> str:
    text = re.sub(r"<.*?>", "", fragment)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _dedupe_results(items: list[SearchResult]) -> list[SearchResult]:
    seen: set[str] = set()
    output: list[SearchResult] = []
    for item in items:
        key = _canonical_url(item.url)
        if not key or key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output


def _canonical_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return ""
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")


def _with_reachability(item: SearchResult, timeout: int) -> SearchResult:
    reachable = _is_reachable(item.url, timeout=timeout)
    return SearchResult(
        title=item.title, url=item.url, snippet=item.snippet, reachable=reachable
    )


def _is_reachable(url: str, timeout: int) -> bool:
    headers = {"User-Agent": USER_AGENT}
    try:
        resp = requests.head(
            url, timeout=timeout, allow_redirects=True, headers=headers
        )
        if resp.status_code < 400:
            return True
        if resp.status_code in {403, 405}:
            fallback = requests.get(
                url, timeout=timeout, allow_redirects=True, headers=headers
            )
            return fallback.status_code < 400
        return False
    except requests.RequestException:
        return False


def _freshness_score(item: SearchResult, query: str) -> int:
    year = dt.datetime.now().year
    text = f"{item.title} {item.snippet} {item.url} {query}"

    score = 0
    years = _extract_years(text)
    if years:
        newest = max(years)
        score += max(0, 12 - abs(year - newest))

    title_l = item.title.lower()
    snippet_l = item.snippet.lower()
    url_l = item.url.lower()

    if any(
        token in title_l
        for token in ("latest", "news", "update", str(year), str(year - 1))
    ):
        score += 4
    if any(
        token in snippet_l
        for token in ("latest", "news", "update", "today", "recent", "breaking")
    ):
        score += 2
    if any(
        token in url_l
        for token in ("/news", "/press", "/blog", "newsroom", "announcement")
    ):
        score += 2

    if any(
        domain in item.url
        for domain in (
            ".gov",
            ".edu",
            "who.int",
            "nature.com",
            "thelancet.com",
            "nejm.org",
            "stanford.edu",
            "ai.stanford.edu",
            "cs.stanford.edu",
            "mit.edu",
            "csail.mit.edu",
            "news.mit.edu",
            "harvard.edu",
            "hms.harvard.edu",
            "seas.harvard.edu",
        )
    ):
        score += 3

    return score


def _prefer_recent_results(
    items: list[SearchResult], max_results: int
) -> list[SearchResult]:
    current_year = dt.datetime.now().year
    recent_items = [
        item for item in items if _is_recent_candidate(item, current_year=current_year)
    ]

    if len(recent_items) >= max(4, max_results):
        return recent_items

    older_items = [item for item in items if item not in recent_items]
    return [*recent_items, *older_items]


def _is_recent_candidate(item: SearchResult, current_year: int) -> bool:
    years = _extract_years(f"{item.title} {item.snippet} {item.url}")
    if years:
        return max(years) >= (current_year - RECENT_WINDOW_YEARS)

    url_l = item.url.lower()
    text_l = f"{item.title} {item.snippet}".lower()
    return any(
        token in url_l
        for token in ("/news", "/press", "/blog", "newsroom", "announcement")
    ) or any(
        token in text_l for token in ("latest", "new", "update", "today", "recent")
    )


def _extract_years(text: str) -> list[int]:
    current_year = dt.datetime.now().year
    years = [int(y) for y in re.findall(r"\b(20\d{2})\b", text)]
    return [y for y in years if 2018 <= y <= (current_year + 1)]
