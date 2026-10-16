"""bash-mcp: MCP-сервер для выполнения команд PowerShell / bash / cmd на локальной машине."""
import asyncio
import os
import shutil
import subprocess
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("bash-mcp")

IS_WINDOWS = sys.platform == "win32"
DEFAULT_CWD = os.environ.get("BASH_MCP_WORKDIR", str(Path.home()))
# Если задано — команды можно запускать только внутри этой папки.
ALLOWED_ROOT = os.environ.get("BASH_MCP_ALLOWED_ROOT")
MAX_OUTPUT = int(os.environ.get("BASH_MCP_MAX_OUTPUT", "20000"))
DEFAULT_TIMEOUT = int(os.environ.get("BASH_MCP_TIMEOUT", "60"))


def _resolve_cwd(cwd: str | None) -> str:
    path = Path(cwd or DEFAULT_CWD).expanduser().resolve()
    if not path.is_dir():
        raise ValueError(f"Папка не существует: {path}")
    if ALLOWED_ROOT:
        root = Path(ALLOWED_ROOT).expanduser().resolve()
        if root != path and root not in path.parents:
            raise ValueError(f"cwd вне разрешённой папки {root}")
    return str(path)


def _truncate(text: str) -> str:
    if len(text) <= MAX_OUTPUT:
        return text
    half = MAX_OUTPUT // 2
    return text[:half] + f"\n...[обрезано {len(text) - MAX_OUTPUT} символов]...\n" + text[-half:]


def _kill_tree(proc: asyncio.subprocess.Process) -> None:
    try:
        if IS_WINDOWS:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                           capture_output=True)
        else:
            proc.kill()
    except Exception:
        pass


async def _run(argv: list[str] | None, shell_cmd: str | None, cwd: str | None,
               timeout: int | None) -> str:
    try:
        workdir = _resolve_cwd(cwd)
    except ValueError as e:
        return f"Ошибка: {e}"
    timeout = timeout or DEFAULT_TIMEOUT

    try:
        if shell_cmd is not None:
            proc = await asyncio.create_subprocess_shell(
                shell_cmd, cwd=workdir,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        else:
            proc = await asyncio.create_subprocess_exec(
                *argv, cwd=workdir,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    except FileNotFoundError as e:
        return f"Ошибка: не найден интерпретатор ({e})"

    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        _kill_tree(proc)
        return f"Ошибка: таймаут {timeout} с, процесс убит."

    stdout = _truncate(out.decode("utf-8", errors="replace"))
    stderr = _truncate(err.decode("utf-8", errors="replace"))
    parts = [f"exit code: {proc.returncode}", f"cwd: {workdir}"]
    if stdout.strip():
        parts.append(f"--- stdout ---\n{stdout.rstrip()}")
    if stderr.strip():
        parts.append(f"--- stderr ---\n{stderr.rstrip()}")
    return "\n".join(parts)


@mcp.tool()
async def run_powershell(command: str, cwd: str | None = None,
                         timeout: int | None = None) -> str:
    """Выполнить команду PowerShell (pwsh, либо Windows PowerShell).

    Args:
        command: текст команды/скрипта.
        cwd: рабочая папка (по умолчанию BASH_MCP_WORKDIR или домашняя).
        timeout: таймаут в секундах (по умолчанию 60).
    """
    exe = shutil.which("pwsh") or shutil.which("powershell")
    if not exe:
        return "Ошибка: PowerShell не найден в PATH."
    return await _run([exe, "-NoLogo", "-NoProfile", "-NonInteractive",
                       "-Command", command], None, cwd, timeout)


@mcp.tool()
async def run_bash(command: str, cwd: str | None = None,
                   timeout: int | None = None) -> str:
    """Выполнить команду в bash (на Windows — Git Bash или WSL, если установлены).

    Args:
        command: текст команды/скрипта.
        cwd: рабочая папка.
        timeout: таймаут в секундах (по умолчанию 60).
    """
    exe = shutil.which("bash")
    if exe:
        return await _run([exe, "-c", command], None, cwd, timeout)
    if IS_WINDOWS and shutil.which("wsl"):
        return await _run(["wsl", "bash", "-c", command], None, cwd, timeout)
    return "Ошибка: bash не найден (на Windows установи Git for Windows или WSL)."


@mcp.tool()
async def run_cmd(command: str, cwd: str | None = None,
                  timeout: int | None = None) -> str:
    """Выполнить команду в cmd.exe (только Windows).

    Args:
        command: текст команды.
        cwd: рабочая папка.
        timeout: таймаут в секундах (по умолчанию 60).
    """
    if not IS_WINDOWS:
        return "Ошибка: cmd доступен только на Windows."
    return await _run(None, command, cwd, timeout)


if __name__ == "__main__":
    mcp.run()  # stdio
