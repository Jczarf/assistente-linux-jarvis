# Estado real do projeto

Este documento separa o que existe na edição pública, o que pertence ao protótipo privado e o que ainda não deve ser tratado como concluído.

## Legenda

- ✅ **Implementado e verificado nesta edição** — há código correspondente e, quando aplicável, validação automatizada recente.
- 🧪 **Parcial / em validação** — existe implementação ou experimento, mas não deve ser apresentado como concluído ou amplamente validado.
- 📋 **Fora da edição pública / planejado** — pertence ao protótipo privado, depende do ambiente original ou ainda não foi consolidado para publicação.

## Estado por área

| Área | Estado | Observação |
|---|---|---|
| CLI em Python | ✅ | Ponto de entrada público disponível e incluído na etapa de compilação do CI. |
| Integração com Gemini | ✅ | Configurada por variável de ambiente; chamadas reais continuam dependentes de chave e serviço externo. |
| Function calling e dispatcher | ✅ | Núcleo reduzido presente na edição pública. |
| Informações básicas do sistema | ✅ | Implementação portátil com `psutil`. |
| Memória local SQLite | ✅ | Opcional e desativada por padrão. |
| Shell genérico | 🧪 | Existe, mas é opt-in e possui política de bloqueio; não é sandbox formal. |
| Testes automatizados | ✅ | Suíte básica executada com sucesso pelo GitHub Actions. |
| GitHub Actions | ✅ | CI validado em 26/08/2026 no commit `cd1fc81`: compilação e testes concluíram com sucesso em Python 3.11 e 3.12. |
| Interface gráfica completa | 📋 | Existiu como experimento no protótipo privado e não foi portada integralmente. |
| Voz bidirecional / Gemini Live | 📋 | Parte do protótipo privado, não consolidada nesta edição. |
| Wake word | 📋 | Não incluído na edição pública atual. |
| Visão/análise de tela | 📋 | Não incluída na edição pública atual. |
| Automação ampla de navegador e desktop | 📋 | Reduzida por segurança e portabilidade. |
| Suporte multiplataforma | 📋 | O foco atual é Linux; Windows/macOS não são escopo desta edição. |

## Evidência automatizada mais recente

Em **26/08/2026**, o workflow `CI` concluiu com sucesso no commit `cd1fc81b601e06ecbc5df7eb549f6d689f454572`.

A validação automatizada cobre:

- instalação das dependências;
- compilação de `jarvis/` e `main.py`;
- execução da suíte pública com `pytest`;
- Python 3.11;
- Python 3.12.

Isso valida a **edição pública reduzida**. Não deve ser interpretado como teste das extensões que continuam somente no protótipo privado.

## Como descrever em portfólio

Use formulações como:

> Protótipo pessoal em evolução de assistente para Linux, com uma edição pública reduzida e sanitizada que demonstra integração com LLM, function calling, ferramentas locais, memória e controles básicos de segurança. A edição pública possui CI validado em Python 3.11 e 3.12.

Evite dizer:

- “assistente completo para Linux”;
- “sandbox seguro”;
- “compatível com qualquer distribuição”;
- “todas as ferramentas do protótipo estão implementadas”; ou
- que as extensões privadas foram testadas pelo CI público.

## Próximos passos

- ampliar testes de segurança e ferramentas;
- melhorar tratamento de erros do provider;
- selecionar, refatorar e publicar somente extensões do protótipo privado que sejam portáveis e seguras;
- adicionar uma demonstração real gravada quando a edição pública estiver estável.
