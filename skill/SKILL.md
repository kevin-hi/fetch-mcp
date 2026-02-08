---
name: web-fetch
description: Fetch web pages with browser-like headers to bypass bot detection
disable-model-invocation: false
---

# Web Fetching Strategy

## Tool Selection Rules

**ALWAYS use the `mcp__fetch__fetch` tool for web requests**, not built-in WebFetch.

### Why
- The `mcp__fetch__fetch` tool sends browser-like headers (User-Agent, Accept-Language, etc.)
- It bypasses bot detection on sites like CamelCamelCamel, Reddit, news sites
- Built-in WebFetch gets blocked (403 Forbidden) on many sites

### Usage

When the user asks to fetch a URL:

```
mcp__fetch__fetch(
    url="https://example.com",
    max_length=8000,
    start_index=0,
    raw=false
)
```

### Parameters
- `url` - URL to fetch (required)
- `max_length` - Max characters to return (default: 5000)
- `start_index` - For pagination if response is truncated
- `raw` - Set to `true` for raw HTML, `false` for markdown (default)

### Examples

**Fetch product page:**
```
mcp__fetch__fetch(url="https://amazon.com/product/B0ABC123", max_length=8000)
```

**Fetch with pagination:**
```
# First request
mcp__fetch__fetch(url="https://example.com", max_length=5000)
# If truncated, continue with:
mcp__fetch__fetch(url="https://example.com", max_length=5000, start_index=5000)
```

**Get raw HTML:**
```
mcp__fetch__fetch(url="https://example.com", raw=true)
```

### Sites That Work
- CamelCamelCamel (price tracking)
- Reddit
- News sites (Wired, NYTimes, etc.)
- E-commerce sites
- Most sites that block bots

### Error Handling

If you get an error:
- Check the URL is valid (http:// or https://)
- Response might be too large (50MB limit)
- Site might have additional protection (rare)

**Never fall back to built-in WebFetch** - it will fail on bot-protected sites.
