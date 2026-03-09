"""Web search and article scraping source."""

import re
import time
from scrapling.fetchers import Fetcher
from scout.types import Finding, ResearchConfig


def _search_duckduckgo(query: str, config: ResearchConfig) -> list[str]:
    """Get URLs from DuckDuckGo Lite."""
    url = f"https://lite.duckduckgo.com/lite/?q={query.replace(' ', '+')}"
    urls = []
    try:
        page = Fetcher.get(url, verify=config.verify_ssl, timeout=config.timeout, stealthy_headers=True)
        if page.status != 200:
            return urls
        for link in page.css("a.result-link, td a[href]"):
            href = str(link.attrib.get("href", ""))
            if href.startswith("http") and "duckduckgo" not in href:
                urls.append(href)
    except Exception:
        pass
    return urls[:config.params["web_pages"]]


def _scrape_article(url: str, config: ResearchConfig) -> dict | None:
    """Scrape an article page for content."""
    try:
        page = Fetcher.get(url, verify=config.verify_ssl, timeout=config.timeout, stealthy_headers=True)
        if page.status != 200:
            return None

        # Try to get title
        title = ""
        for sel in ["h1", "title", "meta[property='og:title']"]:
            el = page.css(sel)
            if el:
                if sel.startswith("meta"):
                    title = str(el[0].attrib.get("content", ""))
                else:
                    title = str(el[0].text or "")
                if title:
                    break

        # Extract main content
        text_parts = []
        # Try article containers first
        containers = page.css("article, main, [role='main'], .post-content, .article-body, .entry-content")
        if containers:
            target = containers[0]
        else:
            target = page

        for el in target.css("p, h2, h3, li"):
            t = str(el.text or "").strip()
            if len(t) > 30:
                text_parts.append(t)

        full_text = " ".join(text_parts)[:5000]

        if not title and not full_text:
            return None

        return {
            "title": title[:200],
            "full_text": full_text,
            "url": url,
        }
    except Exception:
        return None


def search_web(query: str, config: ResearchConfig) -> list[Finding]:
    """Search the web via DuckDuckGo and scrape results."""
    findings = []

    urls = _search_duckduckgo(query, config)
    if not urls:
        return findings

    for url in urls:
        article = _scrape_article(url, config)
        if article:
            findings.append(Finding(
                title=article["title"],
                url=article["url"],
                source="web",
                snippet=article["full_text"][:400],
                full_text=article["full_text"],
                metadata={"query": query},
            ))
            time.sleep(0.5)

    return findings
