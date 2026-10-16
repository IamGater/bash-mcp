"""Прописывает bash-mcp в конфиг Claude Desktop (с бэкапом и слиянием с существующими серверами)."""
import json
import os
import shutil
import sys
import glob
from pathlib import Path


def find_config() -> Path:
    appdata = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    local = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    candidates = [appdata / "Claude" / "claude_desktop_config.json"]
    # Версия из Microsoft Store хранит конфиг в песочнице пакета
    candidates += [
        Path(p) for p in glob.glob(str(
            local / "Packages" / "Claude_*" / "LocalCache" / "Roaming" / "Claude" / "claude_desktop_config.json"))
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


def main() -> int:
    python_exe, server_py, workdir = sys.argv[1:4]
    cfg_path = find_config()
    cfg_path.parent.mkdir(parents=True, exist_ok=True)

    cfg = {}
    if cfg_path.exists() and cfg_path.read_text(encoding="utf-8").strip():
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"ОШИБКА: {cfg_path} содержит невалидный JSON ({e}). Исправь файл вручную.")
            return 1
        shutil.copy2(cfg_path, cfg_path.with_suffix(".json.bak"))

    cfg.setdefault("mcpServers", {})["bash-mcp"] = {
        "command": python_exe,
        "args": [server_py],
        "env": {"BASH_MCP_WORKDIR": workdir, "BASH_MCP_TIMEOUT": "60"},
    }
    cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Конфиг обновлён: {cfg_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
