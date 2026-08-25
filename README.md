# J.A.R.V.I.S. — Assistente Inteligente para Linux

Projeto de assistente pessoal para Linux com integração a modelos de linguagem, interação por voz e texto, automação do sistema e execução de ferramentas locais.

> **Portfólio técnico:** este repositório apresenta arquitetura, decisões de projeto e capacidades do sistema sem expor o código-fonte completo ou configurações privadas do ambiente original.

## Visão geral

O J.A.R.V.I.S. foi desenvolvido como um laboratório prático de **IA aplicada a software, automação e Linux**. A aplicação combina um modelo de linguagem com um conjunto modular de ferramentas capazes de observar o contexto do sistema e executar ações reais mediante solicitação do usuário.

O projeto possui diferentes modos de operação:

- interface gráfica;
- interação contínua por voz;
- modo texto em terminal;
- execução em segundo plano com palavra de ativação.

## Principais capacidades

- integração com Gemini para texto, voz e function calling;
- automação de aplicativos, janelas, teclado e mouse;
- coleta de informações do sistema Linux;
- gerenciamento de arquivos e processos;
- controle de rede, Bluetooth, áudio e serviços;
- automação de navegador;
- análise de tela com visão computacional;
- memória persistente local;
- pesquisa e leitura de conteúdo web;
- ferramentas auxiliares para estudo, código e produtividade.

## Stack

`Python` · `Gemini API` · `Gemini Live` · `Linux` · `Tkinter` · `PipeWire` · `OpenWakeWord` · `Playwright` · `SQLite`

## Arquitetura resumida

```text
Voz / Texto / GUI
       │
       ▼
Modelo de linguagem
       │
       ▼
Function calling / Dispatcher
       │
       ├── Sistema Linux
       ├── Aplicativos e janelas
       ├── Arquivos e processos
       ├── Navegador
       ├── Tela / visão
       ├── Rede e serviços
       └── Memória local
       │
       ▼
Resultado → modelo → usuário
```

A implementação foi organizada em módulos separados para configuração, sessão de IA, interface, memória, contexto e ações do sistema. Isso permite adicionar novas ferramentas sem concentrar toda a lógica em um único arquivo.

## Segurança e limites

Dar a um LLM acesso a ferramentas do sistema cria riscos importantes. Por isso, o projeto inclui mecanismos como validação de comandos, bloqueios para operações destrutivas, limites de execução, proteção de caminhos e registro de ações.

Essas proteções são tratadas como **camadas de redução de risco**, e não como uma sandbox infalível. Operações sensíveis devem continuar exigindo validação e confirmação explícita.

## IA no processo de desenvolvimento

O projeto também foi utilizado para experimentar desenvolvimento assistido por IA ao longo do ciclo de software: planejamento, implementação, refatoração, análise de falhas, documentação e revisão de soluções.

As alterações geradas ou sugeridas por IA são tratadas como propostas que precisam ser revisadas e validadas antes da integração.

## Status

Projeto pessoal em evolução. A versão completa permanece em repositório privado enquanto componentes, configurações e dados específicos do ambiente são sanitizados para eventual publicação seletiva.

## Autor

**Júlio Cézar**  
Estudante de Ciência da Computação · Técnico em Desenvolvimento de Sistemas

[LinkedIn](https://www.linkedin.com/in/j%C3%BAlio-c%C3%A9zar-0a26152b2/) · [GitHub](https://github.com/Jczarf)
