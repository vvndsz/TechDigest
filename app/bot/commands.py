from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes
from app.bot.formatter import format_article


class CommandHandlers:
    def __init__(self, service):
        self.service = service

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.service.add_subscriber(update.effective_user.id)
        await update.message.reply_text("Tech News Digest finds and summarizes relevant engineering news.\n\n/news or /digest: generate a digest\n/latest: newest stories\n/ai: AI and ML stories\n/security: cybersecurity stories\n/programming: programming stories\n/sources: enabled sources\n/settings: view settings\n\nRuntime history resets when the bot restarts.")

    async def digest(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self._send(update, self.service.settings.topics, self.service.settings.articles_per_source)

    async def latest(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self._send(update, self.service.settings.topics, 1)

    async def ai(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self._send(update, ["Artificial Intelligence", "Machine Learning", "LLMs", "Generative AI", "AI agents"], 2)

    async def security(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self._send(update, ["Cybersecurity"], 2)

    async def programming(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self._send(update, ["Programming", "Software engineering", "Developer tools", "Backend engineering"], 2)

    async def sources(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        enabled = [name for name, value in self.service.settings.enabled_sources.items() if value]
        await update.message.reply_text("Enabled sources:\n" + "\n".join(enabled))

    async def settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        settings = self.service.settings
        if context.args:
            if settings.admin_user_ids and update.effective_user.id not in settings.admin_user_ids:
                await update.message.reply_text("Only configured administrators can change shared settings.")
                return
            values = {}
            for item in context.args:
                if "=" in item:
                    key, value = item.split("=", 1)
                    values[key.lower()] = value
            if "topics" in values:
                topics = [topic.strip() for topic in values["topics"].split("|") if topic.strip()]
                if topics:
                    settings.topics = topics
            if "articles" in values:
                try:
                    settings.articles_per_source = max(1, min(10, int(values["articles"])))
                except ValueError:
                    await update.message.reply_text("articles must be an integer from 1 to 10.")
                    return
            if "sources" in values:
                selected = {name.strip().lower() for name in values["sources"].split(",")}
                for name in settings.enabled_sources:
                    settings.enabled_sources[name] = name.lower() in selected
            if "schedule" in values:
                times = tuple(values["schedule"].split(","))
                if len(times) != 2 or any(len(time.split(":")) != 2 for time in times):
                    await update.message.reply_text("schedule must look like 09:00,18:00.")
                    return
                settings.digest_times = (times[0], times[1])
            await update.message.reply_text("Settings updated in memory. Schedule changes take effect after restart; other changes apply now.")
            return
        await update.message.reply_text(f"Topics: {', '.join(settings.topics)}\nArticles per source: {settings.articles_per_source}\nSchedule: {settings.digest_times[0]}, {settings.digest_times[1]} ({settings.timezone})\nSources: {', '.join(name for name, value in settings.enabled_sources.items() if value)}\n\nPreferences are environment-configured in this version.")

    async def _send(self, update, topics, per_source):
        results = await self.service.generate(topics, per_source)
        if not results:
            await update.message.reply_text("No new matching articles were found. Runtime history prevents duplicate delivery.")
            return
        for article, summary in results:
            await update.message.reply_text(format_article(article, summary), parse_mode="HTML", disable_web_page_preview=True)
            self.service.history.mark_delivered(article)
