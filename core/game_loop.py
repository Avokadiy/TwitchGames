"""Игровой цикл: равномерно вызывает tick() активной игры."""
from __future__ import annotations

import asyncio
import logging

from core.registry import GameRegistry

log = logging.getLogger("games.loop")


class GameLoop:
    def __init__(self, registry: GameRegistry, fps: float = 2.0) -> None:
        self.registry = registry
        self.interval = 1.0 / fps
        self._task: asyncio.Task | None = None

    async def _run(self) -> None:
        log.info("Игровой цикл запущен (%.1f тик/с)", 1 / self.interval)
        while True:
            game = self.registry.active
            if game is not None:
                try:
                    game.tick()
                except Exception:  # noqa: BLE001 — игра не должна ронять бота
                    log.exception("Ошибка в tick() игры %s", game.id)
            await asyncio.sleep(self.interval)

    def start(self) -> None:
        if self._task is None or self._task.done():
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.get_event_loop()
            self._task = loop.create_task(self._run())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
