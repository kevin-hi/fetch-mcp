#!/usr/bin/env python3
"""
MCP server for browser-like web fetching.
Replaces the default fetch MCP with one that mimics real browser headers.
"""

import requests
from datetime import date
from html2text import HTML2Text
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("browser-fetch")


def get_chrome_version() -> int:
    """
    Estimate current Chrome version based on date.
    Chrome 122 released ~Feb 2024, ~13 releases/year (every 4 weeks).
    """
    base_version = 122
    base_date = date(2024, 2, 1)
    days_since = (date.today() - base_date).days
    versions_since = days_since // 28  # ~4 weeks per release
    return base_version + versions_since


def get_browser_headers() -> dict:
    """Generate browser headers with current Chrome version."""
    chrome_ver = get_chrome_version()
    return {
        "User-Agent": f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver}.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Sec-Ch-Ua": f'"Chromium";v="{chrome_ver}", "Not(A:Brand";v="24", "Google Chrome";v="{chrome_ver}"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"macOS"',
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    }


@mcp.tool()
def fetch(
    url: str,
    max_length: int = 5000,
    start_index: int = 0,
    raw: bool = False,
) -> str:
    """
    Fetch a URL with browser-like headers to avoid bot detection.

    Args:
        url: URL to fetch
        max_length: Maximum number of characters to return (default 5000)
        start_index: Start index for pagination (default 0)
        raw: If True, return raw HTML instead of markdown (default False)

    Returns:
        The page content as markdown (or raw HTML if raw=True)
    """
    session = requests.Session()
    response = session.get(url, headers=get_browser_headers(), timeout=30)
    response.raise_for_status()

    if raw:
        content = response.text
    else:
        h = HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        h.body_width = 0
        content = h.handle(response.text)

    # Apply pagination
    paginated = content[start_index : start_index + max_length]

    # Add continuation hint if truncated
    if len(content) > start_index + max_length:
        remaining = len(content) - (start_index + max_length)
        paginated += f"\n\n[Truncated. {remaining} chars remaining. Use start_index={start_index + max_length} to continue.]"

    return paginated


if __name__ == "__main__":
    mcp.run()
