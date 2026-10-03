from __future__ import annotations

import asyncio
import logging
import httpx
from app.config import Settings
from app.deduplication import deduplicate
from app.extraction.article_extractor import ArticleExtractor
from app.filtering import filter_articles
from app.history import RuntimeHistory
from app.llm.base import Summarizer
from app.models import Article, Summary
from app.ranking import rank_articles
from app.sources.base import NewsSource

log = logging.getLogger(__name__)


class NewsPipeline:
    def __init__(self, settings: Settings, sources: list[NewsSource], summarizer: Summarizer, client: httpx.AsyncClient, history: RuntimeHistory):
        self.settings, self.sources, self.summarizer, self.history = settings, sources, summarizer, history
        self.extractor = ArticleExtractor(client, settings.max_article_chars)

    async def collect(self, topics: list[str] | None = None, per_source: int | None = None) -> list[tuple[Article, Summary]]:
        topics = topics or self.settings.topics
        enabled = [source for source in self.sources if self.settings.enabled_sources.get(source.name, True)]
        results = await asyncio.gather(*(self._fetch(source) for source in enabled))
        all_articles = deduplicate([article for batch in results for article in batch])
        fresh = self.history.unseen(all_articles)
        self.history.mark_processed(fresh)
        selected = rank_articles(filter_articles(fresh, topics), topics, per_source or self.settings.articles_per_source)
        chosen = [article for articles in selected.values() for article in articles]
        log.info("Selected %d articles after filtering and ranking", len(chosen))
        return await self._process(chosen, topics)

    async def _fetch(self, source: NewsSource) -> list[Article]:
        try:
            log.info("Fetching %s", source.name)
            return await source.fetch_articles()
        except Exception as exc:
            log.error("Source %s failed: %s", source.name, exc)
            return []

    async def _process(self, articles: list[Article], topics: list[str]) -> list[tuple[Article, Summary]]:
        async def one(article: Article):
            try:
                content = await self.extractor.extract(article)
                summary = await self.summarizer.summarize(article, content, topics)
                return article, summary
            except Exception as exc:
                log.error("Failed to process %s: %s", article.url, exc)
                return None
        values = await asyncio.gather(*(one(article) for article in articles))
        return [value for value in values if value is not None]
