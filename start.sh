#!/usr/bin/env bash
# ============================================
#  Игры для стрима — запуск одной кнопкой
#  ./start.sh
# ============================================
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
    echo ""
    echo "[ОШИБКА] Python не найден!"
    echo "Установите: https://www.python.org/downloads/"
    echo ""
    exit 1
fi

echo "Проверяю зависимости..."
if ! python3 -c "import aiohttp, twitchio" 2>/dev/null; then
    echo "Устанавливаю нужные библиотеки, это займёт минуту..."
    python3 -m pip install -r requirements.txt
fi

echo ""
echo "Запускаю бота... (остановка — Ctrl+C)"
echo "Оверлей для OBS откроется на http://localhost:8080/overlay"
echo ""
python3 main.py
