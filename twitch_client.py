"""Подключение к чату Twitch.

Если twitchio не установлен или нет токенов — работает "сухой режим":
бот поднимает оверлей и консольный эмулятор чата, чтобы всё можно было
протестировать локально (строка вводится как: user: !game snake).
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Awaitable, Callable, Optional

from core.base import ChatEvent

log = logging.getLogger("games.twitch")

MessageHandler = Callable[[ChatEvent], Awaitable[Optional[str]]]


def load_env(path: str = ".env") -> None:
    """Мини-загрузчик .env без зависимостей."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


class TwitchClient:
    def __init__(self, handler: MessageHandler) -> None:
        self.handler = handler
        self._bot = None

    # --- Twitch -----------------------------------------------------------
    async def connect(self) -> bool:
        load_env()
        client_id = os.environ.get("TWITCH_CLIENT_ID")
        token = os.environ.get("TWITCH_OAUTH_TOKEN")
        channel = os.environ.get("TWITCH_CHANNEL")
        if not (client_id and token and channel):
            log.warning("Нет Twitch-креденшелов (.env) — запускаюсь в сухом режиме.")
            return False
        try:
            import twitchio
        except ImportError:
            log.warning("twitchio не установлен (pip install -r requirements.txt) — сухой режим.")
            return False

        outer = self

        class Bot(twitchio.Client):
            async def event_message(self, message):
                if message.echo or not message.channel:
                    return
                author = message.author
                event = ChatEvent(
                    user=getattr(author, "display_name", None) or getattr(author, "name", "anon"),
                    text=message.content,
                    is_mod=bool(getattr(author, "is_mod", False)),
                    is_sub=bool(getattr(author, "is_sub", False)),
                )
                reply = await outer.handler(event)
                if reply:
                    await message.channel.send(reply)

        nick = os.environ.get("BOT_NICKNAME")
        self._bot = Bot(
            token_or_client_id=token,
            client_id=client_id,
            initial_channels=[channel],
            nick=nick,
        )
        await self._bot.connect()
        log.info("Подключено к чату канала: %s", channel)
        return True

    async def close(self) -> None:
        if self._bot is not None:
            await self._bot.close()
            self._bot = None


# --- Эмулятор чата для тестирования без Twitch -------------------------
async def console_chat_emulator(handler: MessageHandler) -> None:
    print("\n=== Эмулятор чата (Twitch не подключён) ===")
    print('Формат: <ник>: <сообщение>, например  viewer1: !game snake')
    print('Команда "exit" — остановить бота.\n')
    loop = asyncio.get_event_loop()
    while True:
        try:
            line = await loop.run_in_executor(None, input, "")
        except EOFError:
            break
        if line.strip().lower() == "exit":
            break
        user, _, text = line.partition(":")
        if not text:  # без ника — считаем сообщением
            user, text = "console", line
        event = ChatEvent(user=user.strip() or "console", text=text.strip())
        reply = await handler(event)
        if reply:
            print(f"[bot -> {event.user}] {reply}")
