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


@dataclass(frozen=True)
class Settings:
    api_key: str = os.getenv("GEMINI_API_KEY", "")
    model: str = os.getenv("JARVIS_MODEL", "gemini-2.5-flash")
    assistant_name: str = os.getenv("JARVIS_NAME", "JARVIS")
    memory_enabled: bool = _as_bool("JARVIS_MEMORY_ENABLED", False)
    allow_shell: bool = _as_bool("JARVIS_ALLOW_SHELL", False)
    shell_timeout: int = int(os.getenv("JARVIS_SHELL_TIMEOUT", "8"))
    max_command_length: int = int(os.getenv("JARVIS_MAX_COMMAND_LENGTH", "500"))
    data_dir: Path = Path(
        os.getenv(
            "JARVIS_DATA_DIR",
            str(Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "jarvis-assistente"),
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


settings = Settings()
