# Estado real do projeto

Este documento separa o que existe na edição pública do J.A.R.V.I.S. do que ainda pertence ao protótipo privado ou permanece fora de escopo.

## Legenda

- ✅ **Implementado** — existe código correspondente e validação automatizada quando aplicável.
- 🧪 **Parcial / condicionado ao ambiente** — existe implementação, mas o comportamento depende de permissões, desktop Linux ou configuração explícita.
- 📋 **Fora da edição pública** — não aparece como funcionalidade ativa enquanto não houver implementação pública verificável.

## Estado por área

| Área | Estado | Observação |
|---|---|---|
| Interface gráfica PySide6 / Qt 6 | ✅ | Navegação e páginas reais implementadas. |
| Layout responsivo | ✅ | Modos compacto, médio e amplo com mínimo de `680×520`. |
| Chat gráfico integrado ao núcleo | ✅ | Usa o mesmo `JarvisAssistant` da CLI e processa chamadas do modelo em `QThread`. |
| CLI em Python | ✅ | Fallback com `python main.py --cli`. |
| Gemini | ✅ | Integração real, dependente de chave e serviço externo. |
| Function calling | ✅ | Ferramentas retornam sucesso/falha estruturados. |
| Proteção contra repetição de tool calls | ✅ | Chamadas idênticas acima do limite configurado não são executadas novamente. |
| Timeout do provider | ✅ | Configurável por `JARVIS_REQUEST_TIMEOUT`. |
| Limite de etapas do agente | ✅ | Configurável por `JARVIS_MAX_AGENT_STEPS`. |
| Informações do sistema | ✅ | CPU, RAM, disco, kernel, uptime e sessão Linux. |
| Busca de aplicativos XDG | ✅ | Pesquisa entradas `.desktop`. |
| Abertura de aplicativos | 🧪 | Usa executáveis no `PATH` ou `gtk-launch`; depende do desktop disponível. |
| Memória SQLite | ✅ | Persistência local opcional; GUI permite adicionar, atualizar e remover fatos. |
| Shell genérico | 🧪 | Opt-in, limitado por timeout e política básica; não é sandbox formal. |
| Configurações / diagnóstico | ✅ | Exibe estado carregado sem mostrar segredos e permite copiar diagnóstico não sensível. |
| Testes automatizados | ✅ | `pytest` cobre ferramentas, segurança, breakpoints e lógica auxiliar do agente. |
| GitHub Actions | ✅ | CI em Python 3.11 e 3.12, compilação, smoke da GUI e auditoria de segurança. |
| Renderização em múltiplos desktops Linux | 🧪 | O layout é adaptativo, mas diferenças de compositor, fonte e escala ainda exigem teste visual real. |
| Voz / wake word | 📋 | Não expostos como controle ativo na edição pública. |
| Visão/análise de tela | 📋 | Fora da edição pública atual. |
| Automação ampla de navegador/desktop | 📋 | Fora da interface pública até existir implementação segura e testável. |
| Windows/macOS | 📋 | Fora do escopo atual. |

## Princípio de produto

A edição pública não usa páginas ou botões para representar funcionalidades que ainda não existem.

Se uma capacidade não foi portada, ela deve aparecer somente como limitação documentada — não como controle interativo cenográfico.

## Arquitetura operacional

```text
GUI / CLI
   ↓
JarvisAssistant
   ↓
Gemini + function calling
   ↓
Dispatcher
   ↓
Ferramenta local
   ↓
{ ok, tool, message, data/error }
   ↓
Resposta final
```

O modelo recebe o resultado real da ferramenta e é instruído a não declarar sucesso quando `ok=false`.

Para impedir repetição sem progresso, o núcleo limita etapas, bloqueia tool calls idênticas repetidas e, quando o limite é atingido, faz uma etapa final sem novas ferramentas usando somente os resultados já obtidos.

## Interface atual

A GUI possui:

- sidebar de navegação;
- chat central;
- inspector apenas em larguras amplas;
- cards responsivos;
- páginas reais de Ferramentas, Memória, Sistema e Configurações;
- barras reais de CPU, RAM e disco;
- status real de shell, memória, LLM e suporte XDG;
- operações de memória pela própria interface.

Breakpoints:

```text
< 780 px       compacto
780–1119 px    médio
>= 1120 px     amplo
```

## Evidência automatizada

O workflow valida:

- instalação das dependências;
- Python 3.11 e 3.12;
- segurança da árvore pública;
- compilação de `jarvis/` e `main.py`;
- importação da GUI em modo offscreen;
- suíte `pytest`.

O CI headless **não certifica a aparência visual em todos os desktops Linux**.

## Como descrever em portfólio

Formulação adequada:

> Protótipo pessoal em evolução de assistente para Linux, com interface desktop em Qt, integração com Gemini, function calling, ferramentas locais, memória SQLite, monitoramento do sistema e limites explícitos contra execução sem evidência e repetição de chamadas.

Evite dizer:

- “assistente completo para Linux”;
- “sandbox segura”;
- “compatível com qualquer distribuição”;
- “voz e automação avançada já funcionam”; ou
- que CI headless equivale a validação visual em desktop real.

## Próximos passos legítimos

- ampliar testes de integração do provider com doubles/fakes;
- testar visualmente em X11 e Wayland com escalas diferentes;
- melhorar cancelamento cooperativo de operações longas;
- fortalecer a política de shell ou substituí-la por ações mais restritas;
- portar novas capacidades somente quando houver backend, teste e comportamento de erro definidos.
