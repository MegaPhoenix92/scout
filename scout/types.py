"""Data models for Scout research pipeline."""

from dataclasses import dataclass, field
from typing import Literal


DepthLevel = Literal["quick", "medium", "deep"]
OutputFormat = Literal["json", "markdown", "text"]


DEPTH_CONFIG = {
    "quick":  {"hn_per_query": 10, "web_pages": 3,  "github_results": 5,  "num_queries": 3,  "max_workers": 3,  "article_scrape": 5},
    "medium": {"hn_per_query": 25, "web_pages": 8,  "github_results": 10, "num_queries": 6,  "max_workers": 5,  "article_scrape": 12},
    "deep":   {"hn_per_query": 50, "web_pages": 15, "github_results": 20, "num_queries": 10, "max_workers": 8,  "article_scrape": 25},
}


@dataclass
class ResearchConfig:
    depth: DepthLevel = "medium"
    output_format: OutputFormat = "markdown"
    output_path: str | None = None
    proxy: str | None = None
    timeout: int = 15
    github_token: str | None = None
    verify_ssl: bool = False

    @property
    def params(self) -> dict:
        return DEPTH_CONFIG[self.depth]


@dataclass
class SearchQuery:
    query: str
    source: str  # "hn", "web", "github"
    priority: int = 0


@dataclass
class Finding:
    title: str
    url: str
    source: str
    snippet: str = ""
    full_text: str = ""
    relevance_score: int = 0
    upvotes: int = 0
    comments: int = 0
    stars: int = 0
    date: str = ""
    categories: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class Category:
    name: str
    findings: list[Finding] = field(default_factory=list)
    count: int = 0


@dataclass
class Report:
    topic: str
    timestamp: str = ""
    config_depth: str = ""
    categories: list[Category] = field(default_factory=list)
    all_findings: list[Finding] = field(default_factory=list)
    statistics: dict = field(default_factory=dict)
    pain_sentences: list[dict] = field(default_factory=list)
