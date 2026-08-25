# Arquitetura do J.A.R.V.I.S.

## Objetivo

Separar conversação, contexto, ferramentas e execução local para que o modelo de linguagem atue como orquestrador, sem concentrar regras de sistema dentro do prompt.

## Fluxo principal

```text
Entrada do usuário
  ├─ voz
  ├─ texto
  └─ interface gráfica
        │
        ▼
Sessão de IA
        │
        ├─ prompt do sistema
        ├─ contexto atual
        ├─ memória local
        └─ declarações de ferramentas
        │
        ▼
Seleção de ferramenta
        │
        ▼
Dispatcher
        │
        ├─ apps
        ├─ sistema
        ├─ arquivos
        ├─ navegador
        ├─ tela
        ├─ rede
        └─ utilidades
        │
        ▼
Execução local
        │
        ▼
Resultado estruturado
        │
        ▼
Resposta ao usuário
```

## Componentes

### Orquestração
Responsável por inicializar os modos de operação e encaminhar entrada de voz ou texto para a sessão apropriada.

### Sessão de IA
Mantém a comunicação com o modelo de linguagem e executa o ciclo de function calling.

### Registro de ferramentas
Centraliza as capacidades disponíveis ao modelo e seus parâmetros esperados.

### Ações
As ações do sistema são separadas por domínio: aplicações, sistema, rede, arquivos, navegador, tela e outros recursos.

### Contexto
Coleta informações relevantes do ambiente para que o assistente possa responder de maneira contextual sem depender apenas do histórico da conversa.

### Memória
Persistência local para fatos e preferências selecionados, evitando depender exclusivamente da janela de contexto do modelo.

## Decisões de segurança

O projeto trata execução de comandos e manipulação de arquivos como superfícies de risco. Entre as estratégias adotadas estão:

- bloqueio de padrões destrutivos conhecidos;
- limites de tamanho e tempo de execução;
- confirmação para ações sensíveis;
- proteção de caminhos;
- registro de ações para auditoria;
- preferência por ferramentas específicas em vez de shell genérico quando possível.

Essas medidas reduzem risco, mas não transformam a aplicação em uma sandbox de segurança formal.

## Evolução

A arquitetura foi pensada para permitir expansão incremental: novas ferramentas podem ser adicionadas ao registro e ao dispatcher sem alterar o fluxo central da aplicação.
