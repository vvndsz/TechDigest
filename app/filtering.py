from __future__ import annotations

import re
from app.models import Article


def topic_matches(article: Article, topics: list[str]) -> bool:
    haystack = f"{article.title} {article.description} {' '.join(article.tags)}".lower()
    return any(re.search(r"\b" + re.escape(topic.lower()) + r"\b", haystack) for topic in topics)


def filter_articles(articles: list[Article], topics: list[str]) -> list[Article]:
    return [article for article in articles if topic_matches(article, topics) or _exceptional(article)]


def _exceptional(article: Article) -> bool:
    text = f"{article.title} {article.description}".lower()
    return any(term in text for term in ("release", "research", "vulnerability", "database", "compiler", "linux", "github"))
