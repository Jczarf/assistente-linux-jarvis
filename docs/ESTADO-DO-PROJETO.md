# Estado real do projeto

Este documento separa o que existe na edição pública, o que pertence ao protótipo privado e o que ainda não deve ser tratado como concluído.

## Legenda

- ✅ **Implementado nesta edição** — há código correspondente no repositório público.
- 🧪 **Parcial / em validação** — existe implementação ou experimento, mas não deve ser apresentado como concluído ou amplamente validado.
- 📋 **Fora da edição pública / planejado** — pertence ao protótipo privado, depende do ambiente original ou ainda não foi consolidado para publicação.

## Estado por área

| Área | Estado | Observação |
|---|---|---|
| CLI em Python | ✅ | Ponto de entrada público disponível. |
| Integração com Gemini | ✅ | Configurada por variável de ambiente. |
| Function calling e dispatcher | ✅ | Núcleo reduzido presente na edição pública. |
| Informações básicas do sistema | ✅ | Implementação portátil com `psutil`. |
| Memória local SQLite | ✅ | Opcional e desativada por padrão. |
| Shell genérico | 🧪 | Existe, mas é opt-in e possui política de bloqueio; não é sandbox formal. |
| Testes automatizados | ✅ | Testes básicos estão incluídos no repositório. |
| GitHub Actions | 🧪 | Workflow configurado; o status de execução deve ser verificado no GitHub antes de afirmar CI verde. |
| Interface gráfica completa | 📋 | Existiu como experimento no protótipo privado e não foi portada integralmente. |
| Voz bidirecional / Gemini Live | 📋 | Parte do protótipo privado, não consolidada nesta edição. |
| Wake word | 📋 | Não incluído na edição pública atual. |
| Visão/análise de tela | 📋 | Não incluída na edição pública atual. |
| Automação ampla de navegador e desktop | 📋 | Reduzida por segurança e portabilidade. |
| Suporte multiplataforma | 📋 | O foco atual é Linux; Windows/macOS não são escopo desta edição. |

## Como descrever em portfólio

Use formulações como:

> Protótipo pessoal em evolução de assistente para Linux, com uma edição pública reduzida e sanitizada que demonstra integração com LLM, function calling, ferramentas locais, memória e controles básicos de segurança.

Evite dizer:

- “assistente completo para Linux”;
- “sandbox seguro”;
- “compatível com qualquer distribuição”;
- “todas as ferramentas do protótipo estão implementadas”; ou
- “CI aprovado” sem verificar a execução do workflow.

## Próximos passos

- validar o workflow de CI em execução real;
- ampliar testes de segurança e ferramentas;
- melhorar tratamento de erros do provider;
- selecionar, refatorar e publicar somente extensões do protótipo privado que sejam portáveis e seguras;
- adicionar uma demonstração real gravada quando a edição pública estiver estável.
