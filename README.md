# MCP Browser Fetch

A Model Context Protocol (MCP) server for browser-like web fetching that bypasses bot detection.

## Features

- **Auto-updating Chrome User-Agent**: Calculates current Chrome version based on release schedule
- **Full browser headers**: Includes Accept, Accept-Language, Sec-Fetch-*, and other headers real browsers send
- **Brotli decompression**: Automatically handles Brotli-compressed responses
- **Session management**: Uses requests.Session() for proper cookie handling

## Why?

The default `mcp-server-fetch` identifies itself as a bot in the User-Agent, causing many sites to block it with 403 Forbidden errors. This implementation mimics a real Chrome browser to avoid detection.

## Installation

```bash
# Clone the repository
git clone git@github.com:kevin-hi/fetch-mcp.git
cd fetch-mcp

# Create virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .

# For development (includes test dependencies)
pip install -e ".[dev]"
```

## Configuration

### Claude Code

Add to `~/.claude/.mcp.json`:

```json
{
  "mcpServers": {
    "fetch": {
      "command": "/path/to/fetch-mcp/.venv/bin/python",
      "args": ["/path/to/fetch-mcp/server.py"]
    }
  }
}
```

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or equivalent:

```json
{
  "mcpServers": {
    "fetch": {
      "command": "/path/to/fetch-mcp/.venv/bin/python",
      "args": ["/path/to/fetch-mcp/server.py"]
    }
  }
}
```

### Ensuring Claude Uses This Tool

To ensure Claude always uses `mcp__fetch__fetch` instead of built-in WebFetch:

1. **Install the skill** (teaches Claude to prefer this tool):
   ```bash
   mkdir -p ~/.claude/skills/web-fetch
   # Copy SKILL.md from this repo to ~/.claude/skills/web-fetch/
   ```

2. **Optional: Add warning hook** to catch WebFetch attempts:
   ```bash
   mkdir -p ~/.claude/hooks
   # Copy hooks.json from this repo to ~/.claude/hooks/
   ```

3. **Restart Claude** to load the new configuration

## Usage

The tool exposes a single `fetch` function that works like the standard MCP fetch but with browser-like headers:

```python
fetch(
    url: str,              # URL to fetch
    max_length: int = 5000,  # Max characters to return
    start_index: int = 0,   # Start index for pagination
    raw: bool = False       # Return raw HTML instead of markdown
)
```

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=server --cov-report=html

# Run specific test class
pytest test_server.py::TestChromeVersion

# Run specific test
pytest test_server.py::TestChromeVersion::test_version_calculation_current_date
```

### Test Coverage

The test suite covers:
- Chrome version calculation and bounds
- Platform detection (macOS, Windows, Linux, ARM, Intel)
- Session management and reuse
- Browser header generation
- URL validation (http/https only, rejects file://, javascript:, data:, ftp:)
- Response size limits (50MB cap)
- Error handling (404, connection errors, timeouts)
- HTML parsing and fallback
- Pagination functionality

### Manual Testing

Successfully tested against:
- CamelCamelCamel (was 403 blocked with default MCP)
- Reddit
- Wired.com
- Most other sites that block obvious bots

## Technical Details

### User-Agent Calculation

Chrome releases approximately every 4 weeks. Starting from Chrome 122 (Feb 2024), the code calculates the current version:

```python
base_version = 122
base_date = date(2024, 2, 1)
days_since = (date.today() - base_date).days
versions_since = days_since // 28
current_version = base_version + versions_since
```

### Browser Headers

Includes all headers that Chrome sends:
- `User-Agent`: Auto-calculated Chrome version
- `Accept`: Full content type preferences
- `Accept-Language`, `Accept-Encoding`
- `Sec-Fetch-Dest`, `Sec-Fetch-Mode`, `Sec-Fetch-Site`, `Sec-Fetch-User`
- `Sec-Ch-Ua`, `Sec-Ch-Ua-Mobile`, `Sec-Ch-Ua-Platform`
- `Upgrade-Insecure-Requests`, `Cache-Control`

## License

MIT
