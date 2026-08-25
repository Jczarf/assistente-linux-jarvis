#!/usr/bin/env python3
from __future__ import annotations

from jarvis.config import settings
from jarvis.core import JarvisAssistant


def main() -> None:
    print(f"\n{settings.assistant_name} — Assistente para Linux")
    print("Digite 'sair' para encerrar.\n")

    try:
        assistant = JarvisAssistant()
    except RuntimeError as exc:
        raise SystemExit(f"Configuração inválida: {exc}") from exc

    while True:
        try:
            text = input("Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrado.")
            break

        if not text:
            continue
        if text.lower() in {"sair", "exit", "quit"}:
            print(f"{settings.assistant_name}: Até logo.")
            break

        try:
            answer = assistant.ask(text)
        except Exception as exc:
            print(f"Erro: {exc}")
            continue

        print(f"{settings.assistant_name}: {answer}\n")


if __name__ == "__main__":
    main()
