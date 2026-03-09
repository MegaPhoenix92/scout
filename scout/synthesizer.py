"""Synthesizes categorized findings into a final report."""

from datetime import datetime
from scout.types import Report, Category, Finding


class Synthesizer:
    def synthesize(
        self,
        topic: str,
        categories: list[Category],
        findings: list[Finding],
        pain_sentences: list[dict],
        depth: str,
    ) -> Report:
        # Build statistics
        source_counts = {}
        for f in findings:
            source_counts[f.source] = source_counts.get(f.source, 0) + 1

        cat_counts = {c.name: c.count for c in categories}

        top_by_engagement = sorted(
            findings,
            key=lambda x: (x.upvotes + x.stars) * max(x.relevance_score, 1),
            reverse=True,
        )[:10]

        stats = {
            "total_findings": len(findings),
            "sources": source_counts,
            "categories": cat_counts,
            "top_engaged": [
                {"title": f.title, "score": (f.upvotes + f.stars) * max(f.relevance_score, 1)}
                for f in top_by_engagement
            ],
            "avg_relevance": round(
                sum(f.relevance_score for f in findings) / max(len(findings), 1), 1
            ),
        }

        return Report(
            topic=topic,
            timestamp=datetime.now().isoformat(),
            config_depth=depth,
            categories=categories,
            all_findings=findings,
            statistics=stats,
            pain_sentences=pain_sentences,
        )
