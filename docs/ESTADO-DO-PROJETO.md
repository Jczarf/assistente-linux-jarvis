# Estado real do projeto

Este documento separa o que existe na edição pública, o que pertence ao protótipo privado e o que ainda não deve ser tratado como concluído.

## Legenda

- ✅ **Implementado e verificado nesta edição** — há código correspondente e, quando aplicável, validação automatizada recente.
- 🧪 **Parcial / em validação** — existe implementação ou experimento, mas não deve ser apresentado como concluído ou amplamente validado.
- 📋 **Fora da edição pública / planejado** — pertence ao protótipo privado, depende do ambiente original ou ainda não foi consolidado para publicação.

## Estado por área

| Área | Estado | Observação |
|---|---|---|
| Interface gráfica desktop | 🧪 | GUI foi reconstruída em PySide6 / Qt 6 para seguir de perto o mockup. Código implementado; validação visual em desktop Linux real ainda é necessária. |
| Chat gráfico integrado ao núcleo | ✅ | Usa o mesmo `JarvisAssistant` da CLI e executa chamadas em `QThread` para não bloquear a janela. |
| Painel de CPU, RAM e disco | ✅ | Dados reais atualizados periodicamente com `psutil`. |
| Navegação GUI: Chat, Ferramentas, Automação, Memória, Sistema e Configurações | ✅ | Páginas implementadas na edição pública. |
| CLI em Python | ✅ | Mantida como fallback com `python main.py --cli`. |
| Integração com Gemini | ✅ | Configurada por variável de ambiente; chamadas reais continuam dependentes de chave e serviço externo. |
| Function calling e dispatcher | ✅ | Núcleo reduzido presente na edição pública. |
| Informações básicas do sistema | ✅ | Implementação portátil com `psutil`. |
| Memória local SQLite | ✅ | Opcional e desativada por padrão. |
| Shell genérico | 🧪 | Existe, mas é opt-in e possui política de bloqueio; não é sandbox formal. |
| Testes automatizados | ✅ | Suíte básica existente; deve permanecer verde após a migração para Qt. |
| GitHub Actions | 🧪 | Workflow atualizado com smoke test de importação da GUI via `QT_QPA_PLATFORM=offscreen`; resultado da nova baseline ainda precisa ser confirmado. |
| Renderização visual em múltiplos desktops Linux | 🧪 | A GUI possui fallbacks de fonte e tamanho mínimo definido, mas ainda não foi inspecionada em diferentes compositores, escalas e distribuições. |
| Voz bidirecional / Gemini Live | 📋 | Parte do protótipo privado, não consolidada nesta edição. A GUI mostra a capacidade como não portada. |
| Wake word | 📋 | Não incluído na edição pública atual. |
| Visão/análise de tela | 📋 | Não incluída na edição pública atual. |
| Automação ampla de navegador e desktop | 📋 | Reduzida por segurança e portabilidade; a página de Automação deixa explícito que o módulo avançado ainda não foi portado. |
| Suporte multiplataforma | 📋 | O foco atual é Linux; Windows/macOS não são escopo desta edição. |

## Migração visual

A primeira GUI pública usava Tkinter e serviu como prova de integração. Ela foi substituída por **PySide6 / Qt 6** porque o objetivo de portfólio passou a ser reproduzir de forma muito mais fiel o conceito visual criado para o J.A.R.V.I.S.

A nova interface inclui:

- sidebar fixa à esquerda;
- terminal/chat central;
- inspector fixo à direita;
- cartões arredondados e sombras;
- verde neon e ciano como identidade visual;
- barras reais de CPU, RAM e disco;
- status real de ferramentas, shell e memória;
- páginas internas com a mesma linguagem visual;
- worker de IA em `QThread`.

## Evidência automatizada

O workflow foi atualizado para validar:

- instalação das dependências, incluindo PySide6;
- compilação de `jarvis/` e `main.py`;
- importação de `jarvis.gui` em modo offscreen;
- execução da suíte pública com `pytest`;
- Python 3.11;
- Python 3.12.

O CI headless **não substitui inspeção visual** da janela em X11/Wayland reais.

## Como descrever em portfólio

Use formulações como:

> Protótipo pessoal em evolução de assistente para Linux, com edição pública sanitizada que demonstra interface desktop em Qt, integração com LLM, function calling, ferramentas locais, memória, monitoramento do sistema e controles básicos de segurança.

Evite dizer:

- “assistente completo para Linux”;
- “sandbox seguro”;
- “compatível com qualquer distribuição”;
- “voz e automação avançada já funcionam na edição pública”; ou
- que o CI headless validou visualmente a GUI.

## Próximos passos

- confirmar a nova baseline de CI após a migração para Qt;
- executar a GUI em desktop Linux real e registrar screenshots reais;
- ajustar eventuais diferenças de escala, fonte ou compositor;
- ampliar testes de segurança e ferramentas;
- melhorar tratamento de erros do provider;
- selecionar e portar somente extensões privadas que sejam seguras e defensáveis em portfólio.
