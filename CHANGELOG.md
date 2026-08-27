# Changelog

## 1.2.0 — Funcionalidade verificável e layout responsivo

- interface reorganizada para expor somente capacidades públicas com backend real;
- remoção de controles cenográficos de voz e automação da navegação ativa;
- layout responsivo com modos compacto, médio e amplo e janela mínima de `680×520`;
- Ferramentas com controles reais para sistema, aplicativos XDG, shell opt-in e memória;
- memória SQLite gerenciável pela interface, incluindo remoção de fatos;
- contrato estruturado das ferramentas com `ok`, `error`, `message` e `data`;
- agente impedido de declarar sucesso quando uma ferramenta retorna falha;
- timeout configurável para chamadas ao modelo;
- retentativas, número de etapas e repetição idêntica de ferramentas limitados;
- finalização automática sem novas tool calls ao atingir o limite de etapas;
- novos testes para breakpoints responsivos, contrato de ferramentas e assinatura anti-repetição;
- documentação e estado do projeto sincronizados com a implementação pública real.

## 1.0.0 — Edição pública sanitizada

- criação de repositório independente, sem importar o histórico do monorepo privado;
- remoção de configurações específicas do computador original;
- migração de segredos para variáveis de ambiente;
- memória persistente desativada por padrão;
- shell genérico desativado por padrão;
- criação de política explícita para comandos de maior risco;
- redução do núcleo para dependências reproduzíveis;
- compatibilidade baseada em PATH e convenções XDG;
- documentação de arquitetura, segurança e compatibilidade;
- testes automatizados e workflow de CI;
- nova apresentação visual para portfólio.

### Fora do escopo desta edição

Os módulos privados de voz, wake word, visão, automação do navegador, controle de desktop e autonomia não foram copiados automaticamente. Eles poderão ser publicados posteriormente, módulo a módulo, após revisão específica de portabilidade e segurança.
