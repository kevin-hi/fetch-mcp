#!/usr/bin/env python3
"""
MCP server for browser-like web fetching.
Replaces the default fetch MCP with one that mimics real browser headers.
"""

import platform
import requests
from datetime import date
from html2text import HTML2Text
from mcp.server.fastmcp import FastMCP
from urllib.parse import urlparse

mcp = FastMCP("browser-fetch")

# Module-level session for connection pooling and reuse
_session = None


def get_session() -> requests.Session:
    """Get or create a module-level session for connection reuse."""
    global _session
    if _session is None:
        _session = requests.Session()
    return _session


def get_chrome_version() -> int:
    """
    Estimate current Chrome version based on date.
    Chrome 122 released ~Feb 2024, ~13 releases/year (every 4 weeks).
    Capped at 200 to prevent unrealistic versions.
    """
    base_version = 122
    base_date = date(2024, 2, 1)
    days_since = (date.today() - base_date).days
    versions_since = days_since // 28  # ~4 weeks per release
    estimated = base_version + versions_since

    # Cap at version 200, fallback to base version if calculation fails
    if estimated < base_version or estimated > 200:
        return base_version
    return estimated


def get_platform_string() -> tuple[str, str]:
    """
    Detect current platform and return User-Agent platform string and Sec-Ch-Ua-Platform.
    Returns: (user_agent_platform, sec_ch_platform)
    """
    system = platform.system()
    machine = platform.machine()

    if system == "Darwin":
        # macOS
        return "Macintosh; Intel Mac OS X 10_15_7", '"macOS"'
    elif system == "Windows":
        # Windows
        arch = "Win64; x64" if machine in ["AMD64", "x86_64"] else "Win32"
        return f"Windows NT 10.0; {arch}", '"Windows"'
    elif system == "Linux":
        # Linux
        arch = "x86_64" if machine == "x86_64" else machine
        return f"X11; Linux {arch}", '"Linux"'
    else:
        # Fallback to macOS
        return "Macintosh; Intel Mac OS X 10_15_7", '"macOS"'


def get_browser_headers() -> dict:
    """Generate browser headers with current Chrome version and detected platform."""
    chrome_ver = get_chrome_version()
    platform_str, sec_ch_platform = get_platform_string()
    # Use major version only for brand version (modern format)
    brand_ver = "8"  # Not A;Brand version stays constant
    return {
        "User-Agent": f"Mozilla/5.0 ({platform_str}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver}.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Sec-Ch-Ua": f'"Google Chrome";v="{chrome_ver}", "Chromium";v="{chrome_ver}", "Not=A?Brand";v="{brand_ver}"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": sec_ch_platform,
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
    # Validate URL scheme
    parsed = urlparse(url)
    if parsed.scheme not in ['http', 'https']:
        raise ValueError(f"Invalid URL scheme: {parsed.scheme}. Only http and https are allowed.")

    session = get_session()
    max_size = 50 * 1024 * 1024  # 50MB limit
    try:
        response = session.get(url, headers=get_browser_headers(), timeout=30, stream=True)
        response.raise_for_status()

        # Check content length if provided
        content_length = response.headers.get('content-length')
        if content_length and int(content_length) > max_size:
            raise ValueError(f"Response too large: {int(content_length)} bytes (max {max_size} bytes)")

        # Read response with size limit
        content_bytes = b""
        for chunk in response.iter_content(chunk_size=8192):
            content_bytes += chunk
            if len(content_bytes) > max_size:
                raise ValueError(f"Response exceeded size limit of {max_size} bytes")

        response._content = content_bytes
    except requests.exceptions.HTTPError as e:
        raise ValueError(f"HTTP error fetching {url}: {e.response.status_code} {e.response.reason}")
    except requests.exceptions.ConnectionError as e:
        raise ValueError(f"Connection error fetching {url}: {str(e)}")
    except requests.exceptions.Timeout as e:
        raise ValueError(f"Timeout fetching {url}: Request took longer than 30 seconds")
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Error fetching {url}: {str(e)}")

    # Handle encoding edge cases
    if response.encoding is None or response.encoding == 'ISO-8859-1':
        # ISO-8859-1 is often a fallback; try to detect actual encoding
        response.encoding = response.apparent_encoding

    if raw:
        content = response.text
    else:
        try:
            h = HTML2Text()
            h.ignore_links = False
            h.ignore_images = True
            h.body_width = 0
            content = h.handle(response.text)
        except Exception as e:
            # Fallback to raw text if HTML parsing fails
            content = f"[HTML parsing failed: {str(e)}]\n\n{response.text}"

    # Apply pagination
    paginated = content[start_index : start_index + max_length]

    # Add continuation hint if truncated
    if len(content) > start_index + max_length:
        remaining = len(content) - (start_index + max_length)
        paginated += f"\n\n[Truncated. {remaining} chars remaining. Use start_index={start_index + max_length} to continue.]"

    return paginated


if __name__ == "__main__":
    mcp.run()
