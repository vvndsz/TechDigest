from __future__ import annotations

from app.deduplication import canonical_url
from app.models import Article


class RuntimeHistory:
    """Replaceable in-memory store; restart intentionally clears this state."""
    def __init__(self):
        self.processed: set[str] = set()
        self.delivered: set[str] = set()

    def unseen(self, articles: list[Article]) -> list[Article]:
        return [article for article in articles if canonical_url(article.url) not in self.processed and canonical_url(article.url) not in self.delivered]

    def mark_processed(self, articles: list[Article]) -> None:
        self.processed.update(canonical_url(article.url) for article in articles)

    def mark_delivered(self, article: Article) -> None:
        key = canonical_url(article.url)
        self.processed.add(key)
        self.delivered.add(key)
