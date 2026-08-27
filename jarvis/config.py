from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


def _as_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on", "sim"}


def _as_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw.strip())
    except ValueError as exc:
        raise RuntimeError(f"{name} deve ser um número inteiro.") from exc


@dataclass(frozen=True)
class Settings:
    api_key: str = os.getenv("GEMINI_API_KEY", "")
    model: str = os.getenv("JARVIS_MODEL", "gemini-3.6-flash")
    assistant_name: str = os.getenv("JARVIS_NAME", "JARVIS")
    memory_enabled: bool = _as_bool("JARVIS_MEMORY_ENABLED", False)
    allow_shell: bool = _as_bool("JARVIS_ALLOW_SHELL", False)
    shell_timeout: int = _as_int("JARVIS_SHELL_TIMEOUT", 8)
    max_command_length: int = _as_int("JARVIS_MAX_COMMAND_LENGTH", 500)
    request_timeout_seconds: int = _as_int("JARVIS_REQUEST_TIMEOUT", 45)
    max_agent_steps: int = _as_int("JARVIS_MAX_AGENT_STEPS", 6)
    agent_retries: int = _as_int("JARVIS_AGENT_RETRIES", 2)
    tool_repeat_limit: int = _as_int("JARVIS_TOOL_REPEAT_LIMIT", 1)
    data_dir: Path = Path(
        os.getenv(
            "JARVIS_DATA_DIR",
            str(
                Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))
                / "jarvis-assistente"
            ),
        )
    ).expanduser()

    def validate(self) -> None:
        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY não configurada. Copie .env.example para .env e adicione sua própria chave."
            )
        if not 1 <= self.shell_timeout <= 60:
            raise RuntimeError("JARVIS_SHELL_TIMEOUT deve estar entre 1 e 60 segundos.")
        if not 50 <= self.max_command_length <= 2000:
            raise RuntimeError("JARVIS_MAX_COMMAND_LENGTH deve estar entre 50 e 2000 caracteres.")
        if not 5 <= self.request_timeout_seconds <= 180:
            raise RuntimeError("JARVIS_REQUEST_TIMEOUT deve estar entre 5 e 180 segundos.")
        if not 1 <= self.max_agent_steps <= 12:
            raise RuntimeError("JARVIS_MAX_AGENT_STEPS deve estar entre 1 e 12.")
        if not 0 <= self.agent_retries <= 4:
            raise RuntimeError("JARVIS_AGENT_RETRIES deve estar entre 0 e 4.")
        if not 1 <= self.tool_repeat_limit <= 3:
            raise RuntimeError("JARVIS_TOOL_REPEAT_LIMIT deve estar entre 1 e 3.")


settings = Settings()
