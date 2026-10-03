from __future__ import annotations

import logging
import feedparser
from bs4 import BeautifulSoup
from app.models import Article
from app.sources.base import NewsSource, parse_datetime

log = logging.getLogger(__name__)


class DevURLsSource(NewsSource):
    name = "DevURLs"

    def __init__(self, client, feed_url: str):
        super().__init__(client)
        self.feed_url = feed_url

    async def fetch_articles(self) -> list[Article]:
        try:
            response = await self.get(self.feed_url)
            feed = feedparser.parse(response.content)
        except Exception as exc:
            log.warning("DevURLs feed unavailable (%s); using homepage", exc)
            response = await self.get("https://devurls.com/")
            feed = None
        articles = []
        if feed is not None and feed.entries:
            for entry in feed.entries[:100]:
                url = entry.get("link")
                title = entry.get("title")
                if not url or not title:
                    continue
                articles.append(Article(id=f"devurls:{entry.get('id', url)}", title=title.strip(), url=url, source=self.name, published_at=parse_datetime(entry.get("published")), author=entry.get("author"), tags=[tag.get("term", "") for tag in entry.get("tags", []) if isinstance(tag, dict)], description=entry.get("summary", entry.get("description", ""))))
        else:
            soup = BeautifulSoup(response.text, "html.parser")
            for index, link in enumerate(soup.select("a.article-link")[:100]):
                url = link.get("href")
                title = link.get_text(" ", strip=True)
                if url and title and not title.lower().startswith("open link"):
                    articles.append(Article(id=f"devurls:{index}:{url}", title=title, url=url, source=self.name))
        log.info("Retrieved %d DevURLs candidates", len(articles))
        return articles
