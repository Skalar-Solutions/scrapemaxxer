import argparse
import json
import time
from pathlib import Path
from urllib.parse import urlparse

import config
from scrapers.example import scrape_page

# Preset selector packs for SEO / GEO / AEO data extraction
PROFILES = {
    "seo": {
        "title": "title::text",
        "desc": "meta[name=description]::attr(content)",
        "headings": "h1,h2,h3",
        "canonical": "link[rel=canonical]::attr(href)",
        "jsonld": 'script[type="application/ld+json"]::text',
        "main": "main",
    },
    "geo": {
        "list": "ul li",
        "table": "table",
        "datetime": "time::attr(datetime)",
    },
    "aeo": {
        "first_p": "p:first-of-type",
        "dl": "dt::text,dd::text",
        "ol": "ol li",
    },
}
PROFILES["all"] = {k: v for prof in PROFILES.values() for k, v in prof.items()}


def save_output(path, result):
    # encoding is mandatory: without it write_text uses the OS locale (cp1252 on
    # Windows) and smart quotes/em dashes become mojibake for any UTF-8 reader
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description="ScrapeMaxxer - Scrapling-based scraper")
    p.add_argument("url", help="Target URL")
    p.add_argument("-s", "--selector", default="title::text", help="Main CSS selector (default: title::text)")
    p.add_argument("-i", "--item", action="append", metavar="NAME=SELECTOR", help="Extra named selectors (repeatable)")
    p.add_argument("--profile", choices=["seo", "geo", "aeo", "all"], help="Preset selector pack (merges with -i)")
    p.add_argument("-o", "--output", help="Output file (default: output/<domain>.json)")
    p.add_argument("--fetcher", choices=["http", "dynamic", "stealthy"], help="Fetcher for this run (overrides FETCHER)")
    p.add_argument("--user-agent", dest="user_agent", help="Custom User-Agent (overrides USER_AGENT)")
    p.add_argument("--timeout", type=int, help="Request timeout in seconds (overrides REQUEST_TIMEOUT)")
    p.add_argument("--delay", type=float, help="Sleep after request (overrides REQUEST_DELAY)")
    p.add_argument("--solve-cf", action="store_true", help="Solve Cloudflare challenge (stealthy only)")
    p.add_argument("--output-dir", dest="output_dir", help="Output dir (overrides OUTPUT_DIR)")
    args = p.parse_args()

    items = dict(x.split("=", 1) for x in args.item) if args.item else None
    if args.profile:
        merged = PROFILES["all"] if args.profile == "all" else PROFILES[args.profile]
        merged = dict(merged)
        merged.update(items or {})
        items = merged
    outdir = Path(args.output_dir) if args.output_dir else config.OUTPUT_DIR
    outdir.mkdir(parents=True, exist_ok=True)

    result = scrape_page(
        args.url,
        selector=args.selector,
        items=items,
        fetcher=args.fetcher,
        user_agent=args.user_agent,
        timeout=args.timeout,
        solve_cf=args.solve_cf,
    )

    out = Path(args.output) if args.output else outdir / f"{urlparse(args.url).netloc.replace(':','_')}.json"
    save_output(out, result)

    if args.delay is not None or config.DELAY:
        time.sleep(args.delay if args.delay is not None else config.DELAY)
    print(f"Saved {args.url} ({result['status']}) -> {out}")


if __name__ == "__main__":
    main()
