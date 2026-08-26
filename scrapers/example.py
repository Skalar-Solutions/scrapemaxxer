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

    data = {selector: resp.css(selector).getall()}
    for label, sel in (items or {}).items():
        data[label] = resp.css(sel).getall()
    data = {k: [v for v in vals if str(v).strip()] for k, vals in data.items()}

    return {"url": url, "status": resp.status, "data": data}
