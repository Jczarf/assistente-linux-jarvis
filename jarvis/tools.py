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

ToolResult = dict[str, Any]
ToolImpl = Callable[[dict[str, Any]], ToolResult]


def _ok(tool: str, message: str, data: Any = None) -> ToolResult:
    result: ToolResult = {"ok": True, "tool": tool, "message": message}
    if data is not None:
        result["data"] = data
    return result


def _fail(tool: str, code: str, message: str, data: Any = None) -> ToolResult:
    result: ToolResult = {
        "ok": False,
        "tool": tool,
        "error": code,
        "message": message,
    }
    if data is not None:
        result["data"] = data
    return result


def system_info(_: dict[str, Any] | None = None) -> ToolResult:
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    data = {
        "os": f"{platform.system()} {platform.release()}",
        "cpu_threads": psutil.cpu_count(logical=True),
        "cpu_percent": round(psutil.cpu_percent(interval=None), 1),
        "ram_used_gib": round(vm.used / 1024**3, 1),
        "ram_total_gib": round(vm.total / 1024**3, 1),
        "ram_percent": round(vm.percent, 1),
        "disk_used_gib": round(disk.used / 1024**3, 1),
        "disk_total_gib": round(disk.total / 1024**3, 1),
        "disk_percent": round(disk.percent, 1),
    }
    message = (
        f"SO: {data['os']} | CPU: {data['cpu_threads']} threads "
        f"({data['cpu_percent']:.0f}%) | RAM: {data['ram_used_gib']:.1f}/"
        f"{data['ram_total_gib']:.1f} GiB ({data['ram_percent']:.0f}%) | "
        f"Disco /: {data['disk_used_gib']:.1f}/{data['disk_total_gib']:.1f} GiB "
        f"({data['disk_percent']:.0f}%)"
    )
    return _ok("system_info", message, data)


def _desktop_roots() -> list[Path]:
    roots = [Path.home() / ".local/share/applications"]
    data_dirs = os.getenv("XDG_DATA_DIRS", "/usr/local/share:/usr/share")
    roots.extend(Path(item) / "applications" for item in data_dirs.split(":") if item)
    return roots


def _desktop_entries() -> dict[str, str]:
    entries: dict[str, str] = {}
    for root in _desktop_roots():
        if not root.exists():
            continue
        for file in root.glob("*.desktop"):
            try:
                lines = file.read_text(errors="ignore").splitlines()
            except OSError:
                continue
            hidden = any(
                line.strip().lower() in {"hidden=true", "nodisplay=true"}
                for line in lines
            )
            if hidden:
                continue
            name = next(
                (
                    line.partition("=")[2].strip()
                    for line in lines
                    if line.startswith("Name=")
                ),
                "",
            )
            if name:
                entries.setdefault(name, file.stem)
    return entries


def list_apps(args: dict[str, Any] | None = None) -> ToolResult:
    query = str((args or {}).get("query", "")).strip().lower()
    names = sorted(
        name for name in _desktop_entries() if not query or query in name.lower()
    )[:80]
    if not names:
        return _fail(
            "list_apps",
            "not_found",
            "Nenhum aplicativo encontrado para esse filtro.",
            [],
        )
    return _ok(
        "list_apps",
        f"{len(names)} aplicativo(s) encontrado(s).",
        names,
    )


def run_command(args: dict[str, Any]) -> ToolResult:
    command = str(args.get("command", "")).strip()
    decision = validate_command(
        command,
        enabled=settings.allow_shell,
        max_length=settings.max_command_length,
    )
    if not decision.allowed:
        return _fail("run_command", "blocked", decision.reason)

    try:
        proc = subprocess.run(
            command,
            shell=True,
            text=True,
            capture_output=True,
            timeout=settings.shell_timeout,
            cwd=str(Path.home()),
            env={
                **os.environ,
                "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
            },
        )
    except subprocess.TimeoutExpired:
        return _fail(
            "run_command",
            "timeout",
            f"Comando excedeu o timeout de {settings.shell_timeout}s.",
        )
    except OSError as exc:
        return _fail("run_command", "os_error", str(exc))

    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()
    output = stdout or stderr or "(sem saída)"
    data = {
        "exit_code": proc.returncode,
        "stdout": stdout[:4000],
        "stderr": stderr[:4000],
    }
    if proc.returncode != 0:
        return _fail(
            "run_command",
            "nonzero_exit",
            f"Comando terminou com código {proc.returncode}.\n{output[:4000]}",
            data,
        )
    return _ok("run_command", output[:4000], data)


def open_app(args: dict[str, Any]) -> ToolResult:
    app = str(args.get("app", "")).strip()
    if not app:
        return _fail("open_app", "invalid_argument", "Nome do aplicativo não informado.")

    executable = shutil.which(app)
    if executable:
        try:
            subprocess.Popen(
                [executable],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError as exc:
            return _fail("open_app", "launch_failed", str(exc))
        return _ok("open_app", f"Aplicativo '{app}' iniciado.", {"source": "PATH"})

    entries = _desktop_entries()
    match = next(
        (
            (name, desktop_id)
            for name, desktop_id in entries.items()
            if name.casefold() == app.casefold()
        ),
        None,
    )
    gtk_launch = shutil.which("gtk-launch")
    if match and gtk_launch:
        try:
            subprocess.Popen(
                [gtk_launch, match[1]],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError as exc:
            return _fail("open_app", "launch_failed", str(exc))
        return _ok(
            "open_app",
            f"Aplicativo '{match[0]}' iniciado pela entrada XDG.",
            {"source": "XDG", "desktop_id": match[1]},
        )

    reason = (
        "gtk-launch não está disponível."
        if match and not gtk_launch
        else "Aplicativo não encontrado no PATH nem nas entradas XDG."
    )
    return _fail("open_app", "not_found", f"'{app}': {reason}")


def remember(args: dict[str, Any]) -> ToolResult:
    key = str(args.get("key", "")).strip()
    value = str(args.get("value", "")).strip()
    if not settings.memory_enabled:
        return _fail("remember", "disabled", "Memória persistente está desativada.")
    if not key or not value:
        return _fail("remember", "invalid_argument", "Chave e valor são obrigatórios.")
    message = save_fact(key, value)
    return _ok("remember", message)


def recall(_: dict[str, Any] | None = None) -> ToolResult:
    if not settings.memory_enabled:
        return _fail("recall", "disabled", "Memória persistente está desativada.")
    facts = list_facts()
    if not facts:
        return _ok("recall", "Nenhuma informação persistente disponível.", {})
    return _ok("recall", f"{len(facts)} fato(s) recuperado(s).", facts)


_TOOL_IMPL: dict[str, ToolImpl] = {
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
        "description": "Obtém informações atuais e não sensíveis de CPU, RAM, disco e sistema operacional.",
        "parameters": {"type": "OBJECT", "properties": {}},
    },
    {
        "name": "list_apps",
        "description": "Lista aplicações gráficas instaladas através de entradas XDG .desktop.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": "Filtro opcional pelo nome do aplicativo",
                }
            },
        },
    },
    {
        "name": "open_app",
        "description": "Abre um executável do PATH ou uma aplicação XDG somente quando o usuário pedir explicitamente.",
        "parameters": {
            "type": "OBJECT",
            "properties": {"app": {"type": "STRING"}},
            "required": ["app"],
        },
    },
    {
        "name": "run_command",
        "description": "Executa um comando shell apenas quando JARVIS_ALLOW_SHELL=true. Nunca use sem pedido explícito do usuário.",
        "parameters": {
            "type": "OBJECT",
            "properties": {"command": {"type": "STRING"}},
            "required": ["command"],
        },
    },
    {
        "name": "remember",
        "description": "Salva uma informação localmente somente quando o usuário pedir para lembrar e a memória persistente estiver habilitada.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "key": {"type": "STRING"},
                "value": {"type": "STRING"},
            },
            "required": ["key", "value"],
        },
    },
    {
        "name": "recall",
        "description": "Recupera informações da memória local quando habilitada.",
        "parameters": {"type": "OBJECT", "properties": {}},
    },
]


def execute_tool(name: str, args: dict[str, Any] | None = None) -> ToolResult:
    impl = _TOOL_IMPL.get(name)
    if impl is None:
        return _fail(name, "unknown_tool", f"Ferramenta desconhecida: {name}")
    try:
        return impl(args or {})
    except Exception as exc:  # fronteira do dispatcher: nunca deixa erro cru escapar ao modelo
        return _fail(name, "internal_error", f"Falha interna da ferramenta: {exc}")
