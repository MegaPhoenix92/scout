"""Data sources for Scout research."""

from scout.sources.hn import search_hn
from scout.sources.github import search_github
from scout.sources.web import search_web

__all__ = ["search_hn", "search_github", "search_web"]
