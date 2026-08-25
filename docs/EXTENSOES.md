# Extensões do projeto original

A edição pública mantém um núcleo pequeno e auditável. O protótipo privado possui módulos adicionais que demonstram a evolução do projeto, mas foram removidos desta publicação até passarem por revisão individual de segurança e portabilidade.

## Voz em tempo real

Integração com Gemini Live para áudio bidirecional, transcrição, function calling durante a conversa, reconexão automática e retomada de sessão.

Dependências principais do protótipo: `sounddevice`, `PyAudio` e recursos de áudio do Linux.

## Interface gráfica

GUI construída em Tkinter com estados visuais para escuta, processamento, fala e execução de ferramentas.

A versão pública utiliza imagens vetoriais próprias para documentar a identidade visual sem depender de assets privados do ambiente original.

## Palavra de ativação

O protótipo possui integração com OpenWakeWord para ativação por voz em segundo plano. A publicação desse módulo exige documentar modelo de wake word, requisitos de áudio e comportamento entre distribuições.

## Visão e automação de desktop

Há experimentos com captura/análise de tela e controle de mouse/teclado. Esses módulos são mais sensíveis em ambientes Wayland e têm maior impacto de segurança, portanto não fazem parte do núcleo público.

## Navegador

Automação baseada em Playwright aparece no protótipo original. Uma versão pública futura deverá isolar perfil de navegador, downloads e credenciais do usuário.

## Autonomia e rotinas

O protótipo evoluiu para rotinas proativas e ferramentas de produtividade/estudo. Para publicação, a regra será manter cada automação explícita, configurável e fácil de desabilitar.

## Critério para promoção ao repositório público

Uma extensão só deve migrar do projeto privado quando:

1. não depender de segredo ou dado pessoal;
2. funcionar sem caminhos fixos;
3. tiver fallback ou mensagem clara para recurso ausente;
4. possuir limites de segurança proporcionais ao impacto;
5. tiver documentação e teste mínimo reproduzível.
