"""ResearchAgent — the main orchestrator for Scout research pipeline."""

from datetime import datetime
from scout.types import ResearchConfig, Report
from scout.query_generator import QueryGenerator
from scout.scraper import Scraper
from scout.extractor import Extractor
from scout.categorizer import Categorizer
from scout.synthesizer import Synthesizer
from scout.formatters import FORMATTERS


class ResearchAgent:
    """Autonomous research agent that scrapes, analyzes, and reports on any topic."""

    def __init__(self, config: ResearchConfig | None = None):
        self.config = config or ResearchConfig()
        self.query_generator = QueryGenerator()
        self.scraper = Scraper(self.config)
        self.extractor = Extractor(self.config)
        self.categorizer = Categorizer()
        self.synthesizer = Synthesizer()

    def research(self, topic: str) -> Report:
        """Run the full research pipeline on a topic."""
        print(f"\n{'=' * 74}")
        print(f"  SCOUT — Agentic Web Research")
        print(f"  Topic: {topic}")
        print(f"  Depth: {self.config.depth} | Format: {self.config.output_format}")
        print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'=' * 74}")

        # Step 1: Generate queries
        print(f"\n[1/5] Generating search queries...")
        queries = self.query_generator.generate(topic, self.config)
        print(f"  Generated {len(queries)} queries across {len(set(q.source for q in queries))} sources")
        for q in queries[:5]:
            print(f"    [{q.source}] {q.query[:60]}")
        if len(queries) > 5:
            print(f"    ... and {len(queries) - 5} more")

        # Step 2: Scrape sources
        print(f"\n[2/5] Scraping sources...")
        findings = self.scraper.scrape(queries)
        print(f"  Collected {len(findings)} unique findings")

        # Step 3: Extract and enrich
        print(f"\n[3/5] Extracting and enriching content...")
        findings, pain_sentences = self.extractor.enrich(findings, topic)
        print(f"  Enriched findings, extracted {len(pain_sentences)} pain point statements")

        # Step 4: Categorize
        print(f"\n[4/5] Categorizing findings...")
        categories = self.categorizer.categorize(findings)
        print(f"  Organized into {len(categories)} categories")
        for c in categories[:5]:
            print(f"    {c.name}: {c.count} items")

        # Step 5: Synthesize
        print(f"\n[5/5] Synthesizing report...")
        report = self.synthesizer.synthesize(topic, categories, findings, pain_sentences, self.config.depth)

        return report

    def research_and_save(self, topic: str) -> str:
        """Run research and save output to file."""
        report = self.research(topic)

        # Format output
        formatter = FORMATTERS.get(self.config.output_format, FORMATTERS["text"])
        output = formatter(report)

        # Determine output path
        ext_map = {"json": ".json", "markdown": ".md", "text": ".txt"}
        ext = ext_map.get(self.config.output_format, ".txt")

        if self.config.output_path:
            path = self.config.output_path
        else:
            safe_topic = "".join(c if c.isalnum() or c in " -_" else "" for c in topic)
            safe_topic = safe_topic.replace(" ", "_").lower()[:50]
            path = f"scout_report_{safe_topic}{ext}"

        with open(path, "w") as f:
            f.write(output)

        # Also print to console
        print(f"\n{output}")
        print(f"\n  Report saved to: {path}")

        return path
