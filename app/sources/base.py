from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
import logging
import httpx
from app.models import Article

log = logging.getLogger(__name__)
USER_AGENT = "TechNewsDigest/1.0 (+https://github.com/example/tech-news-digest)"


class NewsSource(ABC):
    name: str

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    @abstractmethod
    async def fetch_articles(self) -> list[Article]:
        raise NotImplementedError

    async def get(self, url: str) -> httpx.Response:
        for attempt in range(3):
            try:
                response = await self.client.get(url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/json, text/html"})
                if response.status_code == 429 and attempt < 2:
                    continue
                response.raise_for_status()
                return response
            except (httpx.HTTPError, TimeoutError):
                if attempt == 2:
                    raise
        raise RuntimeError("unreachable")


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        from email.utils import parsedate_to_datetime
        result = parsedate_to_datetime(value)
        return result if result.tzinfo else result.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError, OverflowError):
        return None
