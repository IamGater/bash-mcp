@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
echo === bash-mcp: автоустановка ===

rem 1. Ищем Python
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (
    where python >nul 2>nul && set "PY=python"
)
if not defined PY (
    echo ОШИБКА: Python не найден. Установи его командой: winget install Python.Python.3.12
    echo После установки запусти setup.bat снова.
    pause
    exit /b 1
)

rem 2. Виртуальное окружение
if not exist ".venv\Scripts\python.exe" (
    echo Создаю виртуальное окружение...
    %PY% -m venv .venv
    if errorlevel 1 goto :fail
)

rem 3. Зависимости
echo Устанавливаю зависимости...
".venv\Scripts\python.exe" -m pip install --upgrade pip -q
".venv\Scripts\python.exe" -m pip install -r requirements.txt -q
if errorlevel 1 goto :fail

rem 4. Прописываем сервер в конфиг Claude Desktop
echo Обновляю конфиг Claude Desktop...
".venv\Scripts\python.exe" install_config.py "%~dp0.venv\Scripts\python.exe" "%~dp0server.py" "%USERPROFILE%"
if errorlevel 1 goto :fail

echo.
echo Готово! Полностью закрой Claude Desktop ^(в том числе в трее^) и запусти заново.
echo Сервер bash-mcp появится в списке инструментов.
pause
exit /b 0

:fail
echo.
echo Что-то пошло не так, смотри сообщения выше.
pause
exit /b 1
