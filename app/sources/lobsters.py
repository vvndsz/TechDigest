from __future__ import annotations

import logging
import feedparser
from app.models import Article
from app.sources.base import NewsSource, parse_datetime

log = logging.getLogger(__name__)


class LobstersSource(NewsSource):
    name = "Lobsters"

    async def fetch_articles(self) -> list[Article]:
        response = await self.get("https://lobste.rs/rss")
        feed = feedparser.parse(response.content)
        articles = []
        for entry in feed.entries[:80]:
            url = entry.get("link")
            title = entry.get("title")
            if not url or not title:
                continue
            tags = [tag.get("term", "") for tag in entry.get("tags", []) if isinstance(tag, dict)]
            discussion_url = entry.get("comments") or entry.get("comment")
            articles.append(Article(id=f"lobsters:{entry.get('id', url)}", title=title.strip(), url=url, source=self.name, published_at=parse_datetime(entry.get("published")), author=entry.get("author"), score=float(entry.get("score", 0) or 0), comments=0, tags=tags, description=entry.get("summary", ""), discussion_url=discussion_url))
        log.info("Retrieved %d Lobsters candidates", len(articles))
        return articles
