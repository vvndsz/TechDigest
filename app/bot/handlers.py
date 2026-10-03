from telegram.ext import CommandHandler
from app.bot.commands import CommandHandlers


def register_handlers(application, service):
    handlers = CommandHandlers(service)
    for name in ("start", "news", "digest"):
        application.add_handler(CommandHandler(name, handlers.start if name == "start" else handlers.digest))
    for name, callback in {"latest": handlers.latest, "ai": handlers.ai, "security": handlers.security, "programming": handlers.programming, "settings": handlers.settings, "sources": handlers.sources}.items():
        application.add_handler(CommandHandler(name, callback))
