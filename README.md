<p align="center">
  <img src="assets/capa.svg" alt="J.A.R.V.I.S. — Assistente Inteligente para Linux" width="100%">
</p>

# J.A.R.V.I.S. — Assistente Inteligente para Linux

Assistente desktop experimental para Linux que integra **Gemini, function calling, ferramentas locais, memória SQLite e uma interface PySide6**.

O objetivo desta edição pública é simples: **mostrar somente o que realmente funciona**. Controles de voz, automações amplas e outros experimentos do protótipo privado não aparecem como botões ativos enquanto não houver implementação pública verificável.

<p align="center">
  <img src="assets/screenshot-real.png" alt="Interface real do J.A.R.V.I.S." width="900">
</p>

## Estado atual

| Área | Estado |
|---|---|
| Chat gráfico + Gemini | ✅ Funcional |
| Function calling com resultado estruturado | ✅ Funcional |
| Busca e abertura de aplicativos XDG | ✅ Funcional |
| CPU, RAM, disco, uptime e sessão Linux | ✅ Funcional |
| Memória SQLite local | ✅ Funcional quando habilitada |
| Shell local | ⚠️ Opt-in, desativado por padrão |
| Layout responsivo desktop | ✅ Compacto, médio e amplo |
| CLI com `--cli` | ✅ Funcional |
| CI + testes | ✅ Automatizados |
| Voz, wake word, visão e automação ampla | 📋 Fora da interface pública até implementação verificável |

## O que mudou na revisão de funcionalidade

A interface deixou de ser tratada como mockup. Cada área visível agora corresponde a uma capacidade real:

- **Ferramentas** executa leitura do sistema, pesquisa aplicativos, abre aplicativos e expõe shell somente quando habilitado;
- **Memória** permite adicionar, atualizar e remover fatos do SQLite local;
- **Sistema** acompanha recursos reais do computador;
- **Configurações** mostra o estado efetivamente carregado e oferece diagnóstico não sensível;
- páginas e controles sem backend público real foram removidos da navegação.

A janela também não depende mais de um tamanho fixo grande. O layout possui três modos:

```text
< 780 px       compacto
780–1119 px    médio
>= 1120 px     amplo
```

No modo compacto a sidebar vira navegação por ícones e o inspector é ocultado. Cards de Ferramentas e Sistema são reorganizados conforme a largura.

## Agente: execução verificável

O modelo não executa ações diretamente.

```text
Usuário
  ↓
Gemini
  ↓ function call
Dispatcher
  ↓
Ferramenta local
  ↓
{ ok, tool, message, data/error }
  ↓
Gemini
  ↓
Resposta ao usuário
```

O contrato das ferramentas diferencia sucesso e falha explicitamente. O agente recebe instruções para **não declarar uma ação concluída quando `ok=false`**.

Também existem limites contra loops e chamadas penduradas:

- timeout configurável para requisições ao modelo;
- número máximo de etapas do agente;
- retentativas de API limitadas;
- bloqueio de chamadas idênticas repetidas;
- finalização automática sem novas ferramentas ao atingir o limite.

Isso não transforma o modelo em um sistema infalível, mas reduz dois problemas concretos: repetição sem progresso e afirmação de sucesso sem evidência.

## Stack

`Python 3.11+` · `PySide6 / Qt 6` · `google-genai` · `SQLite` · `psutil` · `python-dotenv`

## Instalação

```bash
git clone https://github.com/Jczarf/assistente-linux-jarvis.git
cd assistente-linux-jarvis

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
```

Adicione sua própria chave ao `.env`:

```env
GEMINI_API_KEY=sua_chave
```

Execute:

```bash
python main.py
```

Fallback de terminal:

```bash
python main.py --cli
```

## Configuração

```env
GEMINI_API_KEY=
JARVIS_MODEL=gemini-2.5-flash
JARVIS_NAME=JARVIS

JARVIS_MEMORY_ENABLED=false
JARVIS_ALLOW_SHELL=false
JARVIS_SHELL_TIMEOUT=8
JARVIS_MAX_COMMAND_LENGTH=500

JARVIS_REQUEST_TIMEOUT=45
JARVIS_MAX_AGENT_STEPS=6
JARVIS_AGENT_RETRIES=2
JARVIS_TOOL_REPEAT_LIMIT=1
```

Memória e shell permanecem **desativados por padrão**.

Mudanças no `.env` são aplicadas ao reiniciar o aplicativo.

## Ferramentas disponíveis ao modelo

### `system_info`

Retorna estado atual de sistema, CPU, RAM e disco.

### `list_apps`

Pesquisa aplicações gráficas pelas entradas XDG `.desktop`.

### `open_app`

Abre um executável no `PATH` ou uma entrada XDG quando o usuário pede explicitamente.

### `run_command`

Executa shell somente quando `JARVIS_ALLOW_SHELL=true`, com limite de tamanho, timeout e bloqueios básicos.

### `remember` / `recall`

Persistência SQLite local quando `JARVIS_MEMORY_ENABLED=true`.

## Segurança

Este projeto dá acesso limitado do LLM ao computador local, então defaults conservadores são intencionais:

- `.env`, banco local e credenciais ficam fora do Git;
- shell vem desligado;
- comandos multilinha e padrões destrutivos conhecidos são bloqueados;
- comandos possuem timeout e limite de tamanho;
- ferramentas retornam sucesso/falha de forma estruturada;
- o modelo é instruído a não transformar falha em sucesso;
- memória é local e opcional.

**A política de shell não é uma sandbox formal.** Não habilite execução genérica em ambientes onde um comando incorreto possa causar dano relevante.

Mais detalhes: [`docs/SEGURANCA.md`](docs/SEGURANCA.md).

## Testes

```bash
python -m pytest -q
```

O CI cobre atualmente Python 3.11 e 3.12, compilação, verificações de segurança, ferramentas e regras de layout.

A validação headless não substitui teste visual em um desktop Linux real.

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
├── tests/
├── assets/
├── docs/
├── .env.example
└── requirements.txt
```

## Escopo

O J.A.R.V.I.S. é um **projeto pessoal em evolução**, não um assistente de sistema operacional pronto para produção.

A edição pública prioriza código que possa ser lido, executado e explicado. Funcionalidades do protótipo privado só devem voltar para a interface quando puderem ser testadas de forma reproduzível.

## Autor

**Júlio Cézar**  
Estudante de Ciência da Computação · Técnico em Desenvolvimento de Sistemas

[LinkedIn](https://www.linkedin.com/in/j%C3%BAlio-c%C3%A9zar-0a26152b2/) · [GitHub](https://github.com/Jczarf)

## Uso do código

Código disponibilizado para avaliação de portfólio e estudo. Consulte [`LICENSE`](LICENSE) antes de reutilizar ou redistribuir.
