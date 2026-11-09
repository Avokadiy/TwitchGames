"""Глобальные команды чата: выбор игры, смена игры, помощь, статус."""
from __future__ import annotations

import logging
from typing import Optional

from core.base import ChatEvent
from core.registry import GameRegistry

log = logging.getLogger("games.global_commands")

PREFIXES = ("!", "?", ".", "-", "#")


def parse_command(text: str) -> Optional[tuple[str, list[str]]]:
    """'!game snake' -> ('game', ['snake']). Команды принимаются и без префикса."""
    text = text.strip()
    if not text:
        return None
    prefix = ""
    if text[0] in PREFIXES:
        prefix, text = text[0], text[1:]
    parts = text.split()
    if not parts:
        return None
    return parts[0].lower(), parts[1:] if len(parts) > 1 else []


class GlobalCommands:
    """Команды, доступные поверх любой игры.

    !games          — список всех игр
    !game <id>      — выбрать игру (или !play / !change)
    !status         — какая игра активна
    !commands       — команды активной игры
    !help           — общая справка
    """

    def __init__(self, registry: GameRegistry) -> None:
        self.registry = registry

    async def handle(self, event: ChatEvent) -> Optional[str]:
        parsed = parse_command(event.text)
        if parsed is None:
            return None
        cmd, args = parsed

        if cmd == "games":
            if not self.registry.available:
                return "Нет зарегистрированных игр 😢"
            lines = []
            for gid in self.registry.available:
                g = self.registry.info(gid)
                active = " ✅" if self.registry.active and self.registry.active.id == gid else ""
                lines.append(f"{gid} — {g.name}{active}")
            return "🎮 Доступные игры: " + " | ".join(lines) + " . Выбрать: !game <id>"

        if cmd in ("game", "play", "change", "игра"):
            if not args:
                cur = self.registry.active.id if self.registry.active else "нет"
                return f"Сейчас активна: {cur}. Список: !games. Выбор: !game <id>"
            target = args[0]
            try:
                game = self.registry.change_to(target)
            except KeyError:
                return f"Игры '{target}' нет. Список: !games"
            except ValueError:
                return f"Игра '{target}' уже активна 🙂"
            msg = f"🎮 Сменили игру на {game.name}! Команды: !commands"
            log.info("%s выбрал игру %s", event.user, game.id)
            return msg

        if cmd == "status":
            g = self.registry.active
            if g is None:
                return "Активной игры нет. Выберите: !game <id> (см. !games)"
            s = g.get_state()
            return f"🎯 Активна: {g.name} | {g.description} | состояние: score={s.get('score', '-')}"

        if cmd in ("commands", "команды"):
            specs = self.registry.active_commands()
            if not specs:
                return "Нет активной игры. Выберите: !game <id>"
            return "Команды: " + "; ".join(f"{c.usage} — {c.description}" for c in specs)

        if cmd == "help":
            return (
                "🤖 Я — бот игр для стрима! Глобальные команды: !games, !game <id>, "
                "!status, !commands, !help. Команды текущей игры: !commands"
            )

        return None
