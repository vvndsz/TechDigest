from __future__ import annotations

from html import escape
from app.models import Article, Summary

MAX_TELEGRAM = 4096

def format_article(article: Article, summary: Summary) -> str:
    tags = " ".join(f"#{tag.replace(' ', '')}" for tag in summary.tags)
    points = "\n".join(f"• {escape(point)}" for point in summary.key_points) or "• Information unavailable."
    body = f"<b>━━━━━━━━━━━━━━━━━━━━</b>\n<b>{escape(' / '.join(summary.tags[:3]).upper() or 'TECHNOLOGY')}</b>\n<b>━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>Title:</b> {escape(summary.title)}\n\n<b>Source:</b> {escape(summary.source)}\n\n<b>Summary:</b>\n{escape(summary.summary)}\n\n<b>Key Points:</b>\n{points}\n\n<b>Why It Matters:</b>\n{escape(summary.why_it_matters)}\n\n<b>Technical Details:</b>\n{escape(summary.technical_details)}\n\n<b>Tags:</b> {escape(tags)}\n\n<b>Article:</b> {escape(article.url)}"
    if article.discussion_url:
        body += f"\n\n<b>Discussion:</b> {escape(article.discussion_url)}"
    if len(body) <= MAX_TELEGRAM:
        return body
    return body[: MAX_TELEGRAM - 80].rsplit("\n", 1)[0] + "\n\n<i>Message shortened to fit Telegram.</i>"
