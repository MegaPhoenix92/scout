# Scout — Agentic Web Research Tool

## Overview

Scout is TROZLAN's agentic web research tool powered by [Scrapling](https://github.com/D4Vinci/Scrapling). It autonomously researches any topic across multiple web sources, categorizes findings, extracts pain points, and generates structured reports.

**Part of the TROZLANIO ecosystem** — designed to integrate with:
- **agent-gateway/** — central agent orchestration hub
- **nous/** — TROZLAN AI assistant
- **billbridge/** — intel/accountant agent
- **trozlanio/** — main business application

## Architecture

```
User Topic (CLI / API / Agent Gateway)
    │
    ▼
┌──────────────────────────────────────────────────┐
│              ResearchAgent (Orchestrator)          │
│                                                    │
│  [1] QueryGenerator                                │
│      Topic → Search queries per source             │
│                                                    │
│  [2] Scraper (ThreadPoolExecutor)                  │
│      ┌─────────┬──────────┬───────────┐           │
│      │ HN API  │ GitHub   │ Web/DDG   │           │
│      └─────────┴──────────┴───────────┘           │
│                                                    │
│  [3] Extractor                                     │
│      Raw findings → Enriched content + scoring     │
│                                                    │
│  [4] Categorizer                                   │
│      Findings → Themed categories                  │
│                                                    │
│  [5] Synthesizer                                   │
│      Categories → Final Report                     │
│                                                    │
│  [6] Formatter (JSON / Markdown / Text)            │
└──────────────────────────────────────────────────┘
    │
    ▼
Output (file + console)
```

## Pipeline Stages

| Stage | Module | Input | Output |
|-------|--------|-------|--------|
| Query Generation | `query_generator.py` | Topic string | SearchQuery list |
| Scraping | `scraper.py` + `sources/` | Queries | Raw findings |
| Extraction | `extractor.py` | Findings | Enriched findings + pain sentences |
| Categorization | `categorizer.py` | Findings | Themed categories |
| Synthesis | `synthesizer.py` | Categories | Report object |
| Formatting | `formatters/` | Report | JSON / MD / TXT |

## Data Sources

| Source | API | Auth Required | Rate Limit |
|--------|-----|---------------|------------|
| Hacker News | Algolia Search API | No | ~10k/hr |
| GitHub | REST API v3 | Optional (GITHUB_TOKEN) | 10/min (unauth), 30/min (auth) |
| Web | DuckDuckGo Lite + article scraping | No | Respectful delays |

## CLI Usage

```bash
# Install
cd /Users/chrisozsvath/Projects/TROZLAN/TROZLANIO/scout
python3 -m venv .venv && source .venv/bin/activate
pip install -e .

# Research any topic
scout research "AI robotics pain points" --depth deep --format markdown -o report.md
scout research "electric vehicle market trends" -d medium -f json
scout research "remote work challenges 2025" -d quick -f text

# Quick shortcut
scout quick "blockchain scalability"
```

## Depth Levels

| Depth | HN Results | Web Pages | GitHub | Queries | Workers | Article Scrape |
|-------|-----------|-----------|--------|---------|---------|----------------|
| quick | 10 | 3 | 5 | 3 | 3 | 5 |
| medium | 25 | 8 | 10 | 6 | 5 | 12 |
| deep | 50 | 15 | 20 | 10 | 8 | 25 |

## Python API

```python
from scout import ResearchAgent, ResearchConfig

config = ResearchConfig(depth="deep", output_format="json")
agent = ResearchAgent(config)

# Get report object
report = agent.research("AI robotics challenges")

# Or research and save to file
path = agent.research_and_save("quantum computing trends")
```

## MCP Server (Tool Use)

Scout exposes its own MCP server so other agents can use it as a tool:

```bash
# stdio mode (for Claude Code, agent-gateway, nous, etc.)
scout mcp

# HTTP mode (for web clients, multi-agent systems)
scout mcp --http --port 8001
```

### MCP Tools

| Tool | Description |
|------|-------------|
| `scout_research` | Full autonomous research pipeline on any topic |
| `scout_search_hackernews` | Search Hacker News stories |
| `scout_search_github` | Search GitHub repositories |
| `scout_scrape_url` | Scrape a URL and extract content + pain points |
| `scout_generate_queries` | Generate search queries for planning |

### MCP Configuration

Add Scout to any agent's `.mcp.json`:

```json
{
  "mcpServers": {
    "scout": {
      "command": "/Users/chrisozsvath/Projects/TROZLAN/TROZLANIO/scout/.venv/bin/scout",
      "args": ["mcp"]
    }
  }
}
```

Or for HTTP mode:

```json
{
  "mcpServers": {
    "scout": {
      "url": "http://localhost:8001"
    }
  }
}
```

### MCP Tool Examples

```python
# From any MCP client (Claude Code, nous, agent-gateway):

# Full research
scout_research(topic="AI robotics challenges", depth="deep")

# Quick HN search
scout_search_hackernews(query="robotics startup failure", num_results=25)

# GitHub project search
scout_search_github(query="robot operating system", num_results=10)

# Scrape specific article
scout_scrape_url(url="https://example.com/article")

# Plan queries before running
scout_generate_queries(topic="quantum computing", depth="medium")
```

## Agent Gateway Integration

Scout is designed to be called from the TROZLAN agent-gateway as a research capability:

```python
# From agent-gateway, invoke Scout as a tool
from scout import ResearchAgent, ResearchConfig

async def handle_research_request(topic: str, depth: str = "medium"):
    config = ResearchConfig(depth=depth, output_format="json")
    agent = ResearchAgent(config)
    report = agent.research(topic)
    return {
        "topic": report.topic,
        "findings": len(report.all_findings),
        "categories": {c.name: c.count for c in report.categories},
        "statistics": report.statistics,
    }
```

### MCP Integration (Planned)

Scout will expose an MCP server for tool-use by AI agents:

```bash
scout mcp --http --port 8001
```

Tools:
- `scout_research(topic, depth)` — full research pipeline
- `scout_search(query, source)` — single source search
- `scout_scrape(url)` — scrape a specific URL

## Integration Map

```
┌─────────────────────────────────────────────────────────────┐
│                    agent-gateway/                            │
│                 (Central Orchestration)                      │
├──────────┬──────────┬──────────┬──────────┬────────────────┤
│  nous/   │ scout/   │billbridge│ trozlanio│  other agents  │
│   AI     │ Research │  Intel   │   Main   │                │
│ Assistant│  Agent   │Accountant│   App    │                │
└──────────┴──────────┴──────────┴──────────┴────────────────┘
```

### How Agents Use Scout

1. **nous/** (AI Assistant) — delegates research tasks to Scout
2. **billbridge/** (Intel Accountant) — uses Scout for market/competitor research
3. **trozlanio/** — uses Scout for automated industry monitoring
4. **agent-gateway/** — routes research requests to Scout

## Project Structure

```
scout/
├── pyproject.toml          # Package config, CLI entry point
├── CLAUDE.md               # This file
├── scout/
│   ├── __init__.py         # Public API
│   ├── cli.py              # Click CLI
│   ├── agent.py            # ResearchAgent orchestrator
│   ├── types.py            # Dataclasses (Config, Finding, Report)
│   ├── query_generator.py  # Topic → search queries
│   ├── scraper.py          # Parallel multi-source scraper
│   ├── extractor.py        # Content enrichment + pain extraction
│   ├── categorizer.py      # Keyword-based categorization
│   ├── synthesizer.py      # Report synthesis
│   ├── sources/
│   │   ├── hn.py           # Hacker News Algolia API
│   │   ├── github.py       # GitHub Search API
│   │   └── web.py          # DuckDuckGo + article scraping
│   └── formatters/
│       ├── json_fmt.py     # JSON output
│       ├── markdown_fmt.py # Markdown output
│       └── text_fmt.py     # Plain text output
└── .gitignore
```

## Key Design Decisions

- **No LLM dependency** — deterministic keyword-based query generation and categorization (fast, offline, no API keys)
- **Scrapling-powered** — uses Scrapling's `Fetcher` for all HTTP with stealth headers and anti-bot capabilities
- **ThreadPoolExecutor** — parallel scraping across sources (sync Fetcher, threaded concurrency)
- **Pluggable sources** — easy to add new data sources in `sources/`
- **Pluggable formatters** — easy to add new output formats

## Roadmap

- [ ] MCP server mode for AI agent tool-use
- [ ] Agent-gateway REST API integration
- [ ] StealthyFetcher for Reddit and protected sources
- [ ] arXiv paper search source
- [ ] LLM-powered query generation (optional, with Claude API)
- [ ] Scheduled research (cron-based monitoring)
- [ ] Research history and diff tracking
- [ ] Web dashboard for results visualization
