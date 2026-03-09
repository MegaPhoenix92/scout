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


@main.command()
@click.option("--http", is_flag=True, default=False,
              help="Run MCP server in streamable-http transport instead of stdio")
@click.option("--host", type=str, default="0.0.0.0",
              help="Host for HTTP transport (default: 0.0.0.0)")
@click.option("--port", type=int, default=8001,
              help="Port for HTTP transport (default: 8001)")
def mcp(http, host, port):
    """Run Scout's MCP server for AI agent tool-use.

    Exposes research tools via Model Context Protocol:

    \b
    Tools:
      scout_research         — Full autonomous research pipeline
      scout_search_hackernews — Search Hacker News
      scout_search_github    — Search GitHub repositories
      scout_scrape_url       — Scrape and extract from a URL
      scout_generate_queries — Generate search queries for a topic

    Examples:

        scout mcp                          # stdio mode (for Claude, etc.)

        scout mcp --http --port 8001       # HTTP mode
    """
    from scout.mcp_server import ScoutMCPServer
    server = ScoutMCPServer()
    server.serve(http, host, port)


if __name__ == "__main__":
    main()
