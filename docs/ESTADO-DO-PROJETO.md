# Estado real do projeto

Este documento separa o que existe na edição pública, o que pertence ao protótipo privado e o que ainda não deve ser tratado como concluído.

## Legenda

- ✅ **Implementado e verificado nesta edição** — há código correspondente e, quando aplicável, validação automatizada recente.
- 🧪 **Parcial / em validação** — existe implementação ou experimento, mas não deve ser apresentado como concluído ou amplamente validado.
- 📋 **Fora da edição pública / planejado** — pertence ao protótipo privado, depende do ambiente original ou ainda não foi consolidado para publicação.

## Estado por área

| Área | Estado | Observação |
|---|---|---|
| Interface gráfica desktop | ✅ | GUI em Tkinter implementada na edição pública, inspirada no conceito visual do portfólio. O código é compilado no CI; a renderização depende de ambiente gráfico Linux. |
| Chat gráfico integrado ao núcleo | ✅ | Usa o mesmo `JarvisAssistant` da CLI e executa chamadas em thread separada para não bloquear a janela. |
| Painel de CPU, RAM e disco | ✅ | Dados reais atualizados periodicamente com `psutil`. |
| Navegação GUI: Chat, Ferramentas, Memória, Sistema e Configurações | ✅ | Páginas implementadas na edição pública. |
| CLI em Python | ✅ | Mantida como fallback com `python main.py --cli`. |
| Integração com Gemini | ✅ | Configurada por variável de ambiente; chamadas reais continuam dependentes de chave e serviço externo. |
| Function calling e dispatcher | ✅ | Núcleo reduzido presente na edição pública. |
| Informações básicas do sistema | ✅ | Implementação portátil com `psutil`. |
| Memória local SQLite | ✅ | Opcional e desativada por padrão. |
| Shell genérico | 🧪 | Existe, mas é opt-in e possui política de bloqueio; não é sandbox formal. |
| Testes automatizados | ✅ | Suíte básica executada com sucesso pelo GitHub Actions. |
| GitHub Actions | ✅ | O commit que introduziu GUI + fallback CLI passou no CI em Python 3.11 e 3.12 em 26/08/2026. |
| Renderização visual em múltiplos desktops Linux | 🧪 | A GUI é responsiva e possui fontes de fallback, mas ainda não foi validada em todos os desktops/compositores. |
| Voz bidirecional / Gemini Live | 📋 | Parte do protótipo privado, não consolidada nesta edição. A GUI mostra essa capacidade como não portada. |
| Wake word | 📋 | Não incluído na edição pública atual. |
| Visão/análise de tela | 📋 | Não incluída na edição pública atual. |
| Automação ampla de navegador e desktop | 📋 | Reduzida por segurança e portabilidade; a página de Automação não finge que esses módulos estão ativos. |
| Suporte multiplataforma | 📋 | O foco atual é Linux; Windows/macOS não são escopo desta edição. |

## Evidência automatizada

Em **26/08/2026**, o workflow `CI` concluiu com sucesso após a introdução da interface gráfica e do novo ponto de entrada que usa GUI por padrão e preserva `--cli`.

A validação automatizada cobre:

- instalação das dependências;
- compilação de `jarvis/`, incluindo `jarvis/gui.py`;
- compilação de `main.py`;
- execução da suíte pública com `pytest`;
- Python 3.11;
- Python 3.12.

O CI não abre uma janela gráfica no runner headless. Portanto ele valida sintaxe, importações usadas pela suíte e regressões do núcleo, mas **não substitui inspeção visual em uma sessão desktop real**.

## Como descrever em portfólio

Use formulações como:

> Protótipo pessoal em evolução de assistente para Linux, com edição pública sanitizada que demonstra interface gráfica desktop, integração com LLM, function calling, ferramentas locais, memória, monitoramento do sistema e controles básicos de segurança.

Evite dizer:

- “assistente completo para Linux”;
- “sandbox seguro”;
- “compatível com qualquer distribuição”;
- “voz e automação avançada já funcionam na edição pública”; ou
- que o CI headless validou visualmente a GUI.

## Próximos passos

- executar a GUI em desktops Linux reais e registrar screenshots reais;
- ampliar testes de segurança e ferramentas;
- melhorar tratamento de erros do provider;
- selecionar, refatorar e publicar somente extensões do protótipo privado que sejam portáveis e seguras;
- adicionar demonstração real gravada quando a edição pública estiver estável.
