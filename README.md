<p align="center">
  <img src="assets/capa.svg" alt="J.A.R.V.I.S. — Assistente para Linux" width="100%">
</p>

# J.A.R.V.I.S.

Assistente desktop para Linux desenvolvido em Python. O projeto integra **Gemini**, ferramentas locais, memória SQLite opcional e uma interface em **PySide6 / Qt 6**.

<p align="center">
  <img src="assets/screenshot-real.png" alt="Interface do J.A.R.V.I.S." width="900">
</p>

## Recursos

- chat com Gemini e function calling;
- informações de CPU, memória, disco e sessão Linux;
- busca e abertura de aplicativos pelas entradas XDG;
- shell local opcional, com timeout e bloqueios básicos;
- memória persistente em SQLite;
- interface adaptável para diferentes larguras de janela;
- modo terminal com `--cli`.

## Instalação

Requer Python 3.11 ou superior.

```bash
git clone https://github.com/Jczarf/assistente-linux-jarvis.git
cd assistente-linux-jarvis

python3 -m venv .venv
source .venv/bin/activate
pip install .

cp .env.example .env
```

Adicione sua chave do Gemini ao arquivo `.env`:

```env
GEMINI_API_KEY=sua_chave
```

Depois execute:

```bash
python main.py
```

Para usar pelo terminal:

```bash
python main.py --cli
```

## Configuração

As principais opções ficam no `.env`:

```env
JARVIS_MODEL=gemini-2.5-flash
JARVIS_NAME=JARVIS
JARVIS_MEMORY_ENABLED=false
JARVIS_ALLOW_SHELL=false
```

Outros limites de execução e timeout estão documentados no próprio `.env.example`.

Memória persistente e shell ficam desativados por padrão.

## Estrutura

```text
.
├── main.py
├── jarvis/
│   ├── config.py
│   ├── core.py
│   ├── gui.py
│   ├── memory.py
│   ├── security.py
│   └── tools.py
├── assets/
├── .env.example
└── pyproject.toml
```

## Observação sobre o shell

A execução de comandos é opcional e possui filtros para alguns padrões destrutivos, mas não funciona como uma sandbox completa. Mantenha `JARVIS_ALLOW_SHELL=false` quando não precisar desse recurso.

## Autor

**Júlio Cézar**  
Estudante de Ciência da Computação · Técnico em Desenvolvimento de Sistemas

[LinkedIn](https://www.linkedin.com/in/j%C3%BAlio-c%C3%A9zar-0a26152b2/) · [GitHub](https://github.com/Jczarf)

## Licença

Consulte o arquivo [`LICENSE`](LICENSE).
