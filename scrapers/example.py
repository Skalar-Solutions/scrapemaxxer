import config


def get_fetcher():
    """Return the fetcher class based on config.FETCHER (http|dynamic|stealthy)."""
    if config.FETCHER == "stealthy":
        from scrapling.fetchers import StealthyFetcher

        return StealthyFetcher
    if config.FETCHER == "dynamic":
        from scrapling.fetchers import DynamicFetcher

        return DynamicFetcher
    from scrapling.fetchers import Fetcher

    return Fetcher


def scrape_page(url, selector="title::text", items=None):
    """Fetch a URL and extract text/attr values matching `selector`.

    `items` is a list of CSS selectors to extract alongside the main selector.
    Returns a dict with status, url, and extracted data.
    """
    headers = {"User-Agent": config.USER_AGENT or "scrapemaxxer/0.1"}
    resp = get_fetcher().get(url, timeout=config.TIMEOUT, headers=headers)
    if resp.status >= 400:
        raise RuntimeError(f"Request failed: HTTP {resp.status}")

    data = {selector: resp.css(selector).getall()}
    for label, sel in (items or {}).items():
        data[label] = resp.css(sel).getall()

    return {"url": url, "status": resp.status, "data": data}
