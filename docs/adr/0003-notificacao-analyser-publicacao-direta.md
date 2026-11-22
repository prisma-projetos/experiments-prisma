# ADR 0003 — Notificação Classifier → Analyser: publicação direta, sem outbox no `app_db2`

**Status**: Aceito (28/08/2026) — supersede parcialmente a ADR 0002 (mantém a decisão de RabbitMQ como transporte; substitui o mecanismo de garantia de entrega)

## Contexto

A ADR 0002 previa outbox transacional também na fronteira Classifier → Analyser: gravar "precisa notificar" na mesma transação do resultado (tabela `analyser_notifications`), com um publisher separado (`src/notify_analyser.py`) drenando essa tabela com retry.

Duas mudanças de contexto invalidaram essa implementação concreta (não a intenção por trás dela):

1. O Classifier migrou de um schema próprio (`classification_runs`/`classifications`/`analyser_notifications`, migrations deste repositório) para gravar em `tabela_classificacao`, no System DB compartilhado `app_db2` — schema e migrations gerenciados por outra pessoa da equipe (ver ADR 0002). `app_db2` não tem hoje um equivalente a `analyser_notifications`, e criar um ali é uma decisão de schema compartilhado que este repositório não pode tomar sozinho.
2. Decisão da Bea (2026-08-28): "o envio da classificação pro Analyser vai ser feito a princípio igual o scraper pro classificador, por meio do RabbitMQ" — ou seja, o mesmo padrão simples de produtor/consumidor já usado na fronteira Scraper → Classifier (ver ADR 0001), sem outbox intermediário.

## Decisão

- O Classifier publica a notificação **diretamente** no RabbitMQ logo depois de persistir E COMITAR o resultado em `tabela_classificacao` — nunca antes do commit (mesma garantia de ordem que a ADR 0002 já exigia, só que sem outbox no meio).
- Implementado em `src/analyser_notifier.py` (payload) + `src/message_handler.py` (orquestração: persiste, comita, só então notifica) + `src/rabbitmq_publisher.py` (reaproveitado — infraestrutura de conexão/publicação já existente, construída para o outbox antigo, mas genérica o suficiente para publicação síncrona).
- **Falha de publicação não rejeita a mensagem**: como a classificação já foi persistida e commitada no momento da tentativa de publicação, uma falha aqui (RabbitMQ fora do ar, por exemplo) é logada como erro e o processamento da mensagem é considerado concluído (ack) — não há retry nem DLQ para a notificação em si. **Risco aceito explicitamente**: uma notificação pode ser perdida silenciosamente se o RabbitMQ estiver indisponível exatamente no momento da publicação. Mitigação futura possível (não implementada agora): job de reconciliação que compare `tabela_classificacao` com algum registro de "já notificado" — depende de decisão do dono do `app_db2` sobre se vale a pena adicionar essa coluna/tabela ao schema compartilhado.
- `src/notify_analyser.py`, `src/notification_publisher.py` e `src/notifications_store.py` (implementação do outbox antigo) ficam **órfãos** — não apagados nesta mudança (decisão de limpeza maior, fora do escopo desta tarefa), mas não fazem mais parte do fluxo de produção. Recomendação registrada: remover ou arquivar quando alguém tiver tempo de confirmar que não há uso remanescente.
- Reaproveitadas as variáveis de ambiente já existentes para esta fronteira (`RABBITMQ_NOTIFIER_USER`, `RABBITMQ_NOTIFIER_PASSWORD`, `RABBITMQ_NOTIFIER_EXCHANGE`, `RABBITMQ_NOTIFIER_EXCHANGE_TYPE`, `RABBITMQ_NOTIFIER_QUEUE`, `RABBITMQ_NOTIFIER_ROUTING_KEY`, `RABBITMQ_NOTIFIER_DURABLE`) — nenhuma variável nova foi criada; `RABBITMQ_HOST`/`RABBITMQ_PORT`/`RABBITMQ_VHOST` continuam compartilhadas com o consumidor.

## Contrato de payload (PENDENTE DE VALIDAÇÃO)

`src/analyser_notifier.py::build_notification_payload` monta um payload com `article_id`, `job_id`, `pipeline_version`, `link_noticia`, `data_publicacao_noticia` e uma lista `classificacoes` (entidade, tipo, parágrafo, categoria, score) — baseado só nas colunas que `tabela_classificacao` já tem.

Isso é uma **proposta**, não um contrato fechado — igual ao aviso já existente em `src/rabbitmq_publisher.py` sobre fila/exchange/routing key não confirmados com o DevOps, o **formato da mensagem também precisa ser validado com quem for implementar o consumidor do lado do Analyser** antes de virar contrato de produção. Não é uma decisão que um repositório sozinho pode fechar.

## Consequências

- Pendente: confirmar com o time do Analyser o formato exato do payload.
- Pendente: confirmar com o DevOps o nome de fila/exchange/routing key desta fronteira (mesma pendência já registrada na ADR 0002, ainda não resolvida).
- Pendente: decidir o destino de `src/notify_analyser.py` e módulos relacionados (arquivar/remover) depois que a equipe confirmar que o padrão outbox não será revivido no curto prazo.
- Risco aceito e documentado: perda silenciosa de notificação em caso de indisponibilidade do RabbitMQ no momento da publicação (ver seção "Decisão" acima).
