from __future__ import annotations

import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable

import psutil

from jarvis.config import settings
from jarvis.memory import list_facts, save_fact
from jarvis.security import validate_command


def system_info(_: dict[str, Any] | None = None) -> str:
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return (
        f"SO: {platform.system()} {platform.release()} | "
        f"CPU: {psutil.cpu_count(logical=True)} threads | "
        f"RAM: {vm.used / 1024**3:.1f}/{vm.total / 1024**3:.1f} GB ({vm.percent:.0f}%) | "
        f"Disco /: {disk.used / 1024**3:.1f}/{disk.total / 1024**3:.1f} GB ({disk.percent:.0f}%)"
    )


def _desktop_roots() -> list[Path]:
    roots = [Path.home() / ".local/share/applications"]
    data_dirs = os.getenv("XDG_DATA_DIRS", "/usr/local/share:/usr/share")
    roots.extend(Path(item) / "applications" for item in data_dirs.split(":") if item)
    return roots


def _desktop_entries() -> dict[str, str]:
    """Retorna {nome exibido: desktop-id} sem depender de um usuário específico."""
    entries: dict[str, str] = {}
    for root in _desktop_roots():
        if not root.exists():
            continue
        for file in root.glob("*.desktop"):
            try:
                lines = file.read_text(errors="ignore").splitlines()
            except OSError:
                continue

            hidden = any(line.strip().lower() in {"hidden=true", "nodisplay=true"} for line in lines)
            if hidden:
                continue

            name = next(
                (line.partition("=")[2].strip() for line in lines if line.startswith("Name=")),
                "",
            )
            if name:
                entries.setdefault(name, file.stem)
    return entries


def list_apps(args: dict[str, Any] | None = None) -> str:
    query = str((args or {}).get("query", "")).strip().lower()
    names = sorted(
        name for name in _desktop_entries() if not query or query in name.lower()
    )[:80]
    return "Aplicativos encontrados: " + ", ".join(names) if names else "Nenhum aplicativo encontrado."


def run_command(args: dict[str, Any]) -> str:
    command = str(args.get("command", ""))
    decision = validate_command(
        command,
        enabled=settings.allow_shell,
        max_length=settings.max_command_length,
    )
    if not decision.allowed:
        return f"Bloqueado: {decision.reason}."

    try:
        proc = subprocess.run(
            command,
            shell=True,
            text=True,
            capture_output=True,
            timeout=settings.shell_timeout,
            cwd=str(Path.home()),
            env={**os.environ, "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin")},
        )
    except subprocess.TimeoutExpired:
        return f"Comando excedeu o timeout de {settings.shell_timeout}s."

    output = (proc.stdout or proc.stderr or "(sem saída)").strip()
    return f"exit={proc.returncode}\n{output[:4000]}"


def open_app(args: dict[str, Any]) -> str:
    app = str(args.get("app", "")).strip()
    if not app:
        return "Nome do aplicativo não informado."

    # 1) Nome de executável, portátil para programas no PATH.
    executable = shutil.which(app)
    if executable:
        subprocess.Popen(
            [executable],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return f"Aplicativo '{app}' iniciado."

    # 2) Nome amigável de uma entrada XDG. Evita hardcode de programas instalados.
    entries = _desktop_entries()
    match = next(
        ((name, desktop_id) for name, desktop_id in entries.items() if name.lower() == app.lower()),
        None,
    )
    gtk_launch = shutil.which("gtk-launch")
    if match and gtk_launch:
        subprocess.Popen(
            [gtk_launch, match[1]],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return f"Aplicativo '{match[0]}' iniciado pela entrada XDG."

    return f"Aplicativo '{app}' não encontrado no PATH nem nas entradas XDG disponíveis."


def remember(args: dict[str, Any]) -> str:
    return save_fact(str(args.get("key", "")), str(args.get("value", "")))


def recall(_: dict[str, Any] | None = None) -> str:
    facts = list_facts()
    if not facts:
        return "Nenhuma informação persistente disponível."
    return "\n".join(f"{key}: {value}" for key, value in facts.items())


_TOOL_IMPL: dict[str, Callable[[dict[str, Any]], str]] = {
    "system_info": system_info,
    "list_apps": list_apps,
    "open_app": open_app,
    "run_command": run_command,
    "remember": remember,
    "recall": recall,
}

TOOL_DECLARATIONS = [
    {
        "name": "system_info",
        "description": "Obtém informações básicas e não sensíveis de CPU, RAM, disco e sistema operacional.",
        "parameters": {"type": "OBJECT", "properties": {}},
    },
    {
        "name": "list_apps",
        "description": "Lista aplicações gráficas instaladas através de entradas XDG .desktop.",
        "parameters": {
            "type": "OBJECT",
            "properties": {"query": {"type": "STRING", "description": "Filtro opcional pelo nome"}},
        },
    },
    {
        "name": "open_app",
        "description": "Abre um executável do PATH ou uma aplicação XDG. Use somente quando o usuário pedir explicitamente.",
        "parameters": {
            "type": "OBJECT",
            "properties": {"app": {"type": "STRING"}},
            "required": ["app"],
        },
    },
    {
        "name": "run_command",
        "description": "Executa um comando shell somente quando JARVIS_ALLOW_SHELL=true. Operações destrutivas conhecidas são bloqueadas.",
        "parameters": {
            "type": "OBJECT",
            "properties": {"command": {"type": "STRING"}},
            "required": ["command"],
        },
    },
    {
        "name": "remember",
        "description": "Salva uma informação localmente quando a memória persistente está habilitada.",
        "parameters": {
            "type": "OBJECT",
            "properties": {"key": {"type": "STRING"}, "value": {"type": "STRING"}},
            "required": ["key", "value"],
        },
    },
    {
        "name": "recall",
        "description": "Lista as informações da memória local quando habilitada.",
        "parameters": {"type": "OBJECT", "properties": {}},
    },
]


def execute_tool(name: str, args: dict[str, Any] | None = None) -> str:
    impl = _TOOL_IMPL.get(name)
    if impl is None:
        return f"Ferramenta desconhecida: {name}"
    return impl(args or {})
