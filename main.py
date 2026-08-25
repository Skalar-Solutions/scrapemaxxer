import argparse
import json
import time
from pathlib import Path
from urllib.parse import urlparse

import config
from scrapers.example import scrape_page


def main():
    p = argparse.ArgumentParser(description="ScrapeMaxxer - Scrapling-based scraper")
    p.add_argument("url", help="Target URL")
    p.add_argument("-s", "--selector", default="title::text", help="Main CSS selector (default: title::text)")
    p.add_argument("-i", "--item", action="append", metavar="NAME=SELECTOR", help="Extra named selectors (repeatable)")
    p.add_argument("-o", "--output", help="Output file (default: output/<domain>.json)")
    args = p.parse_args()

    items = dict(x.split("=", 1) for x in args.item) if args.item else None
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    result = scrape_page(args.url, selector=args.selector, items=items)

    out = Path(args.output) if args.output else config.OUTPUT_DIR / f"{urlparse(args.url).netloc.replace(':','_')}.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False))

    if config.DELAY:
        time.sleep(config.DELAY)
    print(f"Saved {args.url} ({result['status']}) -> {out}")


if __name__ == "__main__":
    main()
