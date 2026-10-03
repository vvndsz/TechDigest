from __future__ import annotations

import logging
from zoneinfo import ZoneInfo
from app.bot.formatter import format_article

log = logging.getLogger(__name__)


def schedule_digest(application, service) -> None:
    timezone = ZoneInfo(service.settings.timezone)
    for value in service.settings.digest_times:
        hour, minute = (int(part) for part in value.split(":", 1))
        application.job_queue.run_daily(send_scheduled_digest, time=__import__("datetime").time(hour, minute, tzinfo=timezone), name=f"digest-{value}", data=service)


async def send_scheduled_digest(context):
    service = context.job.data
    results = await service.generate(service.settings.topics, service.settings.articles_per_source)
    for article, summary in results:
        for user_id in service.subscribers:
            try:
                await context.bot.send_message(chat_id=user_id, text=format_article(article, summary), parse_mode="HTML", disable_web_page_preview=True)
                service.history.mark_delivered(article)
            except Exception as exc:
                log.error("Telegram delivery failed: %s", exc)
