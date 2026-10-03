from __future__ import annotations

import math
from datetime import datetime, timezone
from app.models import Article
from app.filtering import topic_matches


def rank_articles(articles: list[Article], topics: list[str], per_source: int = 2) -> dict[str, list[Article]]:
    now = datetime.now(timezone.utc)
    grouped: dict[str, list[Article]] = {}
    for article in articles:
        age_hours = max(0.0, (now - article.timestamp).total_seconds() / 3600)
        recency = max(0.0, 1.0 - age_hours / (24 * 7))
        engagement = min(1.0, math.log1p(max(0.0, article.score) + max(0, article.comments)) / math.log(1001))
        topic = 1.0 if topic_matches(article, topics) else 0.2
        technical = 1.0 if any(term in f"{article.title} {article.description}".lower() for term in ("api", "open source", "database", "security", "model", "compiler", "distributed", "infrastructure", "programming")) else 0.3
        article.metadata["rank_score"] = 0.40 * topic + 0.20 * technical + 0.20 * engagement + 0.20 * recency
        grouped.setdefault(article.source, []).append(article)
    return {source: sorted(items, key=lambda item: item.metadata["rank_score"], reverse=True)[:per_source] for source, items in grouped.items()}
