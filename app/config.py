from __future__ import annotations

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

DEFAULT_TOPICS = [
    "Artificial Intelligence", "Machine Learning", "LLMs", "Generative AI",
    "AI agents", "Software engineering", "Programming", "Developer tools",
    "Open source", "Cybersecurity", "Startups", "Cloud computing", "DevOps",
    "Infrastructure", "Databases", "Distributed systems", "Web development",
    "Backend engineering", "Computer science", "Robotics", "Data engineering",
    "Developer productivity",
]


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class Settings:
    telegram_token: str
    openrouter_api_key: str
    openrouter_model: str = "qwen/qwen3.8-27b:free"
    openrouter_app_url: str = "http://localhost"
    openrouter_app_name: str = "Tech News Digest"
    timezone: str = "UTC"
    digest_times: tuple[str, str] = ("09:00", "18:00")
    articles_per_source: int = 2
    request_timeout: float = 20.0
    max_article_chars: int = 30000
    enabled_sources: dict[str, bool] = field(default_factory=dict)
    topics: list[str] = field(default_factory=lambda: DEFAULT_TOPICS.copy())
    devurls_feed_url: str = "https://devurls.com/"
    admin_user_ids: set[int] = field(default_factory=set)

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        topic_text = os.getenv("TOPICS", ",".join(DEFAULT_TOPICS))
        admins = {int(value) for value in os.getenv("ADMIN_USER_IDS", "").split(",") if value.strip().isdigit()}
        times = (os.getenv("DIGEST_TIME_1", "09:00"), os.getenv("DIGEST_TIME_2", "18:00"))
        return cls(
            telegram_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
            openrouter_model=os.getenv("OPENROUTER_MODEL", cls.openrouter_model),
            openrouter_app_url=os.getenv("OPENROUTER_APP_URL", cls.openrouter_app_url),
            openrouter_app_name=os.getenv("OPENROUTER_APP_NAME", cls.openrouter_app_name),
            timezone=os.getenv("TIMEZONE", "UTC"), digest_times=times,
            articles_per_source=max(1, int(os.getenv("ARTICLES_PER_SOURCE", "2"))),
            request_timeout=float(os.getenv("REQUEST_TIMEOUT_SECONDS", "20")),
            max_article_chars=max(1000, int(os.getenv("MAX_ARTICLE_CHARS", "30000"))),
            enabled_sources={"Hacker News": _bool("ENABLE_HACKERNEWS", True), "Lobsters": _bool("ENABLE_LOBSTERS", True), "DevURLs": _bool("ENABLE_DEVURLS", True)},
            topics=[item.strip() for item in topic_text.split(",") if item.strip()],
            devurls_feed_url=os.getenv("DEVURLS_FEED_URL", "https://devurls.com/"), admin_user_ids=admins,
        )
