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


def list_apps(args: dict[str, Any] | None = None) -> str:
    query = str((args or {}).get("query", "")).strip().lower()
    roots = [
        Path.home() / ".local/share/applications",
        Path("/usr/local/share/applications"),
        Path("/usr/share/applications"),
    ]
    names: set[str] = set()
    for root in roots:
        if not root.exists():
            continue
        for file in root.glob("*.desktop"):
            try:
                for line in file.read_text(errors="ignore").splitlines():
                    if line.startswith("Name="):
                        name = line.partition("=")[2].strip()
                        if name and (not query or query in name.lower()):
                            names.add(name)
                        break
            except OSError:
                continue
    result = sorted(names)[:80]
    return "Aplicativos encontrados: " + ", ".join(result) if result else "Nenhum aplicativo encontrado."


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
    executable = shutil.which(app)
    if executable is None:
        return f"Executável '{app}' não encontrado no PATH."
    subprocess.Popen(
        [executable],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return f"Aplicativo '{app}' iniciado."


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
        "description": "Lista aplicações gráficas instaladas através de arquivos .desktop.",
        "parameters": {
            "type": "OBJECT",
            "properties": {"query": {"type": "STRING", "description": "Filtro opcional pelo nome"}},
        },
    },
    {
        "name": "open_app",
        "description": "Abre um executável disponível no PATH. Use somente quando o usuário pedir explicitamente.",
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
