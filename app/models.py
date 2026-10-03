from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class Article:
    id: str
    title: str
    url: str
    source: str
    published_at: datetime | None = None
    author: str | None = None
    score: float = 0.0
    comments: int = 0
    tags: list[str] = field(default_factory=list)
    description: str = ""
    discussion_url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def timestamp(self) -> datetime:
        return self.published_at or datetime.now(timezone.utc)


@dataclass(slots=True)
class ArticleContent:
    text: str
    retrieved: bool
    reason: str = ""


@dataclass(slots=True)
class Summary:
    title: str
    source: str
    summary: str
    key_points: list[str]
    why_it_matters: str
    technical_details: str
    tags: list[str]
