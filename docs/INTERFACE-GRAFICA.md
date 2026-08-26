# Interface gráfica

A edição pública do J.A.R.V.I.S. usa **PySide6 / Qt 6** para aproximar a aplicação real do mockup criado para o portfólio.

## Objetivo visual

A interface foi reconstruída para manter a mesma linguagem do conceito:

- fundo quase preto com cartões em grafite;
- verde neon e ciano como cores de destaque;
- navegação vertical à esquerda;
- área principal de conversa com aparência de terminal moderno;
- painel lateral direito com interação, ferramentas, métricas, memória e automação;
- cartões arredondados, bordas sutis, sombras e barras de progresso;
- tipografia com preferência por Inter e JetBrains Mono, com fallbacks portáveis.

A prioridade foi aproximar a **composição e a hierarquia visual** do mockup sem transformar elementos conceituais em funcionalidades falsas.

## Estrutura

A janela é dividida em três regiões permanentes:

1. **Sidebar esquerda** — Chat, Ferramentas, Automação, Memória, Sistema e Configurações.
2. **Área central** — página ativa. No Chat, inclui terminal/conversa e campo de mensagem.
3. **Inspector direito** — estado de interação, ferramentas locais, CPU, memória, disco, memória persistente e automação.

## Componentes reais

- chat integrado ao mesmo `JarvisAssistant` usado pela CLI;
- worker em `QThread` para a chamada ao modelo não congelar a janela;
- CPU, RAM e disco atualizados por `psutil`;
- sistema operacional, uptime, usuário, hostname, shell e desktop reais;
- status do shell baseado em `JARVIS_ALLOW_SHELL`;
- status da memória baseado em `JARVIS_MEMORY_ENABLED`;
- indicação da disponibilidade de `gtk-launch` para aplicativos XDG;
- página de memória com os fatos SQLite quando o recurso está habilitado;
- página de configurações sem revelar a chave da API;
- fallback completo para CLI com `python main.py --cli`.

## Elementos do mockup que continuam conceituais

A fotografia conceitual apresenta voz, waveform e automações mais avançadas. Esses itens **não são simulados como concluídos** na GUI real:

- Voz aparece como `não portada` e o botão de microfone fica desabilitado.
- A página Automação explica que o módulo avançado ainda não foi portado.
- Wake word, visão e automação ampla continuam fora da edição pública.

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

PySide6 inclui os bindings do Qt 6. Em uma sessão Linux desktop normal, o Qt seleciona o backend gráfico disponível. Em ambientes SSH/headless, use a CLI.

No CI, a GUI é importada com `QT_QPA_PLATFORM=offscreen` apenas como smoke test. Isso confirma dependências e importação, mas **não substitui inspeção visual em X11/Wayland reais**.

## Responsividade

A janela inicia em `1480×900` e possui mínimo de `1120×720`. A área central é flexível; sidebar e inspector mantêm largura fixa para preservar a composição do mockup.

## Limites de fidelidade

A implementação busca alta fidelidade visual, mas não é uma imagem estática. Tamanho de fonte, antialiasing, decoração nativa da janela e renderização podem variar conforme distribuição, compositor, escala HiDPI e fontes instaladas. Esses desvios são esperados em uma aplicação desktop real.
