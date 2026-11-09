"""Точка входа: собирает реестр игр, игровой цикл, чат и HTTP-оверлей.

Запуск:  python main.py
Без Twitch-токенов поднимается оверлей + консольный эмулятор чата.
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.base import ChatEvent                       # noqa: E402
from core.game_loop import GameLoop                   # noqa: E402
from core.global_commands import GlobalCommands       # noqa: E402
from core.registry import GameRegistry                # noqa: E402
from games.snake import SnakeGame                     # noqa: E402
from twitch_client import TwitchClient, console_chat_emulator, load_env  # noqa: E402
from web.overlay_server import OverlayServer          # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("main")


def build_registry() -> GameRegistry:
    registry = GameRegistry()
    registry.register(SnakeGame)
    # Новые игры добавляйте сюда, например: registry.register(TetrisGame)
    return registry


class StreamGamesBot:
    def __init__(self) -> None:
        self.registry = build_registry()
        self.globals = GlobalCommands(self.registry)
        self.loop_game = GameLoop(self.registry, fps=2.0)
        self.twitch = TwitchClient(self.on_message)
        port = int(os.environ.get("PORT", "8080"))
        self.overlay = OverlayServer(self.registry, port=port)

    async def on_message(self, event: ChatEvent) -> str | None:
        """Сначала глобальные команды (выбор/смена игры), затем — командам игры."""
        reply = await self.globals.handle(event)
        if reply is not None:
            return reply
        return await self.registry.handle_chat(event)

    async def run(self) -> None:
        load_env()
        await self.overlay.start()
        self.loop_game.start()

        # Стартуем первую доступную игру по умолчанию, чтобы чат сразу жил
        default_game = os.environ.get("DEFAULT_GAME", "snake")
        if default_game in self.registry.available:
            self.registry.select(default_game)

        connected = await self.twitch.connect()
        try:
            if connected:
                # twitchio держит соединение сам — просто ждём
                while True:
                    await asyncio.sleep(3600)
            else:
                await console_chat_emulator(self.on_message)
        finally:
            await self.loop_game.stop()
            await self.twitch.close()
            await self.overlay.stop()


def main() -> None:
    bot = StreamGamesBot()
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        log.info("Остановка по Ctrl+C")


if __name__ == "__main__":
    main()
