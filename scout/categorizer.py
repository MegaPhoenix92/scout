"""Categorizes findings into thematic groups."""

import re
from collections import Counter
from scout.types import Finding, Category


# Base categories that apply broadly
BASE_CATEGORIES = {
    "Challenges & Pain Points": [
        "challenge", "problem", "difficult", "struggle", "pain", "frustrat",
        "limitation", "bottleneck", "obstacle", "barrier", "fail", "issue",
    ],
    "Tools & Solutions": [
        "tool", "framework", "platform", "library", "sdk", "api", "solution",
        "open source", "package", "module",
    ],
    "Market & Trends": [
        "market", "trend", "growth", "forecast", "adoption", "investment",
        "funding", "valuation", "revenue", "startup",
    ],
    "Cost & Economics": [
        "cost", "expensive", "pricing", "roi", "budget", "afford", "savings",
        "payback", "economic",
    ],
    "Safety & Risk": [
        "safety", "risk", "security", "danger", "regulation", "compliance",
        "ethical", "liability", "privacy",
    ],
    "Technical Deep-Dive": [
        "algorithm", "architecture", "implementation", "performance", "benchmark",
        "optimization", "latency", "throughput", "scalab",
    ],
    "Community & Discussion": [
        "ask hn", "show hn", "launch hn", "discussion", "opinion", "debate",
        "community", "experience",
    ],
    "Case Studies": [
        "case study", "experience", "lessons", "postmortem", "retrospective",
        "built", "shipped", "deployed", "production",
    ],
    "Open Source Projects": [
        "github", "repository", "stars", "fork", "open source", "mit", "apache",
    ],
    "Research & Academia": [
        "paper", "research", "study", "arxiv", "university", "academic",
        "experiment", "methodology",
    ],
}


class Categorizer:
    def __init__(self, custom_categories: dict[str, list[str]] | None = None):
        self.categories = dict(BASE_CATEGORIES)
        if custom_categories:
            self.categories.update(custom_categories)

    def _match_category(self, text: str) -> list[str]:
        text_lower = text.lower()
        matched = []
        for cat_name, keywords in self.categories.items():
            if any(kw in text_lower for kw in keywords):
                matched.append(cat_name)
        return matched or ["Uncategorized"]

    def categorize(self, findings: list[Finding]) -> list[Category]:
        """Group findings into categories."""
        cat_map: dict[str, list[Finding]] = {}

        for f in findings:
            text = f"{f.title} {f.snippet} {f.full_text}"
            cats = self._match_category(text)
            f.categories = cats
            for cat in cats:
                cat_map.setdefault(cat, []).append(f)

        # Build Category objects sorted by count
        categories = []
        for name in sorted(cat_map, key=lambda k: -len(cat_map[k])):
            items = cat_map[name]
            # Sort within category by relevance
            items.sort(key=lambda x: (x.relevance_score, x.upvotes + x.stars), reverse=True)
            categories.append(Category(name=name, findings=items, count=len(items)))

        return categories

    def auto_discover_topics(self, findings: list[Finding], top_n: int = 5) -> list[str]:
        """Discover top recurring topics from finding titles."""
        words = Counter()
        stop = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                "to", "of", "in", "for", "on", "with", "at", "by", "from",
                "and", "or", "not", "this", "that", "it", "its", "as", "but",
                "hn", "show", "ask", "launch", "http", "https", "www", "com"}
        for f in findings:
            for w in re.findall(r"\b[a-z]{3,}\b", f.title.lower()):
                if w not in stop:
                    words[w] += 1
        return [w for w, _ in words.most_common(top_n)]
