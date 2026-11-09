"""Змейка — первая игра для тестирования команд чата.

Управление направлениями: !up !down !left !right (или ru-алиасы).
Также поддерживаются команды !start !stop !pause !resume !score !help.
"""
from __future__ import annotations

import random
from typing import Optional

from core.base import ChatEvent, CommandSpec, Game

UP, DOWN, LEFT, RIGHT = "up", "down", "left", "right"
OPPOSITE = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}
VECTORS = {UP: (0, -1), DOWN: (0, 1), LEFT: (-1, 0), RIGHT: (1, 0)}

WIDTH = 20
HEIGHT = 15


class SnakeGame(Game):
    id = "snake"
    name = "Змейка"
    description = "Классическая змейка: чат управляет направлением движения."
    commands = [
        CommandSpec("!start", "!start", "запустить / перезапустить игру"),
        CommandSpec("!stop", "!stop", "остановить игру"),
        CommandSpec("!pause", "!pause", "пауза"),
        CommandSpec("!resume", "!resume", "продолжить после паузы"),
        CommandSpec("!up", "!up | !down | !left | !right", "задать направление змейке"),
        CommandSpec("!score", "!score", "текущий счёт, рекорд и длина"),
        CommandSpec("!help", "!help", "список команд этой игры"),
    ]

    ALIASES = {
        "up": UP, "вверх": UP, "^": UP, "w": UP,
        "down": DOWN, "вниз": DOWN, "v": DOWN, "s": DOWN,
        "left": LEFT, "влево": LEFT, "a": LEFT,
        "right": RIGHT, "вправо": RIGHT, "d": RIGHT,
    }

    # рекорд живёт между партиями и между экземплярами (пока игра активна)
    high_score: int = 0

    def __init__(self) -> None:
        super().__init__()
        self.paused = True          # ждёт !start
        self.reset()

    # --- жизненный цикл ------------------------------------------------------
    def reset(self) -> None:
        cx, cy = WIDTH // 2, HEIGHT // 2
        self.snake = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
        self.direction = RIGHT
        self.pending: list[str] = []
        self.score = 0
        self.paused = True          # ждем !start
        self.game_over = False
        self.food = self._spawn_food()

    def start(self) -> None:
        super().start()
        self.reset()
        self.paused = False

    # --- логика шага ----------------------------------------------------------
    def tick(self) -> None:
        if not self.running or self.paused or self.game_over:
            return

        if self.pending:
            self.direction = self.pending.pop(0)

        dx, dy = VECTORS[self.direction]
        head = self.snake[0]
        new_head = (head[0] + dx, head[1] + dy)

        # столкновение со стеной или собой
        if (
            not (0 <= new_head[0] < WIDTH and 0 <= new_head[1] < HEIGHT)
            or new_head in self.snake[:-1]
        ):
            self.game_over = True
            self.high_score = max(self.high_score, self.score)
            return

        self.snake.insert(0, new_head)
        if new_head == self.food:
            self.score += 1
            self.food = self._spawn_food()
        else:
            self.snake.pop()

    def _spawn_food(self) -> tuple[int, int]:
        free = [
            (x, y)
            for x in range(WIDTH)
            for y in range(HEIGHT)
            if (x, y) not in self.snake
        ]
        return random.choice(free) if free else (0, 0)

    # --- команды чата -----------------------------------------------------------
    async def on_command(self, event: ChatEvent) -> Optional[str]:
        words = event.words
        if not words:
            return None
        cmd = words[0].lstrip("!@").strip()

        if cmd in ("help", "помощь"):
            names = " ".join(c.name for c in self.commands)
            return f"{self.name}: {names}"

        if cmd in ("start", "старт", "new"):
            self.start()
            return "🐍 Змейка перезапущена! Управление: !up !down !left !right"

        if cmd == "stop":
            self.stop()
            return "⏹ Игра остановлена. !start — чтобы начать заново."

        if cmd == "pause":
            if self.game_over:
                return "Игра окончена — нажмите !start"
            self.paused = True
            return f"⏸ Пауза. Счёт: {self.score}"

        if cmd == "resume":
            if self.game_over:
                return "Игра окончена — !start для новой партии"
            self.paused = False
            return "▶ Поехали!"

        if cmd == "score":
            return (
                f"🏆 Счёт: {self.score} | Рекорд: {self.high_score} | "
                f"Длина: {len(self.snake)}"
            )

        if cmd in self.ALIASES:
            direction = self.ALIASES[cmd]
            if not self.running:
                return "Игра остановлена — жми !start"
            if self.game_over:
                return "💀 Игра окончена! Счёт: {}. Жми !start".format(self.score)
            if self.paused:
                return "Игра на паузе — !resume или !start"
            current = self.pending[-1] if self.pending else self.direction
            if direction == OPPOSITE[current]:
                return f"Нельзя развернуться на 180° 🙂"
            if direction != current:
                self.pending.append(direction)
            return None  # без флуда в чат

        return None

    # --- состояние для оверлея ----------------------------------------------------
    def get_state(self) -> dict:
        return {
            "game": self.id,
            "name": self.name,
            "width": WIDTH,
            "height": HEIGHT,
            "snake": self.snake,
            "food": self.food,
            "direction": self.direction,
            "score": self.score,
            "high_score": self.high_score,
            "paused": self.paused,
            "game_over": self.game_over,
            "running": self.running,
        }
