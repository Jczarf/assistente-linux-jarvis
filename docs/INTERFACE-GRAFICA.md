# Interface gráfica

A edição pública do J.A.R.V.I.S. usa **PySide6 / Qt 6** e segue uma regra simples: a interface só deve expor como interativo aquilo que possui implementação pública real.

## Estrutura atual

A aplicação possui cinco áreas de navegação:

1. **Chat** — conversa com o mesmo `JarvisAssistant` usado pela CLI.
2. **Ferramentas** — controles diretos para sistema, aplicativos XDG, shell opt-in e memória.
3. **Memória** — leitura, inclusão, atualização e remoção de fatos SQLite quando habilitada.
4. **Sistema** — métricas e informações reais do computador.
5. **Configurações** — estado efetivamente carregado do ambiente e diagnóstico não sensível.

Controles de voz e uma página de automação não aparecem como funcionalidades públicas enquanto não houver backend verificável correspondente.

## Responsividade

A janela inicia em `1320×820` e aceita tamanho mínimo de `680×520`.

Existem três modos de layout:

```text
< 780 px       compacto
780–1119 px    médio
>= 1120 px     amplo
```

### Compacto

- sidebar reduzida para ícones;
- inspector ocultado;
- margens menores;
- cards de Ferramentas em uma coluna;
- cards de Sistema em uma coluna.

### Médio

- sidebar textual reduzida;
- inspector ocultado;
- Ferramentas em uma coluna;
- Sistema em duas colunas.

### Amplo

- sidebar completa;
- inspector visível;
- Ferramentas em duas colunas;
- Sistema em três colunas.

O rearranjo ocorre no `resizeEvent`, sem depender de screenshots ou ajustes manuais por resolução.

## Componentes reais

- chat integrado ao `JarvisAssistant`;
- chamada ao modelo executada em `QThread` para manter a janela responsiva;
- CPU, RAM, disco, uptime, usuário, hostname, shell e desktop lidos do sistema;
- busca de aplicações por entradas XDG;
- abertura de aplicativos por `PATH` ou `gtk-launch` quando disponível;
- shell somente quando `JARVIS_ALLOW_SHELL=true`;
- memória SQLite somente quando `JARVIS_MEMORY_ENABLED=true`;
- gerenciamento de memória pela própria GUI;
- configurações sem exibir a chave da API;
- cópia de diagnóstico não sensível;
- abertura do diretório local de dados.

## Estado e falhas

A GUI usa o mesmo dispatcher do agente. Ferramentas retornam um contrato estruturado com sucesso ou erro explícito. A interface mostra a mensagem recebida em vez de transformar falha em sucesso aparente.

Quando uma capacidade está desativada, o controle correspondente permanece desativado e a interface explica qual configuração seria necessária para habilitá-la.

## Execução

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

Modo terminal:

```bash
python main.py --cli
```

## Qt e ambientes Linux

Em uma sessão Linux desktop normal, o Qt seleciona o backend gráfico disponível. Em SSH/headless, use a CLI.

No CI, a GUI é importada com `QT_QPA_PLATFORM=offscreen`. Isso valida importação, compilação e regras testáveis de layout, mas **não substitui inspeção visual em X11/Wayland reais**.

## Limites de fidelidade

Fontes, escala HiDPI, decoração nativa e antialiasing podem variar entre distribuições e compositores. O objetivo da responsividade é preservar usabilidade e hierarquia, não reproduzir pixels idênticos em todo ambiente.
