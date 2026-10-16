# bash-mcp

MCP-сервер (stdio), который даёт Claude три инструмента:
`run_powershell`, `run_bash`, `run_cmd` (только Windows).

## Установка

```
cd bash-mcp
python -m venv .venv
.venv\Scripts\activate        # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

## Подключение к Claude Desktop

Открой конфиг (Settings → Developer → Edit Config) и добавь блок из
`claude_desktop_config.example.json`, подставив свои пути. Если ставил venv,
в `command` укажи путь к `python.exe` из `.venv`. Затем полностью перезапусти Claude Desktop.

## Переменные окружения

| Переменная | Назначение | По умолчанию |
|---|---|---|
| `BASH_MCP_WORKDIR` | рабочая папка по умолчанию | домашняя папка |
| `BASH_MCP_ALLOWED_ROOT` | ограничить cwd этой папкой | не задано (без ограничения) |
| `BASH_MCP_TIMEOUT` | таймаут, сек | 60 |
| `BASH_MCP_MAX_OUTPUT` | макс. символов вывода | 20000 |

## Безопасность

Сервер выполняет **произвольные команды** с твоими правами. Важно:
- Оставь включённым подтверждение вызова инструментов в Claude Desktop и читай команды перед разрешением.
- Задай `BASH_MCP_ALLOWED_ROOT`. Это ограничивает только стартовую папку, но не мешает команде обратиться к другим путям. Для настоящей изоляции запускай под отдельным пользователем или в VM/контейнере.
- Не подключай сервер к недоверенным источникам (например, не давай Claude выполнять инструкции из чужих файлов и сайтов без проверки).

## Проверка

```
npx @modelcontextprotocol/inspector python server.py
```
