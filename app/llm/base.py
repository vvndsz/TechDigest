from __future__ import annotations

from abc import ABC, abstractmethod
from app.models import Article, ArticleContent, Summary


class Summarizer(ABC):
    @abstractmethod
    async def summarize(self, article: Article, content: ArticleContent, topics: list[str]) -> Summary:
        raise NotImplementedError
