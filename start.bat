@echo off
rem ============================================
rem  Игры для стрима - запуск в один клик
rem  Просто дважды кликните по этому файлу
rem ============================================
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo.
    echo [ОШИБКА] Python не найден!
    echo Скачайте и установите с https://www.python.org/downloads/
    echo ВАЖНО: при установке поставьте галочку "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo Проверяю зависимости...
python -c "import aiohttp, twitchio" 2>nul
if errorlevel 1 (
    echo Устанавливаю нужные библиотеки, это займет минуту...
    pip install -r requirements.txt
)

echo.
echo Запускаю бота... (остановка - Ctrl+C или закрыть это окно)
echo Оверлей для OBS откроется на http://localhost:8080/overlay
echo.
python main.py

pause
