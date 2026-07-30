"""
scrap_core — shared fetch / extract / filter logic.

Used by both scrap.py (CLI) and app.py (web UI) so there's exactly one
place that knows how to talk to scrapling.
"""
import re
from scrapling import Fetcher, StealthyFetcher


def fetch(url: str, stealth: bool = False, timeout: int = 30):
    """Fetch a URL, auto-falling back to StealthyFetcher if the plain
    fetcher gets blocked or errors out. Returns (response, mode)."""
    if stealth:
        return StealthyFetcher.fetch(url, timeout=timeout), "stealth"

    try:
        resp = Fetcher.get(url, timeout=timeout)
        if resp.status in (403, 406, 429, 503):
            resp = StealthyFetcher.fetch(url, timeout=timeout)
            return resp, "stealth (auto fallback)"
        return resp, "plain"
    except Exception:
        resp = StealthyFetcher.fetch(url, timeout=timeout)
        return resp, "stealth (auto fallback, plain fetch raised)"


def extract(resp, css=None, xpath=None, links=False, images=False, text=False):
    """Returns a list of dicts: {"value": str, "href": str|None}"""
    results = []

    if css:
        for v in resp.css(css).getall():
            results.append({"value": v.strip(), "href": None})

    elif xpath:
        for v in resp.xpath(xpath).getall():
            results.append({"value": str(v).strip(), "href": None})

    elif links:
        for a in resp.css("a"):
            href = a.attrib.get("href")
            label = a.get_all_text(strip=True) or ""
            if href:
                results.append({"value": label, "href": resp.urljoin(href)})

    elif images:
        for img in resp.css("img"):
            src = img.attrib.get("src") or img.attrib.get("data-src")
            alt = img.attrib.get("alt") or ""
            if src:
                results.append({"value": alt, "href": resp.urljoin(src)})

    elif text:
        raw = resp.get_all_text(strip=True)
        for line in str(raw).splitlines():
            line = line.strip()
            if line:
                results.append({"value": line, "href": None})

    else:
        title = resp.css("title::text").get() or ""
        desc = resp.css('meta[name="description"]::attr(content)').get() or ""
        if title:
            results.append({"value": title.strip(), "href": None})
        if desc:
            results.append({"value": desc.strip(), "href": None})

    return results


def apply_filters(results, contains=None, regex=None, exclude=None):
    if contains:
        needle = contains.lower()
        results = [r for r in results if needle in r["value"].lower()
                   or (r["href"] and needle in r["href"].lower())]
    if regex:
        pattern = re.compile(regex, re.IGNORECASE)
        results = [r for r in results if pattern.search(r["value"])
                   or (r["href"] and pattern.search(r["href"]))]
    if exclude:
        needle = exclude.lower()
        results = [r for r in results if needle not in r["value"].lower()
                   and not (r["href"] and needle in r["href"].lower())]
    return results


def dedupe(results):
    seen = set()
    out = []
    for r in results:
        key = (r["value"], r["href"])
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out


def run_one(url, mode_kwargs, filter_kwargs, limit=0, no_dedupe=False,
            stealth=False, timeout=30):
    """High-level helper: fetch + extract + filter + limit for one URL.
    Never raises — errors come back in the "error" field."""
    try:
        resp, mode = fetch(url, stealth=stealth, timeout=timeout)
    except Exception as e:
        return {"url": url, "status": None, "mode": None, "results": [], "error": str(e)}

    try:
        results = extract(resp, **mode_kwargs)
        results = apply_filters(results, **filter_kwargs)
        if not no_dedupe:
            results = dedupe(results)
        if limit:
            results = results[:limit]
        return {"url": url, "status": resp.status, "mode": mode, "results": results, "error": None}
    except Exception as e:
        return {"url": url, "status": resp.status, "mode": mode, "results": [], "error": str(e)}
