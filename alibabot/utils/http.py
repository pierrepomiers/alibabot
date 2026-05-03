import asyncio
import httpx
from typing import Optional


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}


async def fetch(
    client: httpx.AsyncClient,
    url: str,
    *,
    rate_limit_seconds: float = 1.0,
    max_retries: int = 3,
    expect_json: bool = False,
) -> httpx.Response:
    """Fetch avec retries exponentiels + backoff agressif sur 429 + rate-limit poli après succès."""
    last_exc: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            response = await client.get(url, headers=DEFAULT_HEADERS, timeout=30.0, follow_redirects=True)
            if response.status_code == 429:
                wait = (attempt + 1) * 5
                await asyncio.sleep(wait)
                continue
            response.raise_for_status()
            await asyncio.sleep(rate_limit_seconds)
            return response
        except (httpx.HTTPError, httpx.TimeoutException) as e:
            last_exc = e
            await asyncio.sleep(2 ** attempt)
    raise RuntimeError(f"Failed after {max_retries} retries: {url}") from last_exc
