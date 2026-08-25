# Compatibilidade

## Escopo

A edição pública prioriza Linux desktop e remove dependências fixas do computador em que o protótipo original foi desenvolvido.

## Distribuições

### Linux Mint / Ubuntu / Debian

É o caminho principal de compatibilidade. As funções básicas de CLI, memória, informações de sistema e descoberta de aplicações devem funcionar sem configuração adicional além das dependências Python.

### Fedora / Arch Linux

O núcleo Python não depende de `apt`, então as funções públicas básicas continuam válidas. Recursos futuros de gerenciamento de pacotes devem detectar o gerenciador disponível em vez de assumir `apt`.

## X11 e Wayland

A edição pública atual não depende de automação gráfica, portanto funciona nos dois cenários para CLI.

O protótipo privado possui recursos de teclado, mouse, janela e captura de tela que podem se comportar de forma diferente em Wayland. Esses módulos não foram copiados para a versão pública justamente para evitar falsa promessa de portabilidade.

## Diretórios

Não existem caminhos como `/home/usuario/...` no código público.

Dados locais seguem:

1. `JARVIS_DATA_DIR`, se configurado;
2. `XDG_DATA_HOME/jarvis-assistente`;
3. `~/.local/share/jarvis-assistente` como fallback.

## Aplicativos

`list_apps` procura arquivos `.desktop` em locais XDG comuns.

`open_app` exige que o nome informado corresponda a um executável no `PATH`; não existe uma tabela pública com programas específicos instalados na máquina do autor.

## Recursos não incluídos nesta edição

- áudio bidirecional e PipeWire;
- wake word;
- automação de navegador;
- controle de janelas, teclado e mouse;
- gerenciamento de serviços e pacotes;
- rotinas proativas;
- integrações específicas de hardware.

Esses recursos continuam relevantes para o projeto original, mas dependem mais fortemente do ambiente e serão publicados apenas quando puderem ser isolados e testados adequadamente.
