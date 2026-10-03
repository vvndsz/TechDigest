from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path

from app.bot.formatter import format_article
from app.config import Settings
from app.main import build_service

log = logging.getLogger(__name__)
STATE_FILE = Path(os.getenv("DIGEST_STATE_FILE", ".digest-history.json"))


def load_history(service) -> None:
    if not STATE_FILE.exists():
        return
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        service.history.processed.update(str(value) for value in data.get("processed", []))
        service.history.delivered.update(str(value) for value in data.get("delivered", []))
    except (OSError, ValueError, TypeError) as exc:
        log.warning("Could not load digest history: %s", exc)


def save_history(service) -> None:
    STATE_FILE.write_text(json.dumps({"processed": sorted(service.history.processed), "delivered": sorted(service.history.delivered)}, indent=2), encoding="utf-8")


async def run() -> None:
    settings = Settings.from_env()
    chat_ids = [value.strip() for value in os.getenv("TELEGRAM_CHAT_IDS", "").split(",") if value.strip()]
    if not settings.telegram_token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is required")
    if not settings.openrouter_api_key:
        raise SystemExit("OPENROUTER_API_KEY is required")
    if not chat_ids:
        raise SystemExit("TELEGRAM_CHAT_IDS is required for GitHub Actions")

    service, client = build_service(settings)
    load_history(service)
    try:
        results = await service.generate(settings.topics, settings.articles_per_source)
        telegram_url = f"https://api.telegram.org/bot{settings.telegram_token}/sendMessage"
        for article, summary in results:
            for chat_id in chat_ids:
                response = await client.post(telegram_url, json={"chat_id": chat_id, "text": format_article(article, summary), "parse_mode": "HTML", "disable_web_page_preview": True}, timeout=30)
                response.raise_for_status()
            service.history.mark_delivered(article)
            log.info("Delivered %s", article.title)
        save_history(service)
        log.info("Digest complete: %d article(s)", len(results))
    finally:
        await client.aclose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    asyncio.run(run())
