import json
import re

import config
from scrapling.fetchers import Fetcher


def get_fetcher(name=None):
    """Return the fetcher class based on config.FETCHER (http|dynamic|stealthy)."""
    name = name or config.FETCHER
    if name == "stealthy":
        from scrapling.fetchers import StealthyFetcher

        return StealthyFetcher
    if name == "dynamic":
        from scrapling.fetchers import DynamicFetcher

        return DynamicFetcher
    return Fetcher


def extract(resp, sel):
    """Extract values for a CSS selector.

    `::text`/`::attr()` pseudo-selectors return raw matches (unchanged).
    Plain element selectors return the full descendant text via get_all_text(),
    so container elements like `<main>` and `<table>` aren't empty.
    """
    if "::" in sel:
        return resp.css(sel).getall()
    return [e.get_all_text() for e in resp.css(sel)]


def _walk(obj, fn):
    if isinstance(obj, dict):
        fn(obj)
        for v in obj.values():
            _walk(v, fn)
    elif isinstance(obj, list):
        for v in obj:
            _walk(v, fn)


def _schema_types(blocks):
    """Collect every @type found in the raw json-ld blocks."""
    types = set()

    def visit(node):
        t = node.get("@type")
        if isinstance(t, list):
            types.update(t)
        elif isinstance(t, str):
            types.add(t)

    for raw in blocks:
        try:
            data = json.loads(raw)
        except (ValueError, TypeError):
            continue
        _walk(data, visit)
    return sorted(types)


def _is_type(node, wanted):
    t = node.get("@type")
    if isinstance(t, list):
        return any(str(x).lower() == wanted for x in t)
    return str(t or "").lower() == wanted


def _faq_answers(blocks):
    """Extract acceptedAnswer text from FAQPage json-ld blocks."""
    answers = []

    def visit(node):
        if not _is_type(node, "faqpage"):
            return
        main_entity = node.get("mainEntity", [])
        if isinstance(main_entity, dict):
            main_entity = [main_entity]
        for q in main_entity:
            ans = q.get("acceptedAnswer")
            if isinstance(ans, list):
                for a in ans:
                    if a.get("text"):
                        answers.append(re.sub(r"<[^>]+>", "", a["text"]))
            elif isinstance(ans, dict) and ans.get("text"):
                answers.append(re.sub(r"<[^>]+>", "", ans["text"]))

    for raw in blocks:
        try:
            data = json.loads(raw)
        except (ValueError, TypeError):
            continue
        _walk(data, visit)
    return answers


def scrape_page(url, selector="title::text", items=None, fetcher=None, user_agent=None, timeout=None, solve_cf=False):
    """Fetch a URL and extract text/attr values matching `selector`.

    `items` is a list of CSS selectors to extract alongside the main selector.
    `fetcher`/`user_agent`/`timeout` override the project-level config for this call.
    `solve_cf` makes stealthy fetchers solve Cloudflare Turnstile/interstitial challenges.
    Returns a dict with status, url, and extracted data.
    """
    headers = {"User-Agent": user_agent or config.USER_AGENT or "scrapemaxxer/0.1"}
    cls = get_fetcher(fetcher)
    # http Fetcher uses .get(); browser fetchers use .fetch() on an instance
    if cls is not Fetcher and getattr(cls, "get", None) is None:
        resp = cls().fetch(url, timeout=timeout or config.TIMEOUT, headers=headers, solve_cloudflare=solve_cf)
    else:
        resp = cls.get(url, timeout=timeout or config.TIMEOUT, headers=headers)
    if resp.status >= 400:
        raise RuntimeError(f"Request failed: HTTP {resp.status}")

    data = {selector: extract(resp, selector)}
    for label, sel in (items or {}).items():
        data[label] = extract(resp, sel)
    data = {k: [v for v in vals if str(v).strip()] for k, vals in data.items()}

    if "jsonld" in data:
        data["schema_types"] = _schema_types(data["jsonld"])
        if "answer" not in data:
            data["answer"] = _faq_answers(data["jsonld"])

    return {"url": url, "status": resp.status, "data": data}
