# Scout — Agentic Web Research Platform

## Overview

Scout is TROZLAN's agentic web research platform. It autonomously researches any topic across multiple web sources, categorizes findings, extracts insights, and delivers structured reports. Scout operates as a standalone CLI tool, an MCP server for AI agent tool-use, and a multi-user application with RBAC — all integrated into the TROZLAN ecosystem via `agent-gateway`.

**Ecosystem Position:**
```
┌─────────────────────────────────────────────────────────────┐
│                    agent-gateway/                            │
│          (Identity, Policy Gate, Capability Registry)        │
├──────────┬──────────┬──────────┬──────────┬────────────────┤
│  nous/   │ scout/   │billbridge│ trozlanio│  other agents  │
│   AI     │ Research │  Intel   │   Main   │                │
│ Assistant│  Agent   │Accountant│   App    │                │
└──────────┴──────────┴──────────┴──────────┴────────────────┘
```

---

## Architecture

### Agentic Pipeline (Complete Flow)

```
┌──────────────────────────────────────────────────────────────────┐
│                    SCOUT AGENTIC FLOW                             │
│                                                                   │
│  ┌──────────┐    ┌─────────────────────────────────────────────┐ │
│  │  INPUT   │    │         ResearchAgent (Orchestrator)         │ │
│  │          │    │                                              │ │
│  │ - CLI    │───▶│  [1] QueryGenerator                         │ │
│  │ - MCP    │    │      Topic → multi-source search queries    │ │
│  │ - API    │    │                    │                         │ │
│  │ - Gateway│    │  [2] Scraper (ThreadPoolExecutor)           │ │
│  └──────────┘    │      ┌──────────┬──────────┬──────────┐    │ │
│                  │      │ HN API   │ GitHub   │ Web/DDG  │    │ │
│                  │      └──────────┴──────────┴──────────┘    │ │
│                  │                    │                         │ │
│                  │  [3] Extractor                               │ │
│                  │      Content enrichment + relevance scoring  │ │
│                  │      Pain point sentence extraction          │ │
│                  │                    │                         │ │
│                  │  [4] Categorizer                             │ │
│                  │      Keyword clustering → themed groups      │ │
│                  │                    │                         │ │
│                  │  [5] Synthesizer                             │ │
│                  │      Statistics + ranking + report assembly  │ │
│                  │                    │                         │ │
│                  │  [6] Formatter (JSON / Markdown / Text)      │ │
│                  └─────────────────────┬───────────────────────┘ │
│                                        │                         │
│  ┌─────────────────────────────────────▼───────────────────────┐ │
│  │                      OUTPUT                                  │ │
│  │  - Structured Report (categories, findings, pain points)     │ │
│  │  - File export (JSON/MD/TXT)                                 │ │
│  │  - MCP structured response                                   │ │
│  │  - API response to agent-gateway                             │ │
│  └──────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### Pipeline Stage Details

| # | Stage | Module | Input | Output | Parallelism |
|---|-------|--------|-------|--------|-------------|
| 1 | Query Generation | `query_generator.py` | Topic string | SearchQuery list | Single |
| 2 | Scraping | `scraper.py` + `sources/` | Queries | Raw findings | ThreadPoolExecutor |
| 3 | Extraction | `extractor.py` | Findings | Enriched findings + pain sentences | Sequential |
| 4 | Categorization | `categorizer.py` | Findings | Themed categories | Single |
| 5 | Synthesis | `synthesizer.py` | Categories | Report object | Single |
| 6 | Formatting | `formatters/` | Report | JSON / MD / TXT | Single |

---

## Agent-Gateway Integration

### Capability Registration

Scout registers with `agent-gateway` as a research capability:

```javascript
// agent-gateway capability registration
{
  source_app: "scout",
  agent_id: "scout-research-agent",
  capability_key: "web_research",
  version: "0.1.0",
  lifecycle: "active",
  scopes: ["research:execute", "research:read"],
  metadata: {
    tools: [
      "scout_research",
      "scout_search_hackernews",
      "scout_search_github",
      "scout_scrape_url",
      "scout_generate_queries"
    ],
    transport: ["stdio", "streamable-http"],
    depth_levels: ["quick", "medium", "deep"]
  }
}
```

### Identity Resolution

Scout uses the gateway's identity service for user context:

```
User Request → agent-gateway
    → Identity Service (person_id resolution)
    → Policy Gate (entitlement check: research:execute)
    → Delegation Router → Scout MCP
    → Scout processes request with user context
    → Response → agent-gateway → User
```

### Policy Gate Authorization Flow

```
┌────────────────┐     ┌──────────────┐     ┌──────────┐
│  User Request  │────▶│ Policy Gate   │────▶│  Scout   │
│                │     │              │     │          │
│ person_id      │     │ 1. Entitle?  │     │ Execute  │
│ role           │     │ 2. Risk?     │     │ Research │
│ tenant_id      │     │ 3. Decision  │     │          │
│ scope          │     │              │     │          │
└────────────────┘     └──────────────┘     └──────────┘
                              │
                       ┌──────▼──────┐
                       │ Audit Trail │
                       │ (logged)    │
                       └─────────────┘
```

### Agent Coordination

Scout participates in multi-agent coordination via `agent-gateway`:

```bash
# Scout registers heartbeat
AGENT_ID=scout npm run agent:heartbeat

# Scout checks inbox for research requests
AGENT_ID=scout npm run agent:inbox

# Scout shares findings with other agents
node scripts/agent-coord.cjs share-findings "research" \
  '{"topic":"AI robotics","findings":42}'

# Scout hands off to billbridge for cost analysis
node scripts/agent-coord.cjs handoff billbridge \
  --context "Market research complete, need cost analysis"
```

---

## RBAC (Role-Based Access Control)

### Role Hierarchy

Following the TROZLAN permission model (`trozlanio/shared/permissions.ts`):

```
godfather (50)    — Full system access, all research features
    │
ceo (40)          — All research, manage team quotas
    │
admin (30)        — All research, manage org settings
    │
sales_manager (28)— Research + market intelligence
    │
marketing_manager (25) — Research + competitor analysis
    │
user_admin (20)   — Research with standard limits
    │
sales_rep (15)    — Quick research only
    │
user (10)         — Quick research, read reports
    │
guest (0)         — Read public reports only
```

### Permissions

```python
# Scout-specific permissions (registered in shared/permissions.ts)
SCOUT_PERMISSIONS = {
    # Research execution
    "research:execute":       "Run research pipelines",
    "research:execute:deep":  "Run deep research (higher resource usage)",
    "research:read":          "Read research reports",
    "research:export":        "Export reports (JSON/MD/TXT)",

    # Source access
    "research:source:hn":     "Search Hacker News",
    "research:source:github": "Search GitHub",
    "research:source:web":    "Scrape web articles",

    # Administration
    "research:admin:quotas":  "Manage research quotas",
    "research:admin:history": "View all users' research history",
    "research:admin:config":  "Configure Scout settings",

    # API / MCP access
    "research:api:mcp":       "Use Scout MCP tools",
    "research:api:rest":      "Use Scout REST API",
}
```

### Permission Matrix

| Permission | guest | user | sales_rep | user_admin | admin | godfather |
|-----------|-------|------|-----------|------------|-------|-----------|
| research:read | public only | own | own | own | all | all |
| research:execute | - | quick | quick | quick+medium | all | all |
| research:execute:deep | - | - | - | - | yes | yes |
| research:export | - | yes | yes | yes | yes | yes |
| research:source:hn | - | yes | yes | yes | yes | yes |
| research:source:github | - | yes | yes | yes | yes | yes |
| research:source:web | - | - | yes | yes | yes | yes |
| research:admin:quotas | - | - | - | - | yes | yes |
| research:admin:history | - | - | - | - | yes | yes |
| research:api:mcp | - | - | - | yes | yes | yes |

### Rate Limits by Role

| Role | Requests/hour | Depth allowed | Max sources | Report retention |
|------|--------------|---------------|-------------|-----------------|
| guest | 5 | - | - | - |
| user | 20 | quick | 2 | 7 days |
| sales_rep | 30 | quick | 2 | 30 days |
| user_admin | 50 | quick, medium | 3 | 90 days |
| admin | 200 | all | all | unlimited |
| godfather | unlimited | all | all | unlimited |

### Authorization Middleware

```python
# scout/middleware/auth.py (planned)
from scout.types import ResearchConfig

class AuthContext:
    person_id: str       # From agent-gateway identity service
    tenant_id: str       # Multi-tenant isolation
    role: str            # Role from RBAC hierarchy
    permissions: list    # Resolved permissions
    rate_limit: dict     # Rate limit config for this role

def authorize(required_permission: str):
    """Decorator for permission-gated endpoints."""
    def decorator(func):
        async def wrapper(ctx: AuthContext, *args, **kwargs):
            # 1. Validate session via agent-gateway
            # 2. Resolve person_id → role → permissions
            # 3. Check required_permission against granted
            # 4. Apply rate limiting
            # 5. Log authz event to audit trail
            # 6. Execute if authorized
            if not has_permission(ctx, required_permission):
                raise AuthorizationError(f"Missing: {required_permission}")
            return await func(ctx, *args, **kwargs)
        return wrapper
    return decorator
```

### Row-Level Security (RLS)

Following `billbridge` RLS patterns:

```sql
-- Research reports are tenant-scoped
CREATE POLICY research_tenant_isolation ON research_reports
  USING (tenant_id = current_setting('app.tenant_id'));

-- Users see only their own reports (unless admin)
CREATE POLICY research_user_isolation ON research_reports
  USING (
    user_id = current_setting('app.user_id')
    OR current_setting('app.role') IN ('admin', 'godfather')
    OR current_setting('app.bypass_rls') = 'true'
  );
```

---

## MCP Server (Tool Use)

Scout exposes its research capabilities as MCP tools for AI agent consumption:

```bash
# stdio mode (for Claude Code, agent-gateway, nous)
scout mcp

# HTTP mode (for web clients, multi-agent systems)
scout mcp --http --port 8001
```

### MCP Tools

| Tool | Description | Permission Required |
|------|-------------|-------------------|
| `scout_research` | Full autonomous research pipeline on any topic | `research:execute` |
| `scout_search_hackernews` | Search Hacker News stories | `research:source:hn` |
| `scout_search_github` | Search GitHub repositories | `research:source:github` |
| `scout_scrape_url` | Scrape a URL and extract content + pain points | `research:source:web` |
| `scout_generate_queries` | Generate search queries for research planning | `research:execute` |

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

For HTTP mode:
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

---

## Multi-Agent Communication

### How Other Agents Use Scout

```
┌──────────────────────────────────────────────────────────────────┐
│                    INTER-AGENT FLOWS                             │
│                                                                   │
│  nous/ (AI Assistant)                                             │
│    User: "Research AI robotics trends"                            │
│    → nous delegates to scout via agent-gateway                    │
│    → scout_research(topic="AI robotics trends", depth="medium")  │
│    → nous synthesizes response from Scout report                  │
│                                                                   │
│  billbridge/ (Intel Accountant)                                   │
│    Task: "Competitor pricing analysis"                            │
│    → billbridge requests scout_research(topic="...", depth="deep")│
│    → Scout returns market findings                                │
│    → billbridge integrates into financial models                  │
│                                                                   │
│  trozlanio/ (Main App)                                            │
│    Trigger: Scheduled industry monitoring                         │
│    → cron calls scout_research for configured topics              │
│    → Results stored in research_reports table                     │
│    → Dashboard shows latest findings                              │
│                                                                   │
│  Any Agent (via MCP)                                              │
│    → scout_search_hackernews(query="...")                         │
│    → scout_search_github(query="...")                             │
│    → scout_scrape_url(url="...")                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Agent Handoff Protocol

```python
# Scout completes research → hands off to specialist
{
    "handoff": {
        "from": "scout",
        "to": "billbridge",
        "context": {
            "research_id": "rpt_abc123",
            "topic": "AI robotics market",
            "findings_count": 42,
            "action_required": "cost_analysis",
            "categories": ["Cost & ROI", "Market & Trends"],
        }
    }
}
```

---

## Data Sources

| Source | API | Auth Required | Rate Limit | Depth: quick | medium | deep |
|--------|-----|---------------|------------|-------------|--------|------|
| Hacker News | Algolia Search | No | ~10k/hr | 10 | 25 | 50 |
| GitHub | REST API v3 | Optional | 10-30/min | 5 | 10 | 20 |
| Web | DDG + scraping | No | Respectful | 3 | 8 | 15 |

### Planned Sources (Roadmap)

| Source | Status | Priority |
|--------|--------|----------|
| arXiv | Planned | High |
| Reddit (via StealthyFetcher) | Planned | High |
| Stack Overflow | Planned | Medium |
| Twitter/X | Planned | Medium |
| Product Hunt | Planned | Low |
| Crunchbase | Planned | Low |

---

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

# MCP server
scout mcp                     # stdio mode
scout mcp --http --port 8001  # HTTP mode
```

## Python API

```python
from scout import ResearchAgent, ResearchConfig

# Configure and run
config = ResearchConfig(depth="deep", output_format="json")
agent = ResearchAgent(config)

# Get report object
report = agent.research("AI robotics challenges")

# Access results
print(f"Found {len(report.all_findings)} findings")
for cat in report.categories:
    print(f"  {cat.name}: {cat.count} items")

# Or research and save to file
path = agent.research_and_save("quantum computing trends")
```

---

## Database Schema (Planned)

```sql
-- Research reports (tenant-scoped, RLS-enabled)
CREATE TABLE research_reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    user_id         UUID NOT NULL REFERENCES users(id),
    person_id       TEXT NOT NULL,  -- agent-gateway canonical ID
    topic           TEXT NOT NULL,
    depth           TEXT NOT NULL CHECK (depth IN ('quick', 'medium', 'deep')),
    status          TEXT NOT NULL DEFAULT 'running'
                    CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
    total_findings  INT DEFAULT 0,
    categories      JSONB DEFAULT '{}',
    statistics      JSONB DEFAULT '{}',
    report_json     JSONB,
    report_markdown TEXT,
    created_at      TIMESTAMPTZ DEFAULT now(),
    completed_at    TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ  -- based on role retention policy
);

-- Individual findings (searchable)
CREATE TABLE research_findings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id       UUID NOT NULL REFERENCES research_reports(id) ON DELETE CASCADE,
    tenant_id       UUID NOT NULL,
    title           TEXT NOT NULL,
    url             TEXT NOT NULL,
    source          TEXT NOT NULL,  -- hackernews, github, web
    snippet         TEXT,
    relevance_score INT DEFAULT 0,
    upvotes         INT DEFAULT 0,
    stars           INT DEFAULT 0,
    categories      TEXT[] DEFAULT '{}',
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- Pain point sentences (extracted insights)
CREATE TABLE research_pain_points (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id       UUID NOT NULL REFERENCES research_reports(id) ON DELETE CASCADE,
    finding_id      UUID REFERENCES research_findings(id),
    tenant_id       UUID NOT NULL,
    sentence        TEXT NOT NULL,
    source_title    TEXT,
    source_url      TEXT,
    categories      TEXT[] DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- Research quotas (per tenant + role)
CREATE TABLE research_quotas (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    role            TEXT NOT NULL,
    max_per_hour    INT NOT NULL DEFAULT 20,
    max_depth       TEXT NOT NULL DEFAULT 'quick',
    retention_days  INT NOT NULL DEFAULT 30,
    created_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE (tenant_id, role)
);

-- Audit log (all research events)
CREATE TABLE research_audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL,
    person_id       TEXT NOT NULL,
    action          TEXT NOT NULL,  -- execute, read, export, admin
    resource        TEXT NOT NULL,  -- report_id, setting name
    outcome         TEXT NOT NULL,  -- allowed, denied, rate_limited
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- Indexes
CREATE INDEX idx_reports_tenant ON research_reports(tenant_id);
CREATE INDEX idx_reports_user ON research_reports(user_id);
CREATE INDEX idx_reports_topic ON research_reports USING gin(to_tsvector('english', topic));
CREATE INDEX idx_findings_report ON research_findings(report_id);
CREATE INDEX idx_findings_source ON research_findings(source);
CREATE INDEX idx_audit_tenant ON research_audit_log(tenant_id);
CREATE INDEX idx_audit_person ON research_audit_log(person_id);

-- RLS policies
ALTER TABLE research_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_findings ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_pain_points ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON research_reports
    USING (tenant_id = current_setting('app.tenant_id')::uuid);

CREATE POLICY user_or_admin ON research_reports
    USING (
        user_id = current_setting('app.user_id')::uuid
        OR current_setting('app.role') IN ('admin', 'godfather')
        OR current_setting('app.bypass_rls') = 'true'
    );
```

---

## Project Structure

```
scout/
├── pyproject.toml              # Package config, CLI entry point, deps
├── CLAUDE.md                   # This file — full architecture docs
├── .gitignore
├── scout/
│   ├── __init__.py             # Public API (ResearchAgent, ResearchConfig, Report)
│   ├── cli.py                  # Click CLI (research, quick, mcp commands)
│   ├── agent.py                # ResearchAgent — main pipeline orchestrator
│   ├── types.py                # Dataclasses (Config, Finding, Category, Report)
│   ├── query_generator.py      # Topic → multi-source search queries
│   ├── scraper.py              # Parallel multi-source scraper (ThreadPoolExecutor)
│   ├── extractor.py            # Content enrichment + pain point extraction
│   ├── categorizer.py          # Keyword-based finding categorization
│   ├── synthesizer.py          # Report assembly + statistics
│   ├── mcp_server.py           # FastMCP server (5 tools, stdio/http)
│   ├── sources/
│   │   ├── __init__.py
│   │   ├── hn.py               # Hacker News Algolia API
│   │   ├── github.py           # GitHub Search API v3
│   │   └── web.py              # DuckDuckGo Lite + article scraping
│   └── formatters/
│       ├── __init__.py
│       ├── json_fmt.py         # JSON output
│       ├── markdown_fmt.py     # Markdown output
│       └── text_fmt.py         # Plain text output
│
│   # Planned additions:
│   ├── middleware/
│   │   ├── auth.py             # Auth context + session validation
│   │   ├── rbac.py             # Permission checks + role enforcement
│   │   ├── rate_limit.py       # Per-role rate limiting
│   │   └── audit.py            # Audit trail logging
│   ├── api/
│   │   ├── router.py           # REST API routes
│   │   ├── schemas.py          # Pydantic request/response schemas
│   │   └── gateway_client.py   # Agent-gateway SDK client
│   ├── db/
│   │   ├── models.py           # SQLAlchemy/Drizzle models
│   │   ├── migrations/         # Alembic migrations
│   │   └── queries.py          # Report CRUD operations
│   └── sources/
│       ├── arxiv.py            # arXiv paper search (planned)
│       ├── reddit.py           # Reddit via StealthyFetcher (planned)
│       └── stackoverflow.py    # Stack Overflow search (planned)
```

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **No LLM for query generation** | Deterministic, offline, no API keys required. LLM optional enhancement later. |
| **Scrapling-powered fetching** | Stealth headers, anti-bot bypass, browser automation when needed |
| **ThreadPoolExecutor** | Sync Fetcher API + threaded concurrency (simple, effective) |
| **FastMCP server** | Follows Scrapling pattern, stdio + HTTP, structured Pydantic outputs |
| **Keyword-based categorization** | Fast, predictable, no training data needed. ML upgrade planned. |
| **Agent-gateway integration** | Centralized identity, policy, audit — not reinvented in Scout |
| **RLS at database level** | Tenant isolation enforced by PostgreSQL, not application code |
| **Pluggable sources/formatters** | Easy to add new data sources and output formats |

---

## Scaling Roadmap

### Phase 1 — MVP (Current)
- [x] CLI tool (`scout research`, `scout quick`)
- [x] MCP server (5 tools, stdio + HTTP)
- [x] 3 data sources (HN, GitHub, Web)
- [x] 3 output formats (JSON, Markdown, Text)
- [x] 3 depth levels (quick, medium, deep)
- [x] Pain point extraction
- [x] Categorization engine
- [x] Git repo + CLAUDE.md

### Phase 2 — Agent Integration
- [ ] Agent-gateway capability registration
- [ ] Identity resolution (person_id)
- [ ] Policy gate authorization
- [ ] Audit trail integration
- [ ] Agent handoff protocol (scout → billbridge, scout → nous)
- [ ] Agent coordination (heartbeat, inbox, task claiming)

### Phase 3 — Multi-User RBAC
- [ ] REST API (Hono or FastAPI)
- [ ] Auth middleware (session + JWT)
- [ ] RBAC permission enforcement
- [ ] Rate limiting per role
- [ ] PostgreSQL database schema
- [ ] RLS policies for tenant isolation
- [ ] Research report persistence
- [ ] Research history + search

### Phase 4 — Advanced Sources
- [ ] arXiv paper search
- [ ] Reddit via StealthyFetcher (bypass 403)
- [ ] Stack Overflow search
- [ ] Twitter/X search
- [ ] Product Hunt
- [ ] LLM-powered query generation (optional Claude API)
- [ ] Semantic similarity for deduplication (embeddings)

### Phase 5 — Production Features
- [ ] Scheduled research (cron-based topic monitoring)
- [ ] Research diffing (what changed since last run)
- [ ] Web dashboard (Next.js, following nous/trozlanio patterns)
- [ ] Email/Slack notifications for findings
- [ ] Webhook support for external integrations
- [ ] GCP Cloud Run deployment
- [ ] Redis caching layer
- [ ] Prometheus metrics + observability

### Phase 6 — Intelligence
- [ ] Trend detection across research runs
- [ ] Automated insight generation
- [ ] Cross-topic correlation
- [ ] Competitive intelligence dashboard
- [ ] Custom category training per tenant
- [ ] ML-powered relevance scoring
