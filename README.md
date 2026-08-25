<h1 align="center">
    SCRAPEMAXXER
    <br>
    <small>Scrapling-powered scraping toolkit for the modern web</small>
</h1>

<p align="center">
    <img alt="Python version" src="https://img.shields.io/badge/Python-3.14-blue">
    <img alt="Scrapling" src="https://img.shields.io/badge/Scrapling-0.4.15-red">
    <img alt="License" src="https://img.shields.io/badge/License-BSD--3--Clause-yellow">
</p>

<p align="center">
    <a href="#getting-started"><strong>Getting Started</strong></a>
    &middot;
    <a href="#cli-usage"><strong>CLI Usage</strong></a>
    &middot;
    <a href="#fetchers"><strong>Fetchers</strong></a>
    &middot;
    <a href="#configuration"><strong>Configuration</strong></a>
    &middot;
    <a href="#mcp-server"><strong>MCP Server</strong></a>
</p>

ScrapeMaxxer is a lightweight CLI wrapper around [Scrapling](https://scrapling.readthedocs.io/). One command takes you from a URL to saved, structured data — no scraping code required. Pick your fetcher (`http`, `dynamic`, or `stealthy`), point it at a page, and get clean JSON in `output/`.

It is designed to run identically on any machine: this macOS 12 dev box for lightweight HTTP jobs, and a full PC (macOS 13+ / Windows / Linux) for browser-based scraping with anti-bot bypass.

```bash
python main.py https://example.com -i 'links=a::attr(href)'
```

## Key Features

- 🚀 **Zero-code CLI**: Scrape any URL with CSS selectors and get JSON — `python main.py <url> -s 'h1::text'`.
- 🧩 **Multiple fetchers**: HTTP (`Fetcher`), Dynamic Playwright browser (`DynamicFetcher`), and stealth anti-bot (`StealthyFetcher`) — swapped with a single `.env` variable.
- 🎯 **Named selectors**: Extract several fields in one pass with repeatable `-i name=selector` flags.
- 🗂️ **Sane output**: Results land in `output/<domain>.json`, auto-organized per target.
- 🤖 **MCP server**: Expose Scrapling's tools to any AI agent via `scrapling-mcp` (already wired into `opencode.json`).
- 🔌 **Familiar API**: The scraper functions return Scrapling's `Response` objects, so you can drop into `resp.css(...)` / `resp.xpath(...)` anytime.

## Getting Started

Let's get you scraping in two commands.

### Installation

ScrapeMaxxer requires Python 3.10 or higher (developed on 3.14):

```bash
python -m venv .venv
source .venv/bin/activate                      # macOS: required — the activate script carries a curl_cffi fix
pip install -r requirements.txt
cp .env.example .env                           # then adjust if needed
```

If you are going to use the browser fetchers (`dynamic` / `stealthy`), also install the browsers:

```bash
scrapling install
```

> [!IMPORTANT]
> `scrapling install` only works on macOS 13+ / Windows / Linux. On this macOS 12 Intel dev machine it fails — see [Platform notes](#platform-notes).

### Basic Usage

```bash
python main.py https://quotes.toscrape.com -s 'h1::text'
```

Extract multiple named fields in one run:

```bash
python main.py https://quotes.toscrape.com \
  -s 'div.quote' \
  -i 'text=span.text::text' \
  -i 'author=small.author::text'
```

Write to a custom path instead of `output/`:

```bash
python main.py https://example.com -o /tmp/result.json
```

## CLI Usage

```
python main.py <url> [-s SELECTOR] [-i NAME=SELECTOR ...] [-o FILE]
```

| Flag | Default | Description |
|---|---|---|
| `url` | — | Target URL (positional, required) |
| `-s, --selector` | `title::text` | Main CSS selector (Scrapling pseudo-elements supported) |
| `-i, --item` | — | Extra named selector, repeatable: `-i name=css` |
| `-o, --output` | `output/<domain>.json` | Output file path |

The underlying scraper is also importable as a library:

```python
from scrapers.example import scrape_page

result = scrape_page("https://example.com", selector="h1::text", items={"links": "a::attr(href)"})
```

## Fetchers

| `FETCHER` | Class | Use for |
|---|---|---|
| `http` (default) | `Fetcher` | Plain HTTP/HTTPS, low–mid protection. Fast, no browser. |
| `dynamic` | `DynamicFetcher` | Pages that render content with JavaScript. Playwright Chromium. |
| `stealthy` | `StealthyFetcher` | High-protection sites (Cloudflare Turnstile/interstitial). Fingerprint spoofing. |

> [!NOTE]
> `dynamic` and `stealthy` launch a real browser, so they need `scrapling install` to have been run once on that machine.

## Configuration

All knobs live in `.env` (see `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `FETCHER` | `http` | `http` \| `dynamic` \| `stealthy` |
| `USER_AGENT` | (empty) | Custom User-Agent header |
| `REQUEST_TIMEOUT` | `30` | Request timeout in seconds |
| `REQUEST_DELAY` | `0` | Seconds to sleep after each request (politeness knob) |
| `OUTPUT_DIR` | `output` | Directory for scrape results |

## MCP Server

ScrapeMaxxer ships Scrapling's MCP server (`scrapling-mcp`), already registered in `opencode.json`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "scrapling": {
      "type": "local",
      "command": [".venv/bin/scrapling-mcp"],
      "enabled": true
    }
  }
}
```

This exposes tools like `make_request`, `bulk_get`, `fetch`, and `stealthy_fetch` to your agent, with session support. Restart opencode after changing MCP config so it reloads.

> [!NOTE]
> On macOS 12, the browser-based MCP tools (`fetch`, `stealthy_fetch`) will fail — use `make_request` / `bulk_get`. Full browser tools work on macOS 13+ / PC.

## Project Structure

```
main.py               # CLI entry point
config.py             # settings loader (.env)
scrapers/             # scraper modules (see scrapers/example.py)
  example.py          # core scrape_page() + fetcher selection
output/               # scrape results (gitignored, keeps only .gitkeep)
opencode.json         # MCP server registration
```

## Platform Notes

> [!CAUTION]
> **macOS 12 (Intel) dev box** — this machine has two hard limits:
> - Browser fetchers (`dynamic`/`stealthy`) **cannot** run: Playwright >= 1.62 dropped macOS 12 support. Use `FETCHER=http`.
> - `curl_cffi` needs `DYLD_INSERT_LIBRARIES=SystemConfiguration` — already baked into `.venv/bin/activate`, so always `source .venv/bin/activate` first.
>
> On **PC / macOS 13+ / Linux**, everything works: `scrapling install` succeeds and all fetchers run. See `AGENTS.md` for the full machine notes.

## Disclaimer

> [!CAUTION]
> This project is provided for educational and research purposes only. By using it, you agree to comply with local and international data scraping and privacy laws. Always respect the terms of service of target websites and their `robots.txt`.

## License

This work is licensed under the BSD-3-Clause License.
