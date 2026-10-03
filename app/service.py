from __future__ import annotations

import httpx
from app.config import Settings
from app.history import RuntimeHistory
from app.pipeline import NewsPipeline


class BotService:
    def __init__(self, settings: Settings, pipeline: NewsPipeline, history: RuntimeHistory):
        self.settings, self.pipeline, self.history = settings, pipeline, history
        self.subscribers: set[int] = set()

    async def generate(self, topics: list[str], per_source: int):
        return await self.pipeline.collect(topics, per_source)

    def add_subscriber(self, user_id: int) -> None:
        self.subscribers.add(user_id)
