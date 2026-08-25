from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class CommandDecision:
    allowed: bool
    reason: str = ""


_BLOCKED_PATTERNS = [
    r"(^|\s)rm\s+-rf\s+/(?:\s|$)",
    r"(^|\s)rm\s+-rf\s+~(?:\s|$)",
    r"(^|\s)mkfs(?:\.|\s)",
    r"(^|\s)dd\s+.*\bof=/dev/",
    r"(^|\s)shutdown(?:\s|$)",
    r"(^|\s)reboot(?:\s|$)",
    r"(^|\s)poweroff(?:\s|$)",
    r"(^|\s)halt(?:\s|$)",
    r":\(\)\s*\{\s*:\|:&\s*;\s*\}\s*;\s*:",
    r"(^|\s)chmod\s+-R\s+777\s+/(?:\s|$)",
    r"(^|\s)chown\s+-R\s+[^\s]+\s+/(?:\s|$)",
]

_BLOCKED_RE = [re.compile(p, re.IGNORECASE) for p in _BLOCKED_PATTERNS]


def validate_command(command: str, *, enabled: bool, max_length: int) -> CommandDecision:
    command = command.strip()

    if not enabled:
        return CommandDecision(False, "shell genérico está desativado por configuração")
    if not command:
        return CommandDecision(False, "comando vazio")
    if len(command) > max_length:
        return CommandDecision(False, "comando excede o tamanho máximo permitido")
    if "\x00" in command or "\n" in command or "\r" in command:
        return CommandDecision(False, "comandos multilinha não são permitidos nesta edição")

    for pattern in _BLOCKED_RE:
        if pattern.search(command):
            return CommandDecision(False, "comando bloqueado pela política de segurança")

    return CommandDecision(True)
