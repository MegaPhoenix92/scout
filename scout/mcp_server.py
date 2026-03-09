"""Scout MCP Server — Expose research tools for AI agent tool-use."""

from typing import Optional, Literal

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field


# ── Response Models ──

class ResearchResultModel(BaseModel):
    """Full research report result."""
    topic: str = Field(description="The research topic.")
    depth: str = Field(description="Research depth used (quick/medium/deep).")
    total_findings: int = Field(description="Total unique findings collected.")
    categories: dict[str, int] = Field(description="Category name to finding count mapping.")
    top_findings: list[dict] = Field(description="Top findings sorted by engagement x relevance.")
    pain_sentences: list[str] = Field(description="Extracted pain point statements from articles.")
    statistics: dict = Field(description="Research statistics (sources, avg relevance, etc).")


class SearchResultModel(BaseModel):
    """Single-source search result."""
    source: str = Field(description="The source searched (hackernews/github/web).")
    query: str = Field(description="The search query used.")
    results: list[dict] = Field(description="List of findings with title, url, snippet, score.")
    count: int = Field(description="Number of results returned.")


class ScrapeResultModel(BaseModel):
    """URL scrape result."""
    url: str = Field(description="The URL that was scraped.")
    title: str = Field(description="Page title.")
    content: str = Field(description="Extracted text content (truncated to 5000 chars).")
    status: int = Field(description="HTTP status code.")
    pain_sentences: list[str] = Field(description="Extracted pain point statements.")


class TopicQueriesModel(BaseModel):
    """Generated search queries for a topic."""
    topic: str = Field(description="The input topic.")
    queries: list[dict] = Field(description="Generated queries with source and priority.")


# ── MCP Server ──

class ScoutMCPServer:

    @staticmethod
    def research(
        topic: str,
        depth: Literal["quick", "medium", "deep"] = "medium",
        proxy: Optional[str] = None,
        timeout: int = 15,
        github_token: Optional[str] = None,
    ) -> ResearchResultModel:
        """Run a full autonomous research pipeline on any topic.

        Searches Hacker News, GitHub, and the web. Scrapes article content,
        extracts pain points, categorizes findings, and returns a structured report.

        Use this tool when you need comprehensive research on a topic.

        :param topic: The research topic (e.g. "AI robotics challenges", "remote work trends").
        :param depth: Research depth - "quick" (fast scan, ~30s), "medium" (balanced, ~2min), "deep" (thorough, ~5min).
        :param proxy: Optional proxy URL for requests.
        :param timeout: Request timeout in seconds. Default 15.
        :param github_token: Optional GitHub API token for higher rate limits.
        """
        from scout.types import ResearchConfig
        from scout.agent import ResearchAgent

        config = ResearchConfig(
            depth=depth,
            proxy=proxy,
            timeout=timeout,
            github_token=github_token,
        )
        agent = ResearchAgent(config)
        report = agent.research(topic)

        top_findings = []
        for f in sorted(
            report.all_findings,
            key=lambda x: (x.upvotes + x.stars) * max(x.relevance_score, 1),
            reverse=True,
        )[:20]:
            top_findings.append({
                "title": f.title,
                "url": f.url,
                "source": f.source,
                "snippet": f.snippet[:300],
                "relevance_score": f.relevance_score,
                "upvotes": f.upvotes,
                "stars": f.stars,
                "comments": f.comments,
                "categories": f.categories,
            })

        return ResearchResultModel(
            topic=report.topic,
            depth=report.config_depth,
            total_findings=len(report.all_findings),
            categories={c.name: c.count for c in report.categories},
            top_findings=top_findings,
            pain_sentences=[ps["sentence"] for ps in report.pain_sentences[:30]],
            statistics=report.statistics,
        )

    @staticmethod
    def search_hackernews(
        query: str,
        num_results: int = 25,
        timeout: int = 15,
    ) -> SearchResultModel:
        """Search Hacker News for stories matching a query.

        Uses the Algolia HN Search API. Good for finding discussions,
        Show HN posts, Launch HN posts, and Ask HN questions on any topic.

        :param query: Search query (e.g. "robotics challenges", "AI startup failure").
        :param num_results: Max number of results to return. Default 25.
        :param timeout: Request timeout in seconds.
        """
        from scout.types import ResearchConfig
        from scout.sources.hn import search_hn

        config = ResearchConfig(timeout=timeout)
        config.params  # ensure defaults loaded
        # Override per_query count
        original = config.params["hn_per_query"]
        config._custom_hn = num_results

        class PatchedConfig(ResearchConfig):
            @property
            def params(self):
                p = super().params.copy()
                p["hn_per_query"] = num_results
                return p

        patched = PatchedConfig(timeout=timeout)
        findings = search_hn(query, patched)

        return SearchResultModel(
            source="hackernews",
            query=query,
            results=[
                {
                    "title": f.title,
                    "url": f.url,
                    "snippet": f.snippet[:300],
                    "upvotes": f.upvotes,
                    "comments": f.comments,
                    "date": f.date,
                }
                for f in findings
            ],
            count=len(findings),
        )

    @staticmethod
    def search_github(
        query: str,
        num_results: int = 10,
        timeout: int = 15,
        github_token: Optional[str] = None,
    ) -> SearchResultModel:
        """Search GitHub repositories matching a query.

        Returns repos sorted by stars. Useful for finding open-source tools,
        frameworks, and projects related to a topic.

        :param query: Search query (e.g. "robotics framework", "web scraping python").
        :param num_results: Max results. Default 10.
        :param timeout: Request timeout in seconds.
        :param github_token: Optional GitHub API token for higher rate limits.
        """
        from scout.types import ResearchConfig
        from scout.sources.github import search_github

        class PatchedConfig(ResearchConfig):
            @property
            def params(self):
                p = super().params.copy()
                p["github_results"] = num_results
                return p

        config = PatchedConfig(timeout=timeout, github_token=github_token)
        findings = search_github(query, config)

        return SearchResultModel(
            source="github",
            query=query,
            results=[
                {
                    "title": f.title,
                    "url": f.url,
                    "snippet": f.snippet[:300],
                    "stars": f.stars,
                    "language": f.metadata.get("language"),
                    "topics": f.metadata.get("topics", []),
                    "date": f.date,
                }
                for f in findings
            ],
            count=len(findings),
        )

    @staticmethod
    def scrape_url(
        url: str,
        timeout: int = 15,
    ) -> ScrapeResultModel:
        """Scrape a URL and extract its text content and pain point statements.

        Fetches the page, extracts text from paragraphs/headings/lists,
        and identifies sentences describing challenges or problems.

        :param url: The URL to scrape.
        :param timeout: Request timeout in seconds.
        """
        import re
        from scrapling.fetchers import Fetcher

        try:
            page = Fetcher.get(url, verify=False, timeout=timeout, stealthy_headers=True)
            status = page.status

            # Extract title
            title = ""
            for sel in ["h1", "title"]:
                el = page.css(sel)
                if el:
                    title = str(el[0].text or "")
                    if title:
                        break

            # Extract content
            parts = []
            containers = page.css("article, main, [role='main']")
            target = containers[0] if containers else page
            for el in target.css("p, h2, h3, li"):
                t = str(el.text or "").strip()
                if len(t) > 25:
                    parts.append(t)
            content = " ".join(parts)[:5000]

            # Extract pain sentences
            pain_patterns = [
                r"[^.]*(?:challenge|problem|difficult|limitation|obstacle|pain point)[^.]*\.",
                r"[^.]*(?:fail|crash|error|broke)[^.]*\.",
                r"[^.]*(?:expensive|costly)[^.]*\.",
                r"[^.]*(?:safety|dangerous|risk)[^.]*\.",
            ]
            pain_sentences = []
            for pattern in pain_patterns:
                for m in re.findall(pattern, content, re.IGNORECASE):
                    m = re.sub(r"<[^>]+>", "", m).strip()
                    if 30 < len(m) < 300:
                        pain_sentences.append(m)

            return ScrapeResultModel(
                url=url,
                title=title,
                content=content,
                status=status,
                pain_sentences=pain_sentences[:10],
            )
        except Exception as e:
            return ScrapeResultModel(
                url=url,
                title="",
                content=f"Error: {str(e)}",
                status=0,
                pain_sentences=[],
            )

    @staticmethod
    def generate_queries(
        topic: str,
        depth: Literal["quick", "medium", "deep"] = "medium",
    ) -> TopicQueriesModel:
        """Generate search queries for a topic across multiple sources.

        Takes a topic and generates optimized search queries for
        Hacker News, GitHub, and web search. Useful for planning research.

        :param topic: The research topic.
        :param depth: Controls how many queries are generated. Default "medium".
        """
        from scout.types import ResearchConfig
        from scout.query_generator import QueryGenerator

        config = ResearchConfig(depth=depth)
        gen = QueryGenerator()
        queries = gen.generate(topic, config)

        return TopicQueriesModel(
            topic=topic,
            queries=[
                {"query": q.query, "source": q.source, "priority": q.priority}
                for q in queries
            ],
        )

    def serve(self, http: bool, host: str, port: int):
        """Start the Scout MCP server."""
        server = FastMCP(name="Scout", host=host, port=port)

        server.add_tool(
            self.research,
            title="scout_research",
            description=self.research.__doc__,
            structured_output=True,
        )
        server.add_tool(
            self.search_hackernews,
            title="scout_search_hackernews",
            description=self.search_hackernews.__doc__,
            structured_output=True,
        )
        server.add_tool(
            self.search_github,
            title="scout_search_github",
            description=self.search_github.__doc__,
            structured_output=True,
        )
        server.add_tool(
            self.scrape_url,
            title="scout_scrape_url",
            description=self.scrape_url.__doc__,
            structured_output=True,
        )
        server.add_tool(
            self.generate_queries,
            title="scout_generate_queries",
            description=self.generate_queries.__doc__,
            structured_output=True,
        )

        server.run(transport="stdio" if not http else "streamable-http")
