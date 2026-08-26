<p align="center">
  <img src="assets/capa.svg" alt="J.A.R.V.I.S. — Assistente Inteligente para Linux" width="100%">
</p>

# J.A.R.V.I.S. — Assistente Inteligente para Linux

Protótipo pessoal em evolução de um assistente para Linux que conecta **LLMs, function calling, interface gráfica e automação local**. Esta edição foi refatorada para portfólio, removendo configurações pessoais, segredos, caminhos fixos e partes excessivamente acopladas ao computador de desenvolvimento.

> **Estado real:** esta não é a versão completa do assistente original e não deve ser apresentada como produto finalizado. Há um núcleo público funcional e sanitizado; voz, wake word, visão e automações mais amplas continuam experimentais, privadas ou ainda não foram portadas.

## Estado do projeto

| Área | Estado |
|---|---|
| Interface gráfica desktop em PySide6 / Qt 6 | ✅ Implementada nesta edição |
| Chat gráfico + Gemini + function calling | ✅ Implementado nesta edição |
| Painel real de CPU, RAM e disco | ✅ Implementado com `psutil` |
| CLI | ✅ Mantida como fallback com `--cli` |
| Memória SQLite opcional | ✅ Implementada nesta edição |
| Política básica de segurança para shell | 🧪 Implementada, mas não é sandbox formal |
| Testes + GitHub Actions | 🧪 CI precisa permanecer verde após a migração para Qt |
| Voz, wake word, visão e automação ampla | 📋 Protótipo privado / não portados integralmente |

Detalhamento: [`docs/ESTADO-DO-PROJETO.md`](docs/ESTADO-DO-PROJETO.md).

## Interface gráfica

A GUI foi reconstruída em **PySide6 / Qt 6** para ficar muito mais próxima do mockup criado para o projeto.

A composição segue a mesma direção visual:

- sidebar escura com navegação à esquerda;
- terminal/chat no centro;
- inspector à direita;
- verde neon e ciano como destaques;
- cartões arredondados com bordas e sombras;
- CPU, RAM e disco com barras de progresso reais;
- status de ferramentas, memória e shell;
- páginas específicas para Ferramentas, Automação, Memória, Sistema e Configurações;
- tipografia preparada para Inter e JetBrains Mono, com fallbacks portáveis.

A interface mostra **estado real**, em vez de simular funcionalidades:

- CPU, RAM, disco, uptime, hostname, shell e desktop são lidos do computador;
- shell e memória mostram se estão realmente habilitados;
- voz aparece como **não portada** e o microfone permanece desabilitado;
- automação avançada é apresentada como recurso ainda não portado;
- o chat usa o mesmo núcleo e o mesmo dispatcher da CLI;
- chamadas ao modelo são feitas em `QThread` para não congelar a janela.

Documentação: [`docs/INTERFACE-GRAFICA.md`](docs/INTERFACE-GRAFICA.md).

## O que o projeto demonstra

- construção de interface desktop com Qt/PySide6;
- integração de IA com ferramentas locais;
- arquitetura modular em Python;
- configuração segura por variáveis de ambiente;
- execução de comandos com política de segurança;
- memória SQLite opcional e local;
- descoberta de aplicações de forma portátil;
- monitoramento básico do Linux em tempo real;
- tratamento explícito de diferenças entre distribuições;
- testes e CI.

## Arquitetura

<p align="center">
  <img src="assets/arquitetura.svg" alt="Arquitetura simplificada" width="900">
</p>

O modelo **não executa ações diretamente**. Ele solicita uma ferramenta, o dispatcher valida a chamada e somente então uma ação local é executada.

```text
PySide6 GUI / CLI
       ↓
Usuário → LLM → Function Calling → Dispatcher → Política de segurança → Linux
                                              ↓
                                        resultado estruturado
                                              ↓
                                           resposta
```

Mais detalhes em [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md).

## Stack

`Python 3.11+` · `PySide6 / Qt 6` · `Gemini API` · `SQLite` · `python-dotenv` · `psutil`

Recursos avançados como voz, wake word, visão e automação de navegador pertencem ao protótipo original e estão documentados como extensões, não como funcionalidades concluídas desta edição.

## Instalação

```bash
git clone https://github.com/Jczarf/assistente-linux-jarvis.git
cd assistente-linux-jarvis

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# adicione sua própria GEMINI_API_KEY no arquivo .env

python main.py
```

Para usar somente o terminal:

```bash
python main.py --cli
```

## Configuração

```env
GEMINI_API_KEY=sua_chave_aqui
JARVIS_MODEL=gemini-2.5-flash
JARVIS_NAME=JARVIS
JARVIS_MEMORY_ENABLED=false
JARVIS_ALLOW_SHELL=false
```

A edição pública adota defaults conservadores: **memória persistente e shell genérico vêm desativados**. Eles precisam ser habilitados explicitamente.

## Compatibilidade

A camada pública evita caminhos hardcoded e tenta descobrir recursos usando `PATH`, variáveis XDG e ferramentas disponíveis no sistema.

| Ambiente | Situação |
|---|---|
| Linux Mint / Ubuntu / Debian | alvo principal |
| Fedora | funções básicas projetadas para funcionar |
| Arch Linux | funções básicas projetadas para funcionar |
| X11 / Wayland | Qt usa o backend gráfico disponível; automação depende do ambiente |
| SSH/headless | use `python main.py --cli` |
| Windows/macOS | fora do escopo atual |

Essa tabela representa **escopo de compatibilidade**, não certificação em todas as distribuições. Veja [`docs/COMPATIBILIDADE.md`](docs/COMPATIBILIDADE.md).

## Segurança

Dar ferramentas locais a um LLM exige limites explícitos. Esta versão:

- não contém chaves de API;
- não contém IPs, senhas, e-mails privados ou caminhos pessoais;
- mantém `.env` e bancos locais fora do Git;
- bloqueia padrões destrutivos conhecidos no shell;
- desativa shell por padrão;
- limita tamanho e tempo de comandos;
- recomenda confirmação humana para ações sensíveis;
- mantém dados de memória somente no computador do usuário;
- não apresenta voz/automação privada como se estivesse ativa.

Essas proteções **reduzem risco, mas não constituem uma sandbox formal**. Leia [`docs/SEGURANCA.md`](docs/SEGURANCA.md).

## Demonstração

<p align="center">
  <img src="assets/demo-terminal.svg" alt="Exemplo conceitual de uso" width="820">
</p>

O material visual do portfólio serviu como referência de design. A interface real agora replica a estrutura principal do mockup, mas screenshots reais ainda devem ser capturados em uma sessão Linux desktop para substituir representações conceituais.

## Estrutura

```text
.
├── main.py
├── jarvis/
│   ├── config.py
│   ├── core.py
│   ├── gui.py
│   ├── memory.py
│   ├── security.py
│   └── tools.py
├── tests/
├── assets/
├── docs/
├── .env.example
├── .gitignore
└── requirements.txt
```

## IA aplicada ao desenvolvimento

O projeto também serviu como ambiente de experimentação com desenvolvimento assistido por IA: planejamento, implementação, revisão, testes, documentação e investigação de falhas. Sugestões produzidas por agentes são tratadas como propostas e passam por revisão antes de serem incorporadas.

## Limitações conhecidas

A GUI pública cobre o fluxo de texto, monitoramento do sistema e páginas de estado, mas ainda não replica integralmente o protótipo privado. Integrações que dependem de microfone, wake word, visão, navegador ou permissões elevadas permanecem deliberadamente fora desta edição até serem sanitizadas e testadas.

O CI é executado em ambiente headless: ele pode validar importação, compilação e testes, mas não substitui inspeção visual da janela em desktops Linux reais.

## Status

**Protótipo pessoal em evolução.** A edição pública demonstra um subconjunto sanitizado da arquitetura original, agora com uma GUI Qt de alta fidelidade em relação ao conceito visual.

## Autor

**Júlio Cézar**  
Estudante de Ciência da Computação · Técnico em Desenvolvimento de Sistemas

[LinkedIn](https://www.linkedin.com/in/j%C3%BAlio-c%C3%A9zar-0a26152b2/) · [GitHub](https://github.com/Jczarf)

## Uso do código

Código disponibilizado para avaliação de portfólio e estudo. Consulte [`LICENSE`](LICENSE) antes de reutilizar ou redistribuir.