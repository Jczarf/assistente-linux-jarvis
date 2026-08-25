# Segurança

## Princípio

O J.A.R.V.I.S. conecta um modelo de linguagem a ferramentas locais. Isso aumenta a utilidade do assistente, mas também aumenta a superfície de risco. A edição pública adota o princípio **desativado por padrão para capacidades de maior impacto**.

## Segredos

Nenhuma chave real deve existir no repositório.

- `GEMINI_API_KEY` é lida do ambiente;
- `.env` está no `.gitignore`;
- `.env.example` contém apenas nomes de variáveis e valores de demonstração não sensíveis;
- nenhum IP, senha, token, e-mail privado ou caminho pessoal é necessário para executar esta edição.

Antes de tornar o repositório público, recomenda-se executar também um scanner de segredos no histórico novo.

## Shell

`JARVIS_ALLOW_SHELL=false` por padrão.

Quando explicitamente habilitado:

- há limite de tamanho de comando;
- comandos multilinha são recusados;
- há timeout configurável;
- padrões destrutivos conhecidos são bloqueados;
- saída retornada ao modelo é truncada.

### Limitação importante

Uma blocklist **não é uma sandbox**. Existem inúmeras formas de expressar operações equivalentes no shell. Em ambiente de produção, a estratégia recomendada é substituir shell genérico por ferramentas específicas e com argumentos tipados, além de isolamento no sistema operacional.

## Memória

`JARVIS_MEMORY_ENABLED=false` por padrão.

Quando habilitada, a memória é armazenada em SQLite no diretório local do usuário. Esta edição não envia o banco para serviços externos e não salva automaticamente todo o histórico de conversa.

## Ferramentas

Cada ferramenta deve seguir três regras:

1. receber somente os argumentos necessários;
2. retornar resultado limitado e estruturado;
3. evitar privilégios elevados e efeitos destrutivos por padrão.

## Modelo de ameaça simplificado

Consideramos, principalmente:

- prompt injection levando o modelo a chamar uma ferramenta indevida;
- comandos gerados de forma incorreta;
- exposição acidental de informações do sistema;
- segredos versionados por engano;
- dependência de caminhos e programas específicos do computador do autor.

A mitigação começa por reduzir privilégios e exposição, e não por confiar que o modelo sempre escolherá corretamente.

## Checklist antes de publicar

- [x] repositório novo, sem histórico do monorepo privado;
- [x] configuração movida para variáveis de ambiente;
- [x] caminhos pessoais removidos;
- [x] shell desativado por padrão;
- [x] memória desativada por padrão;
- [x] `.env` e bancos ignorados;
- [x] documentação deixa claro que os guardrails não formam uma sandbox;
- [ ] executar CI da versão final;
- [ ] executar scanner de segredos no GitHub após publicação/ativação do recurso correspondente.
