"""Generates search queries from a research topic."""

from scout.types import SearchQuery, ResearchConfig

# Synonym expansions for common research angles
ANGLE_EXPANSIONS = {
    "problems": ["challenges", "issues", "pain points", "difficulties", "limitations", "obstacles"],
    "solutions": ["tools", "frameworks", "platforms", "approaches", "methods"],
    "trends": ["market", "growth", "adoption", "future", "forecast"],
    "comparison": ["vs", "alternative", "better than", "compared to"],
    "cost": ["pricing", "expensive", "affordable", "ROI", "budget"],
    "risk": ["safety", "security", "danger", "regulation", "compliance"],
    "experience": ["review", "experience", "case study", "lessons learned", "postmortem"],
}

# Research angles applied to any topic
RESEARCH_ANGLES = [
    "{topic}",
    "{topic} challenges problems",
    "{topic} tools solutions",
    "{topic} trends market 2025 2026",
    "{topic} cost expensive ROI",
    "{topic} risks safety limitations",
    "{topic} case study experience lessons",
    "{topic} open source github",
    "{topic} startup companies",
    "{topic} future predictions",
    "{topic} best practices",
    "{topic} failure postmortem",
    "{topic} integration deployment",
    "{topic} comparison alternatives",
    "{topic} community discussion",
]


class QueryGenerator:
    def generate(self, topic: str, config: ResearchConfig) -> list[SearchQuery]:
        num_queries = config.params["num_queries"]
        queries = []

        # Generate HN queries
        for i, angle in enumerate(RESEARCH_ANGLES[:num_queries]):
            q = angle.format(topic=topic)
            queries.append(SearchQuery(query=q, source="hn", priority=num_queries - i))

        # Generate GitHub queries
        github_queries = [
            topic,
            f"{topic} awesome",
            f"{topic} framework tool",
        ]
        for i, q in enumerate(github_queries[:max(2, num_queries // 3)]):
            queries.append(SearchQuery(query=q, source="github", priority=2 - i))

        # Generate web queries
        web_queries = [
            f"{topic} challenges 2025",
            f"{topic} industry report",
            f"{topic} overview guide",
        ]
        for i, q in enumerate(web_queries[:max(2, num_queries // 3)]):
            queries.append(SearchQuery(query=q, source="web", priority=2 - i))

        return sorted(queries, key=lambda x: -x.priority)
