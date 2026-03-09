"""Scout CLI — Agentic web research from the command line."""

import click
from scout.types import ResearchConfig
from scout.agent import ResearchAgent


@click.group()
@click.version_option(version="0.1.0", prog_name="scout")
def main():
    """Scout — Agentic web research tool powered by Scrapling.

    Research any topic autonomously across multiple sources.
    """
    pass


@main.command()
@click.argument("topic")
@click.option("--depth", "-d", type=click.Choice(["quick", "medium", "deep"]), default="medium",
              help="Research depth: quick (fast scan), medium (balanced), deep (thorough)")
@click.option("--format", "-f", "fmt", type=click.Choice(["json", "markdown", "text"]), default="text",
              help="Output format")
@click.option("--output", "-o", default=None, help="Output file path")
@click.option("--proxy", default=None, help="Proxy URL for requests")
@click.option("--timeout", "-t", type=int, default=15, help="Request timeout in seconds")
@click.option("--github-token", envvar="GITHUB_TOKEN", default=None, help="GitHub API token for higher rate limits")
def research(topic, depth, fmt, output, proxy, timeout, github_token):
    """Research a topic by scraping multiple web sources.

    Examples:

        scout research "AI robotics pain points"

        scout research "electric vehicle trends" --depth deep --format markdown

        scout research "remote work challenges" -d quick -f json -o results.json
    """
    config = ResearchConfig(
        depth=depth,
        output_format=fmt,
        output_path=output,
        proxy=proxy,
        timeout=timeout,
        github_token=github_token,
    )
    agent = ResearchAgent(config)
    agent.research_and_save(topic)


@main.command()
@click.argument("topic")
@click.option("--depth", "-d", type=click.Choice(["quick", "medium", "deep"]), default="quick")
def quick(topic, depth):
    """Quick research with text output (shortcut).

    Examples:

        scout quick "blockchain scalability"

        scout quick "LLM fine-tuning" -d medium
    """
    config = ResearchConfig(depth=depth, output_format="text")
    agent = ResearchAgent(config)
    agent.research_and_save(topic)


if __name__ == "__main__":
    main()
