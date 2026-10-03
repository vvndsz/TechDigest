from __future__ import annotations

import logging
from urllib.parse import urlsplit
import httpx
import trafilatura
from bs4 import BeautifulSoup
from app.models import Article, ArticleContent
from app.sources.base import USER_AGENT

log = logging.getLogger(__name__)


class ArticleExtractor:
    def __init__(self, client: httpx.AsyncClient, max_chars: int = 30000):
        self.client = client
        self.max_chars = max_chars

    async def extract(self, article: Article) -> ArticleContent:
        try:
            parts = urlsplit(article.url)
            if parts.scheme not in {"http", "https"} or not parts.netloc:
                raise ValueError("invalid article URL")
            response = await self.client.get(article.url, headers={"User-Agent": USER_AGENT}, follow_redirects=True, timeout=20)
            response.raise_for_status()
            if len(response.content) > 5_000_000:
                raise ValueError("article response is too large")
            text = trafilatura.extract(response.text, include_comments=False, include_tables=True, favor_precision=True) or ""
            if not text:
                soup = BeautifulSoup(response.text, "html.parser")
                for node in soup(["script", "style", "nav", "footer", "header", "form", "aside"]):
                    node.decompose()
                text = soup.get_text(" ", strip=True)
            text = " ".join(text.split())[: self.max_chars]
            if len(text) < 100:
                raise ValueError("no meaningful article text")
            return ArticleContent(text=text, retrieved=True)
        except Exception as exc:
            log.warning("Failed to retrieve article %s: %s", article.url, exc)
            fallback = " ".join(BeautifulSoup(article.description, "html.parser").get_text(" ", strip=True).split())
            return ArticleContent(text=fallback[: self.max_chars], retrieved=False, reason=str(exc))
