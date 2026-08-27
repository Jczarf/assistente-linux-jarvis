#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$PROJECT_DIR/.venv/bin/python"

if [[ ! -x "$PYTHON" ]]; then
  echo "Ambiente virtual não encontrado. Execute $PROJECT_DIR/install.sh primeiro." >&2
  exit 1
fi

if ! "$PYTHON" -c 'from importlib.metadata import version; p=version("google-genai").split("."); raise SystemExit(0 if tuple(map(int, p[:2])) >= (2, 11) else 1)' >/dev/null 2>&1; then
  echo "Dependências do JARVIS estão desatualizadas. Execute $PROJECT_DIR/install.sh novamente." >&2
  exit 1
fi

exec "$PYTHON" "$PROJECT_DIR/main.py" "$@"
