"""GitHub search API source."""

import os
import time
from scrapling.fetchers import Fetcher
from scout.types import Finding, ResearchConfig


def search_github(query: str, config: ResearchConfig) -> list[Finding]:
    """Search GitHub repositories."""
    num = config.params["github_results"]
    url = f"https://api.github.com/search/repositories?q={query.replace(' ', '+')}&sort=stars&order=desc&per_page={num}"

    headers = {"Accept": "application/vnd.github.v3+json"}
    token = config.github_token or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    findings = []
    try:
        page = Fetcher.get(url, verify=config.verify_ssl, timeout=config.timeout, headers=headers)
        if page.status == 403:
            print("    [GitHub] Rate limited — pass --github-token or set GITHUB_TOKEN")
            return findings
        if page.status != 200:
            return findings

        data = page.json()
        for repo in data.get("items", []):
            desc = repo.get("description") or ""
            topics = repo.get("topics") or []

            findings.append(Finding(
                title=repo.get("full_name", ""),
                url=repo.get("html_url", ""),
                source="github",
                snippet=desc,
                stars=repo.get("stargazers_count", 0),
                date=repo.get("updated_at", ""),
                metadata={
                    "language": repo.get("language"),
                    "topics": topics,
                    "forks": repo.get("forks_count", 0),
                    "query": query,
                },
            ))
        time.sleep(0.5)
    except Exception as e:
        print(f"    [GitHub] Error for '{query[:40]}': {e}")

    return findings
