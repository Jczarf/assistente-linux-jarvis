#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$PROJECT_DIR/.venv/bin/python"

if [[ ! -x "$PYTHON" ]]; then
  echo "Ambiente virtual não encontrado. Execute $PROJECT_DIR/install.sh primeiro." >&2
  exit 1
fi

exec "$PYTHON" "$PROJECT_DIR/main.py" "$@"
