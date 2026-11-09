"""Базовые сущности игрового движка: событие чата и абстрактная игра."""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ChatEvent:
    """Сообщение из чата, приведённое к удобному виду."""

    user: str
    text: str
    is_mod: bool = False
    is_sub: bool = False
    ts: float = field(default_factory=time.time)

    @property
    def words(self) -> list[str]:
        return self.text.lower().split()


@dataclass
class CommandSpec:
    """Описание команды чата для игры (используется в !help и на оверлее)."""

    name: str
    usage: str
    description: str


class Game(ABC):
    """Интерфейс игры для стрима.

    Любая игра обязана уметь:
      - стартовать/останавливаться (start/stop);
      - обрабатывать команды чата (on_command);
      - отдавать состояние для визуализации (get_state).
    """

    id: str = ""
    name: str = ""
    description: str = ""
    commands: list[CommandSpec] = []

    def __init__(self) -> None:
        self.running = False
        self.started_at: Optional[float] = None

    # --- жизненный цикл -----------------------------------------------------
    def start(self) -> None:
        self.running = True
        self.started_at = time.time()

    def stop(self) -> None:
        self.running = False

    @abstractmethod
    async def on_command(self, event: ChatEvent) -> Optional[str]:
        """Обработать команду чата. Возвращает строку-ответ в чат или None."""

    @abstractmethod
    def get_state(self) -> dict:
        """Сериализуемое состояние игры для HTTP-оверлея."""

    def tick(self) -> None:
        """Шаг игровой логики (вызывается игровым циклом, если переопределён)."""
