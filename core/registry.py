"""Реестр игр: регистрация, выбор и смена активной игры."""
from __future__ import annotations

import logging
from typing import Callable, Optional

from .base import ChatEvent, CommandSpec, Game

log = logging.getLogger("games.registry")


class GameRegistry:
    """Хранит все доступные игры и следит за тем, какая из них активна."""

    def __init__(self) -> None:
        self._factories: dict[str, Callable[[], Game]] = {}
        self.active: Optional[Game] = None

    # --- регистрация ---------------------------------------------------------
    def register(self, game_cls: type[Game]) -> type[Game]:
        """Декоратор/метод регистрации класса игры."""
        if not game_cls.id:
            raise ValueError(f"Игра {game_cls.__name__} не имеет id")
        self._factories[game_cls.id] = game_cls
        log.info("Зарегистрирована игра: %s (%s)", game_cls.id, game_cls.name)
        return game_cls

    @property
    def available(self) -> list[str]:
        return list(self._factories.keys())

    def info(self, game_id: str) -> Optional[Game]:
        cls = self._factories.get(game_id)
        return cls() if cls else None

    # --- выбор / смена игры ---------------------------------------------------
    def select(self, game_id: str) -> Game:
        """Выбирает игру по id. Если уже активна другая — меняет её."""
        game_id = game_id.lower().strip()
        factory = self._factories.get(game_id)
        if factory is None:
            raise KeyError(game_id)

        if self.active is not None:
            old = self.active
            old.stop()
            log.info("Остановлена игра: %s", old.id)

        game = factory()
        game.start()
        self.active = game
        log.info("Активна игра: %s (%s)", game.id, game.name)
        return game

    def change_to(self, game_id: str) -> Game:
        """Явная смена игры (select с проверкой, что игра не та же)."""
        if self.active and self.active.id == game_id.lower().strip():
            raise ValueError("same")
        return self.select(game_id)

    def stop_active(self) -> None:
        if self.active is not None:
            self.active.stop()
            self.active = None

    # --- маршрутизация команд чата -------------------------------------------
    async def handle_chat(self, event: ChatEvent) -> Optional[str]:
        """Передаёт сообщение чата активной игре."""
        if self.active is None:
            return None
        return await self.active.on_command(event)

    def active_commands(self) -> list[CommandSpec]:
        return list(self.active.commands) if self.active else []
