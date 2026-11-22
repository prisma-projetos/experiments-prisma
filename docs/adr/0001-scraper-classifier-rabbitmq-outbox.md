# ADR 0001 — RabbitMQ entre Scraper e Classifier, com outbox no scraper

**Status**: Aceito (16-17/08/2026)

## Contexto

O desenho original cogitava o Classifier consumir a fila `analysis_jobs` direto do Postgres do scraper. Isso contraria uma regra já definida no `context.md` raiz (seção 7.2 — "Scraper DB mantém separação lógica"; seção 19.2 — "nenhum componente deve acessar diretamente o banco... de outro").

A tabela `analysis_jobs` (implementada no `scrapping-prisma`, com trigger + `src/jobs_store.py` + `FOR UPDATE SKIP LOCKED`) já resolve bem o problema de concorrência entre workers — então a dúvida não era "como evitar dois workers pegarem o mesmo job", e sim como evitar acoplar os dois bancos.

## Decisão

RabbitMQ como broker entre Scraper e Classifier. `analysis_jobs` não é descartada — muda de papel: deixa de ser "fila que um worker externo consome" e passa a ser um **outbox transacional interno ao `scrapping-prisma`**, gravada via trigger na mesma transação que marca o artigo como `success`.

O `scrapping-prisma` ganha um publisher que lê `analysis_jobs` (reaproveitando `claim_next_job`) e publica cada job no RabbitMQ, com o conteúdo do artigo embutido no payload (texto, título, `canonical_link`, `source_name`, `published_at`, `article_id`, `job_id`, `pipeline_version`) — não só o ID, para o Classifier nunca precisar voltar ao Postgres do scraper.

Ao publicar com sucesso, o publisher marca o job com o status `published_job`. Falha de publicação usa o retry (`attempts`/`max_attempts`) já existente e testado.

**Regra sem exceção**: o Classifier nunca tem connection string para o Postgres do scraper. Só fala com o RabbitMQ.

## Parâmetros de conexão confirmados com o DevOps

| Item | Valor |
|---|---|
| Exchange | `scraper.entrada.exchange` |
| Fila | `scraper.dados.queue` |
| Tipo de exchange | `direct` |
| Durável | `true` |
| Dead-letter queue | `scraper.dados.dlq` (gerenciada pelo DevOps — o Classifier não precisa referenciá-la) |
| Ack | manual (`auto_ack=False`) — confirma só depois de processar com sucesso |
| Routing key | **ainda não confirmada** — publisher usa o nome da fila como default provisório |

Pendente antes do consumidor entrar em produção: routing key exata, credenciais do usuário de consumo (permissão só de leitura).

## Consequências

- Lado do publisher já implementado e commitado no `scrapping-prisma` (commit `4e6c161`): confirmação de entrega (`confirm_delivery` + `mandatory=True`), circuit breaker após falhas consecutivas, não declara/cria topologia (isso é do DevOps). Payload usa `schema_version: 1`.
- O Classifier precisa implementar o lado consumidor seguindo os mesmos parâmetros de posse de topologia (não declarar/criar nada).
