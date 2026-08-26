# Interface gráfica

A edição pública do J.A.R.V.I.S. possui uma interface desktop inspirada no conceito visual usado no material de portfólio.

## Objetivo

A GUI foi desenhada para deixar visíveis três coisas ao mesmo tempo:

1. a conversa com o assistente;
2. o estado real das capacidades locais habilitadas;
3. métricas básicas do Linux em tempo real.

A implementação usa **Tkinter**, disponível na biblioteca padrão do Python em muitas distribuições, evitando adicionar um framework gráfico pesado apenas para a vitrine.

## Estrutura visual

A janela é dividida em três áreas:

- **barra lateral esquerda:** navegação entre Chat, Ferramentas, Automação, Memória, Sistema e Configurações;
- **área central:** conversa e páginas de detalhamento;
- **painel lateral direito:** estado de interação, ferramentas, CPU, memória, disco e memória persistente.

O tema usa fundo escuro, tipografia clara e verde como cor de destaque, aproximando a implementação do conceito visual do projeto sem transformar um mockup em alegação de funcionalidade.

## Funcionalidades reais da GUI

- chat integrado ao mesmo `JarvisAssistant` usado pela CLI;
- chamada ao modelo em thread separada para não travar a janela;
- CPU, RAM e disco atualizados periodicamente com `psutil`;
- indicação explícita do estado de shell e memória;
- página de sistema com informações locais;
- página de ferramentas;
- página de memória;
- página de configurações efetivas;
- fallback para CLI em ambientes SSH/headless.

## Recursos não simulados

A interface **não finge** que módulos inexistentes estão funcionando. Voz e automação avançada aparecem como não portadas ou em desenvolvimento nesta edição.

## Execução

Interface gráfica:

```bash
python main.py
```

Modo terminal:

```bash
python main.py --cli
```

Em Debian/Ubuntu, caso o Python tenha sido instalado sem suporte Tk:

```bash
sudo apt install python3-tk
```

## Observação de compatibilidade

Tkinter é adequado para esta edição de portfólio por ser pequeno e portátil, mas a aparência pode variar um pouco conforme fontes, compositor e desktop environment. O código possui fallback para `DejaVu Sans` e `DejaVu Sans Mono` quando Inter/JetBrains Mono não estão instaladas.
