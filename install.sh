#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

PYTHON_BIN="${PYTHON_BIN:-}"

if [[ -z "$PYTHON_BIN" ]]; then
  for candidate in python3.12 python3.11 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
      PYTHON_BIN="$candidate"
      break
    fi
  done
fi

if [[ -z "$PYTHON_BIN" ]] || ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python 3.11 ou superior não encontrado." >&2
  exit 1
fi

if ! "$PYTHON_BIN" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then
  echo "O JARVIS requer Python 3.11 ou superior." >&2
  exit 1
fi

SELECTED_VERSION="$($PYTHON_BIN -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"

if [[ -d .venv && ! -x .venv/bin/python ]]; then
  echo "O diretório .venv existe, mas está incompleto. Remova-o e execute ./install.sh novamente." >&2
  exit 1
fi

if [[ ! -d .venv ]]; then
  echo "Criando .venv com $PYTHON_BIN (Python $SELECTED_VERSION)..."
  "$PYTHON_BIN" -m venv .venv
else
  VENV_VERSION="$(.venv/bin/python -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"
  echo "Usando .venv existente com Python $VENV_VERSION."
fi

.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install .

SDK_VERSION="$(.venv/bin/python -c 'from importlib.metadata import version; print(version("google-genai"))')"
echo "Google Gen AI SDK $SDK_VERSION instalado."

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Arquivo .env criado. Adicione sua GEMINI_API_KEY antes de iniciar o JARVIS."
else
  MODEL_MIGRATED="$(.venv/bin/python - <<'PY'
from pathlib import Path

path = Path('.env')
lines = path.read_text(encoding='utf-8').splitlines()
changed = False
for index, line in enumerate(lines):
    if line.strip() == 'JARVIS_MODEL=gemini-2.5-flash':
        indent = line[: len(line) - len(line.lstrip())]
        lines[index] = f'{indent}JARVIS_MODEL=gemini-3.6-flash'
        changed = True
if changed:
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('1' if changed else '0')
PY
)"
  if [[ "$MODEL_MIGRATED" == "1" ]]; then
    echo "JARVIS_MODEL atualizado: gemini-2.5-flash -> gemini-3.6-flash."
  fi
fi

echo "Instalação concluída. Execute ./run.sh"
