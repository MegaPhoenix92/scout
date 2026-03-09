"""Multi-source scraper with parallel execution."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from scout.types import SearchQuery, Finding, ResearchConfig
from scout.sources import search_hn, search_github, search_web


SOURCE_MAP = {
    "hn": search_hn,
    "github": search_github,
    "web": search_web,
}


class Scraper:
    def __init__(self, config: ResearchConfig):
        self.config = config

    def _run_query(self, sq: SearchQuery) -> list[Finding]:
        fn = SOURCE_MAP.get(sq.source)
        if not fn:
            return []
        return fn(sq.query, self.config)

    def scrape(self, queries: list[SearchQuery]) -> list[Finding]:
        all_findings = []
        max_workers = self.config.params["max_workers"]

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {
                executor.submit(self._run_query, sq): sq
                for sq in queries
            }
            for future in as_completed(future_map):
                sq = future_map[future]
                try:
                    results = future.result(timeout=60)
                    all_findings.extend(results)
                except Exception as e:
                    print(f"    [{sq.source}] Query failed: {e}")

        # Deduplicate by URL
        seen = set()
        unique = []
        for f in all_findings:
            key = f.url.lower().rstrip("/")
            if key not in seen:
                seen.add(key)
                unique.append(f)

        return unique
