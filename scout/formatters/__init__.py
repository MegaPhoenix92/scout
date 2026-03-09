"""Output formatters for Scout reports."""

from scout.formatters.json_fmt import format_json
from scout.formatters.markdown_fmt import format_markdown
from scout.formatters.text_fmt import format_text

FORMATTERS = {
    "json": format_json,
    "markdown": format_markdown,
    "text": format_text,
}

__all__ = ["FORMATTERS", "format_json", "format_markdown", "format_text"]
