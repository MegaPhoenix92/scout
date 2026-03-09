"""Scout - Agentic web research tool powered by Scrapling."""

__version__ = "0.1.0"

from scout.agent import ResearchAgent
from scout.types import ResearchConfig, Report

__all__ = ["ResearchAgent", "ResearchConfig", "Report"]
