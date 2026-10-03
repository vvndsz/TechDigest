from __future__ import annotations

import logging
from app.models import Article
from app.sources.base import NewsSource

log = logging.getLogger(__name__)
API = "https://hacker-news.firebaseio.com/v0"


class HackerNewsSource(NewsSource):
    name = "Hacker News"

    async def fetch_articles(self) -> list[Article]:
        response = await self.get(f"{API}/newstories.json")
        story_ids = response.json()[:80]
        articles: list[Article] = []
        for story_id in story_ids:
            try:
                item = (await self.get(f"{API}/item/{story_id}.json")).json()
                if item.get("type") != "story" or not item.get("title") or not item.get("url"):
                    continue
                from datetime import datetime, timezone
                published = datetime.fromtimestamp(item.get("time", 0), tz=timezone.utc) if item.get("time") else None
                articles.append(Article(id=f"hn:{story_id}", title=item["title"].strip(), url=item["url"], source=self.name, published_at=published, author=item.get("by"), score=float(item.get("score", 0)), comments=int(item.get("descendants", 0)), discussion_url=f"https://news.ycombinator.com/item?id={story_id}", description=item.get("text", ""), metadata={"hn_id": story_id}))
            except Exception as exc:
                log.warning("Skipping malformed Hacker News item %s: %s", story_id, exc)
        log.info("Retrieved %d Hacker News candidates", len(articles))
        return articles
