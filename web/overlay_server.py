"""HTTP-сервер для OBS Browser Overlay.

Эндпоинты:
  GET /overlay        — HTML-страница змейки/игры
  GET /api/state      — состояние активной игры (JSON)
  GET /api/games      — список игр и активная (JSON)
"""
from __future__ import annotations

import json
import logging

from aiohttp import web

from core.registry import GameRegistry

log = logging.getLogger("games.web")

OVERLAY_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<style>
  html, body { margin: 0; background: transparent; overflow: hidden;
               font-family: 'Segoe UI', Arial, sans-serif; }
  #wrap { display: flex; flex-direction: column; align-items: center; }
  #hud { color: #fff; text-shadow: 0 0 6px #000; font-size: 22px; padding: 6px; }
  canvas { background: rgba(10, 15, 30, .75); border-radius: 12px;
           box-shadow: 0 0 24px rgba(0,0,0,.5); }
</style>
</head>
<body>
<div id="wrap">
  <div id="hud">Загрузка...</div>
  <canvas id="cv" width="600" height="450"></canvas>
</div>
<script>
const cv = document.getElementById('cv');
const ctx = cv.getContext('2d');
const hud = document.getElementById('hud');
let state = null;

async function pull() {
  try {
    const r = await fetch('/api/state');
    state = await r.json();
  } catch (e) { /* сервер ещё не поднялся */ }
}
setInterval(pull, 250); pull();

function draw() {
  requestAnimationFrame(draw);
  if (!state || state.game !== 'snake') {
    hud.textContent = state && state.game ? state.name : 'Нет активной игры';
    return;
  }
  const s = state;
  const cw = cv.width / s.width, ch = cv.height / s.height;
  ctx.clearRect(0, 0, cv.width, cv.height);

  // еда
  ctx.fillStyle = '#ff5b5b';
  ctx.beginPath();
  ctx.arc((s.food[0] + .5) * cw, (s.food[1] + .5) * ch, cw * .38, 0, 7);
  ctx.fill();

  // змея
  s.snake.forEach(([x, y], i) => {
    ctx.fillStyle = i === 0 ? '#7CFC9B' : '#2ecc71';
    ctx.fillRect(x * cw + 1, y * ch + 1, cw - 2, ch - 2);
  });
  if (s.snake.length) { // глаза
    const [hx, hy] = s.snake[0];
    ctx.fillStyle = '#0b2818';
    ctx.fillRect(hx * cw + cw * .25, hy * ch + ch * .3, 4, 4);
    ctx.fillRect(hx * cw + cw * .6, hy * ch + ch * .3, 4, 4);
  }

  let status = '';
  if (s.game_over) status = ' 💀 GAME OVER';
  else if (s.paused) status = ' ⏸ ПАУЗА';
  hud.textContent = `🐍 ${s.name} | Счёт: ${s.score} | Рекорд: ${s.high_score}` + status;
}
draw();
</script>
</body>
</html>
"""


class OverlayServer:
    def __init__(self, registry: GameRegistry, host: str = "0.0.0.0", port: int = 8080) -> None:
        self.registry = registry
        self.host = host
        self.port = port
        self._runner: web.AppRunner | None = None

    # --- handlers -------------------------------------------------------------
    async def overlay(self, request: web.Request) -> web.Response:
        return web.Response(text=OVERLAY_HTML, content_type="text/html")

    async def api_state(self, request: web.Request) -> web.Response:
        game = self.registry.active
        data = game.get_state() if game else {"game": None}
        return web.json_response(data, dumps=json.dumps)

    async def api_games(self, request: web.Request) -> web.Response:
        active = self.registry.active
        data = {
            "available": self.registry.available,
            "active": active.id if active else None,
            "commands": [
                {"name": c.name, "usage": c.usage, "description": c.description}
                for c in self.registry.active_commands()
            ],
        }
        return web.json_response(data, dumps=json.dumps)

    # --- lifecycle --------------------------------------------------------------
    async def start(self) -> None:
        app = web.Application()
        app.add_routes([
            web.get("/overlay", self.overlay),
            web.get("/", self.overlay),
            web.get("/api/state", self.api_state),
            web.get("/api/games", self.api_games),
        ])
        self._runner = web.AppRunner(app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, self.host, self.port)
        await site.start()
        log.info("Оверлей доступен: http://%s:%s/overlay", self.host, self.port)

    async def stop(self) -> None:
        if self._runner is not None:
            await self._runner.cleanup()
            self._runner = None
