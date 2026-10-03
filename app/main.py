from __future__ import annotations

import asyncio
import logging
import httpx
from telegram.ext import Application
from app.bot.handlers import register_handlers
from app.config import Settings
from app.history import RuntimeHistory
from app.llm.openrouter import OpenRouterSummarizer
from app.pipeline import NewsPipeline
from app.scheduler import schedule_digest
from app.service import BotService
from app.sources.devurls import DevURLsSource
from app.sources.hackernews import HackerNewsSource
from app.sources.lobsters import LobstersSource

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger(__name__)


def build_service(settings: Settings):
    client = httpx.AsyncClient(timeout=settings.request_timeout, follow_redirects=True)
    sources = [HackerNewsSource(client), LobstersSource(client), DevURLsSource(client, settings.devurls_feed_url)]
    summarizer = OpenRouterSummarizer(client, settings.openrouter_api_key, settings.openrouter_model, settings.openrouter_app_url, settings.openrouter_app_name)
    history = RuntimeHistory()
    return BotService(settings, NewsPipeline(settings, sources, summarizer, client, history), history), client


def main() -> None:
    settings = Settings.from_env()
    if not settings.telegram_token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is required")
    if not settings.openrouter_api_key:
        raise SystemExit("OPENROUTER_API_KEY is required")
    service, client = build_service(settings)
    application = Application.builder().token(settings.telegram_token).build()
    register_handlers(application, service)
    schedule_digest(application, service)
    asyncio.set_event_loop(asyncio.new_event_loop())
    try:
        application.run_polling(close_loop=False)
    finally:
        asyncio.get_event_loop().run_until_complete(client.aclose())


if __name__ == "__main__":
    main()
