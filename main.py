#!/usr/bin/env python3
from __future__ import annotations

import argparse

from jarvis.config import settings
from jarvis.core import JarvisAssistant


def run_cli() -> None:
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


def main() -> None:
    parser = argparse.ArgumentParser(description="J.A.R.V.I.S. — Assistente para Linux")
    parser.add_argument(
        "--cli",
        action="store_true",
        help="usa a interface de terminal em vez da interface gráfica",
    )
    args = parser.parse_args()

    if args.cli:
        run_cli()
        return

    try:
        from jarvis.gui import run_gui

        run_gui()
    except (ImportError, ModuleNotFoundError) as exc:
        raise SystemExit(
            "Interface gráfica Qt indisponível. Instale as dependências com "
            "`pip install .` ou use `python main.py --cli`."
        ) from exc
    except Exception as exc:
        message = str(exc).lower()
        if any(term in message for term in ("display", "xcb", "wayland", "platform plugin")):
            raise SystemExit(
                "Não foi possível abrir a interface gráfica neste ambiente. "
                "Em sessões SSH/headless use `python main.py --cli`."
            ) from exc
        raise


if __name__ == "__main__":
    main()
