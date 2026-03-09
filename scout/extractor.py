"""Enriches findings with full content and relevance scoring."""

import re
import time
from scrapling.fetchers import Fetcher
from scout.types import Finding, ResearchConfig


def _build_keyword_set(topic: str) -> set[str]:
    """Build keyword set from topic for relevance scoring."""
    words = set(topic.lower().split())
    # Add common research-related terms
    words.update([
        "challenge", "problem", "difficult", "struggle", "pain", "frustrat",
        "limitation", "bottleneck", "obstacle", "barrier", "issue", "fail",
        "expensive", "cost", "slow", "risk", "safety", "error",
        "solution", "tool", "framework", "platform", "approach",
        "trend", "growth", "market", "future", "adoption",
    ])
    return words


def _score_relevance(text: str, keywords: set[str]) -> int:
    """Score text relevance based on keyword matches."""
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw in text_lower)


def _extract_pain_sentences(text: str) -> list[str]:
    """Extract sentences that describe pain points or challenges."""
    patterns = [
        r"[^.]*(?:challenge|problem|difficult|struggle|limitation|obstacle|bottleneck|pain point)[^.]*\.",
        r"[^.]*(?:fail|crash|error|bug|broke)[^.]*\.",
        r"[^.]*(?:expensive|costly|prohibitive)[^.]*\.",
        r"[^.]*(?:safety|dangerous|risk|hazard)[^.]*\.",
        r"[^.]*(?:shortage|scarce|lack of|insufficient|missing)[^.]*\.",
        r"[^.]*(?:slow|latency|bottleneck|overhead)[^.]*\.",
    ]
    sentences = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            m = re.sub(r"<[^>]+>", "", m).strip()
            if 30 < len(m) < 300:
                sentences.append(m)
    return sentences


class Extractor:
    def __init__(self, config: ResearchConfig):
        self.config = config

    def enrich(self, findings: list[Finding], topic: str) -> tuple[list[Finding], list[dict]]:
        """Enrich findings with full text and relevance scores."""
        keywords = _build_keyword_set(topic)
        all_pain_sentences = []

        # Score all findings
        for f in findings:
            text = f"{f.title} {f.snippet} {f.full_text}"
            f.relevance_score = _score_relevance(text, keywords)

        # Sort by relevance, then scrape top articles
        findings.sort(key=lambda x: x.relevance_score, reverse=True)
        max_scrape = self.config.params["article_scrape"]
        scraped = 0

        for f in findings:
            if scraped >= max_scrape:
                break
            if f.full_text or not f.url or "news.ycombinator.com" in f.url:
                # Already have content or it's a discussion page
                if f.full_text:
                    sentences = _extract_pain_sentences(f.full_text)
                    for s in sentences:
                        all_pain_sentences.append({
                            "sentence": s,
                            "source_title": f.title,
                            "source_url": f.url,
                        })
                continue

            print(f"    Scraping: {f.url[:65]}...")
            try:
                page = Fetcher.get(f.url, verify=self.config.verify_ssl, timeout=10, stealthy_headers=True)
                if page.status == 200:
                    parts = []
                    for el in page.css("p, h2, h3, li"):
                        t = str(el.text or "").strip()
                        if len(t) > 25:
                            parts.append(t)
                    f.full_text = " ".join(parts)[:5000]

                    # Re-score with full text
                    full = f"{f.title} {f.full_text}"
                    f.relevance_score = _score_relevance(full, keywords)

                    # Extract pain sentences
                    sentences = _extract_pain_sentences(f.full_text)
                    for s in sentences:
                        all_pain_sentences.append({
                            "sentence": s,
                            "source_title": f.title,
                            "source_url": f.url,
                        })

                    scraped += 1
                    time.sleep(0.5)
            except Exception:
                pass

        # Re-sort after enrichment
        findings.sort(key=lambda x: x.relevance_score, reverse=True)
        return findings, all_pain_sentences
