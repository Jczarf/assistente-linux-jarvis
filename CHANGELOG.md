# Changelog

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

Os módulos privados de voz, GUI, wake word, visão, automação do navegador, controle de desktop e autonomia não foram copiados automaticamente. Eles poderão ser publicados posteriormente, módulo a módulo, após revisão específica de portabilidade e segurança.
