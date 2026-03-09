"""JSON output formatter."""

import json
from dataclasses import asdict
from scout.types import Report


def format_json(report: Report) -> str:
    data = {
        "topic": report.topic,
        "timestamp": report.timestamp,
        "depth": report.config_depth,
        "statistics": report.statistics,
        "categories": [
            {
                "name": c.name,
                "count": c.count,
                "findings": [
                    {
                        "title": f.title,
                        "url": f.url,
                        "source": f.source,
                        "snippet": f.snippet[:300],
                        "relevance_score": f.relevance_score,
                        "upvotes": f.upvotes,
                        "stars": f.stars,
                        "comments": f.comments,
                        "date": f.date,
                        "categories": f.categories,
                    }
                    for f in c.findings
                ],
            }
            for c in report.categories
        ],
        "pain_sentences": report.pain_sentences,
    }
    return json.dumps(data, indent=2, default=str)
