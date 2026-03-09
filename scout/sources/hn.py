"""Hacker News Algolia API source."""

import time
from scrapling.fetchers import Fetcher
from scout.types import Finding, ResearchConfig


def search_hn(query: str, config: ResearchConfig) -> list[Finding]:
    """Search Hacker News via Algolia API."""
    num = config.params["hn_per_query"]
    url = f"https://hn.algolia.com/api/v1/search?query={query.replace(' ', '+')}&tags=story&hitsPerPage={num}"

    findings = []
    try:
        page = Fetcher.get(url, verify=config.verify_ssl, timeout=config.timeout)
        if page.status != 200:
            return findings

        data = page.json()
        for hit in data.get("hits", []):
            title = hit.get("title") or ""
            story_text = hit.get("story_text") or ""
            hn_url = f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"

            findings.append(Finding(
                title=title,
                url=hit.get("url") or hn_url,
                source="hackernews",
                snippet=story_text[:500],
                upvotes=hit.get("points") or 0,
                comments=hit.get("num_comments") or 0,
                date=hit.get("created_at", ""),
                metadata={"hn_url": hn_url, "query": query},
            ))
        time.sleep(0.3)
    except Exception as e:
        print(f"    [HN] Error for '{query[:40]}': {e}")

    return findings
