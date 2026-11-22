# Dicionário de dados — interface Classifier → Analyser

Documento de referência pra quem for implementar o consumo do Analyser. Cobre as três tabelas que o Analyser precisa conhecer (todas no `app_db2`, o System DB compartilhado da plataforma Prisma) e como consumir os dados que o Classifier produz.

Convenção: colunas marcadas **PK**/**FK** são chave primária/estrangeira; "nullable" indica que a coluna aceita `NULL` de propósito, não por omissão.

---

## 1. `entidade_matching`

Cadastro de entidades (políticos e partidos) que o Classifier reconhece em texto. Fonte de dados: TSE (`consulta_cand_2026`), importado por outro componente da plataforma — o Classifier só lê esta tabela, não escreve nela.

| Coluna | Tipo | Nullable | Descrição |
|---|---|---|---|
| `id` | bigint | não | PK interna, sem significado de negócio. |
| `entity_type` | text | não | `'politico'` ou `'partido'`. Define quais das colunas abaixo são preenchidas. |
| `nr_titulo_eleitoral_candidato` | text | sim | Chave do TSE para o político (título eleitoral). Preenchida só quando `entity_type = 'politico'`. |
| `nr_partido` | integer | sim | Número do partido. Preenchida só quando `entity_type = 'partido'` — **atenção**: em linhas de político, esse campo é sempre `NULL`. Não dá pra saber o partido de um candidato só por esta tabela (ver seção 4). FK pra `tabela_partido(nr_partido)` (adicionada pelo Gustavo/DBA em 2026-08-30, junto com FK de `nr_titulo_eleitoral_candidato` pra `tabela_politico`) — impede entidade "fantasma" sem candidato/partido real correspondente. |
| `nome_principal` | text | não | Nome completo (político) ou nome do partido, em CAIXA ALTA (formato bruto do TSE). |
| `aliases` | jsonb | não | Array de strings — variações de nome/apelido que o `entity_matcher` usa pra reconhecer a entidade no texto (ex.: `["LUIZ INÁCIO LULA DA SILVA", "LULA"]`). |
| `sg_uf` | text | sim | UF do candidato (`'BR'` pra candidatos de cargo nacional, como presidente/vice). |
| `ds_cargo` | text | sim | Cargo disputado (ex.: `'PRESIDENTE'`, `'VICE-PRESIDENTE'`, `'GOVERNADOR'`, `'SENADOR'`...). Preenchida só pra político — partido não tem cargo. |
| `origem` | text | não | De onde veio o dado (ex.: `'tse_2026'`). |
| `ativo` | boolean | não | Se `false`, a entidade não é carregada pelo Classifier — **não confundir com filtro de fase** (ver nota abaixo). |
| `criado_em` / `atualizado_em` | timestamptz | não | Auditoria de quando a linha foi criada/alterada. |

**Nota sobre escopo (fase v1, decisão de 2026-08-28)**: o Classifier hoje só carrega o subconjunto de `entidade_matching` com `ds_cargo IN ('PRESIDENTE', 'VICE-PRESIDENTE')` (26 políticos) + os partidos desses candidatos (14 partidos, resolvidos via `tabela_candidatura`, ver seção 4). Isso é um filtro de leitura no código do Classifier (`config/settings.yaml`, `entity_scope.cargos`) — **a tabela em si continua com as ~1.393 entidades completas**, `ativo=true` não muda de significado. Se o Analyser também consultar `entidade_matching` diretamente, uma linha `ativo=true` não implica que o Classifier está processando aquela entidade agora — só implica que ela está disponível no cadastro.

---

## 2. `tabela_classificacao`

Resultado da classificação: uma linha por (parágrafo, entidade citada nele). É o produto principal do Classifier — o Analyser deve tratar esta tabela como fonte de verdade dos resultados.

| Coluna | Tipo | Nullable | Descrição |
|---|---|---|---|
| `id_classificacao` | integer | não | PK, auto-incremento. |
| `id_artigo_scrape` | bigint | sim | ID do artigo no `scrapping-prisma` (`article_id` do payload original). |
| `paragrafo_analisado` | text | sim | Texto do parágrafo onde a entidade foi identificada (evidência). |
| `link_noticia` | text | sim | URL canônica da notícia. |
| `nr_titulo_eleitoral_candidato` | varchar | sim | Preenchida quando a entidade classificada é um **político** (FK lógica pra `entidade_matching`/`tabela_politico`) — `NULL` quando é partido. |
| `nr_partido` | integer | sim | Preenchida quando a entidade classificada é um **partido** (FK lógica pra `tabela_partido`) — `NULL` quando é político. `entidade_matching.nr_partido` também é `integer` desde 2026-08-30 (corrigido pelo Gustavo/DBA, era `text` antes) — os dois batem no tipo agora, sem precisar de cast pra cruzar. |
| `id_midia` | integer | sim | FK pra `tabela_midia`. Resolvida por um lookup de nome (`source_name` do payload → `tabela_midia.nome_midia`); fica `NULL` quando não encontra correspondência — **não é garantia de que sempre virá preenchido**. |
| `classificacao_sentimento` | varchar | sim | Um de `'positivo'`, `'negativo'`, `'neutro'` — heurística léxica v1 (não é modelo de ML), ver `src/lexicon.py`. Não existe hoje um valor tipo "não relacionado" nesta coluna: se a entidade não foi citada no parágrafo, simplesmente não existe linha. |
| `score_confianca` | double precision | sim | 0.0–1.0. Para a heurística léxica atual: `\|positivos − negativos\| / (positivos + negativos)`; `0.0` quando `classificacao_sentimento = 'neutro'` por ausência de termos do léxico (não é "baixa confiança", é "sem evidência textual"). |
| `data_publicacao_noticia` | timestamp (sem timezone) | sim | Data de publicação original da notícia (vem do scraper). |
| `registro_classificacao` | timestamp (sem timezone) | não | **Preenchida automaticamente pelo banco** (`DEFAULT CURRENT_TIMESTAMP`) — não precisa (nem deve) ser passada explicitamente em `INSERT`. Quando a linha foi gravada, não quando a notícia foi publicada. |
| `metodo_classificacao` | varchar | sim | Identifica o método/versão do classificador (ex.: `"lexicon-baseline-v1"`). |
| `pipeline_version` | text | não | Versão do pipeline de processamento (vem do payload do scraper) — parte da chave de idempotência. |
| `evidencia_match` | jsonb | sim | Auditoria de como a entidade foi reconhecida no texto: `{"tipo": "exato"\|"aproximado", "score": 0.0-1.0, "alias": "texto que bateu"}`. |

**Idempotência**: `UNIQUE (id_artigo_scrape, paragrafo_analisado, nr_titulo_eleitoral_candidato, nr_partido, pipeline_version)` (constraint `uq_tabela_classificacao_idempotencia`) — reentrega da mesma mensagem do scraper não duplica linha (`INSERT ... ON CONFLICT DO NOTHING`).

**Granularidade**: um parágrafo com duas entidades diferentes gera duas linhas (uma por entidade), cada uma com o **mesmo** `paragrafo_analisado` e `classificacao_sentimento` (a classificação de sentimento é por parágrafo inteiro, não por entidade — limitação conhecida da v1, ver `src/lexicon.py`).

---

## 3. `classifier_analyser_outbox`

Tabela de uso **interno** do Classifier — não faz parte do modelo de dados compartilhado (por isso não segue o padrão `tabela_*`). Existe pra mitigar o risco de uma notificação ao Analyser se perder se o RabbitMQ estiver fora do ar na hora de publicar. **O Analyser não deveria precisar ler esta tabela diretamente** — ela é drenada por um publisher próprio do Classifier que republica no RabbitMQ. Documentada aqui só pra contexto, caso apareça em alguma consulta exploratória do banco.

Ver [`docs/adr/0004-outbox-proprio-para-notificacao-analyser.md`](adr/0004-outbox-proprio-para-notificacao-analyser.md) para o raciocínio completo da decisão (supera parcialmente a ADR 0003, que fazia publicação direta e síncrona sem outbox).

| Coluna | Tipo | Nullable | Descrição |
|---|---|---|---|
| `id` | bigserial | não | PK interna. |
| `id_artigo_scrape` | bigint | não | Mesmo artigo referenciado em `tabela_classificacao`. |
| `pipeline_version` | text | não | Idem. |
| `payload` | jsonb | não | Payload já pronto (mesmo formato da seção 4) — gravado no momento da classificação, publicado depois. |
| `status` | text | não | `'pending'` → `'processing'` → `'notified'` (sucesso) ou `'failed'` (esgotou tentativas) ou `'cancelled'`. |
| `attempts` / `max_attempts` | integer | não | Contador de tentativas de publicação / limite (default 3). |
| `scheduled_at` | timestamptz | não | Quando deve ser tentada a próxima publicação. |
| `notified_at` | timestamptz | sim | Quando foi publicada com sucesso — `NULL` enquanto pendente. |
| `error_message` | text | sim | Último erro de publicação, se houver. |
| `created_at` / `updated_at` | timestamptz | não | Auditoria (atualizado automaticamente por trigger). |

**Status desta tabela (2026-08-29, atualizado)**: implementada e em uso. `src/message_handler.py` grava aqui o payload de notificação (mesmo formato da seção 4) NA MESMA TRANSAÇÃO que grava `tabela_classificacao`, antes do commit (`src/notifications_store.py::enqueue_notification`). Um processo separado, `src/notify_analyser.py` (rodando uma vez e saindo, agendável via cron — via `src/notification_publisher.py`), drena as linhas `pending` e publica de fato no RabbitMQ, com retry (`attempts`/`max_attempts`) e circuit breaker de falhas consecutivas. A notificação ao Analyser deixou de ser publicação direta e síncrona (ver ADR 0003, agora superada nesse ponto pela ADR 0004).

---

## 4. Como o Analyser deve consumir esses dados

Duas fontes, dois propósitos diferentes:

### 4.1. RabbitMQ — "algo novo foi classificado" (gatilho, não dado completo)

O Classifier publica uma mensagem no RabbitMQ **depois de confirmar (commitar)** a gravação em `tabela_classificacao` — nunca antes, pra nunca notificar algo que não foi salvo de verdade.

- **Exchange**: `classifier.saida.exchange` (tipo `direct`) — **valor placeholder, ainda não confirmado com o DevOps** (mesmo tratamento que a fronteira Scraper→Classifier teve, ver ADR 0001).
- **Fila**: `classifier.notificacoes.queue` — idem, não confirmado.
- **Payload** (formato **proposto, não é contrato fechado** — ver `docs/adr/0003-notificacao-analyser-publicacao-direta.md`):

```json
{
  "schema_version": 1,
  "article_id": 12345,
  "job_id": 987,
  "pipeline_version": "lexicon-baseline-v1",
  "link_noticia": "https://...",
  "data_publicacao_noticia": "2026-08-20T10:00:00+00:00",
  "notificado_em": "2026-08-28T14:32:10+00:00",
  "classificacoes": [
    {
      "entity_type": "politico",
      "entity_id": "122418060191",
      "paragraph_index": 3,
      "classificacao_sentimento": "positivo",
      "score_confianca": 0.6
    }
  ]
}
```

O payload é **leve de propósito** — não duplica o texto do parágrafo nem todos os campos de `tabela_classificacao`. `entity_id` é `nr_titulo_eleitoral_candidato` (quando `entity_type = 'politico'`) ou `nr_partido` (quando `entity_type = 'partido'`), na mesma convenção da própria `tabela_classificacao`.

**Uso esperado**: o Analyser trata a mensagem como um "avise que há coisa nova pro artigo X" e, se precisar do texto do parágrafo, evidência de match ou qualquer outro campo, **consulta `tabela_classificacao` direto** (mesmo banco, `app_db2` — não precisa passar por API nem replicar dado) filtrando por `id_artigo_scrape` + `pipeline_version` (+ `paragraph_index`, se quiser a linha exata em vez de todas do artigo).

**Falha de entrega**: desde a ADR 0004, se o RabbitMQ estiver fora do ar no momento da publicação, a notificação NÃO se perde — fica registrada em `classifier_analyser_outbox` (seção 3) com status `pending`/`failed` e é retentada por um processo separado (`src/notify_analyser.py`, agendável via cron), com retry por tentativas e circuit breaker. Ainda assim, o Analyser não deveria depender *só* da fila pra saber o que processar — a fila é gatilho de baixa latência, não garantia de entrega imediata (pode haver atraso entre a classificação ser persistida e a notificação ser de fato publicada, se o outbox estiver represado) — ver 4.2 para a rede de segurança via Postgres direto.

### 4.2. Postgres direto — fonte de verdade, reconciliação e catch-up

Como `app_db2` é um banco compartilhado por desenho (diferente da fronteira Scraper↔Classifier, que é isolada por RabbitMQ — ver ADR 0002), o Analyser pode e deve ler `tabela_classificacao` diretamente para:

- **Catch-up**: caso perca uma notificação (RabbitMQ fora do ar) ou fique fora do ar por um tempo, uma rotina periódica pode varrer `tabela_classificacao WHERE registro_classificacao > <último processado>` pra não depender só da fila.
- **Detalhe completo**: parágrafo, `evidencia_match`, timestamps — tudo que o payload da fila propositalmente não carrega.
- **Join com entidade**: pra saber nome/partido de quem foi classificado, junta `tabela_classificacao.nr_titulo_eleitoral_candidato`/`nr_partido` com `entidade_matching` (ou diretamente com `tabela_politico`/`tabela_partido`, se preferir os dados brutos do TSE em vez do cadastro do Classifier).

**Recomendação prática**: usar RabbitMQ como gatilho de baixa latência (processa assim que chega) e uma consulta periódica em `tabela_classificacao` como rede de segurança (garante que nada fica pra trás por falha de notificação) — o mesmo raciocínio de "notificação é aviso, banco é verdade" que já vale pra fronteira Scraper→Classifier.

---

## Pendências que afetam este contrato

- Nome de exchange/fila/routing key da fronteira Classifier→Analyser: **não confirmado com o DevOps**.
- ~~Formato do payload da fila (seção 4.1): proposta, precisa validação de quem for implementar o consumidor.~~ **✅ RESOLVIDO (2026-08-29)**: decisão da Bea — o modelo de dados do Classifier (este documento, `tabela_classificacao` + payload da seção 4.1) é a referência fixa. O protótipo do Analyser lido nesta data espera um formato de entrada bem diferente (arquivo JSON agrupado por ator, com item por notícia) — **quem constrói o Analyser é responsável por adaptar o consumo pro formato daqui**, não o contrário. Este repositório não muda nada em função do formato de entrada do Analyser.
- Mapeamento `source_name` (do scraper) → `tabela_midia.nome_midia`: pode deixar `id_midia` como `NULL` em `tabela_classificacao` se os nomes não baterem — **medido em 2026-08-29 contra dado real**: só 33,5% dos artigos coletados batem com os 10 veículos hoje cadastrados (a maioria das fontes reais do scraper simplesmente não está cadastrada; outra parte vem como domínio, ex. `g1.globo.com`, em vez do nome cadastrado `G1`). Não bloqueia nada (`id_midia` é opcional), mas fica registrado como limitação conhecida até alguém decidir investir em cadastrar mais veículos e/ou melhorar o lookup.
- `classifier_analyser_outbox` (seção 3): implementada e em uso (ver ADR 0004) — agendamento de `src/notify_analyser.py` em produção fica por conta da infra (Anderson, via Gitea/CronJob) — não é mais pendência deste lado.
