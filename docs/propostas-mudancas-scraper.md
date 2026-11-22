# Propostas de mudança para o `scrapping-prisma`

Documento de trabalho, escrito do lado do Classifier, com achados da anotação manual e decisões recentes que afetam o scraper. Não é um contrato fechado — é uma proposta pra discutir com quem mantém o `scrapping-prisma`. Onde eu não tenho certeza (principalmente sobre o código do scraper, que não faz parte deste repositório), marco explicitamente como hipótese.

---

## 1. Corrupção de caracteres (mojibake) no texto coletado

### O que encontramos

Durante a anotação manual, apareceram nomes e palavras com acentuação quebrada (ex.: `TarcÃsio` em vez de `Tarcísio`). Fui conferir no dado bruto pra não repetir isso de memória — é real e sistemático, não um caso isolado:

- **49 de 540 artigos** (`data/raw/articles_202608191040.csv`) têm pelo menos uma ocorrência do padrão — **9,1% do corpus**.
- Não é só nome próprio. Palavras comuns do português também quebram: `nÃ£o` (não, 152x), `tambÃ©m` (também, 76x), `estÃ¡` (está, 32x), `jÃ¡` (já, 29x), `atÃ©` (até, 25x), `FlÃ¡vio` (Flávio, 117x), `SÃ£o` (São, 77x).

### Hipótese de causa (não confirmada — preciso olhar o código do scraper pra ter certeza)

O padrão (`ã` virando `Ã£`, `á` virando `Ã¡`, `é` virando `Ã©`) é a assinatura clássica de **double encoding**: um texto que já estava em UTF-8 foi decodificado como se fosse Latin-1 (ISO-8859-1) em algum ponto, e depois regravado como UTF-8 — cada caractere acentuado UTF-8 (2 bytes) vira 2 caracteres Latin-1 errados.

Isso geralmente acontece quando o código que baixa a página HTTP não respeita o charset real da resposta — exemplos comuns (preciso confirmar qual se aplica aqui, olhando o código de coleta):
- Biblioteca de request assume um charset padrão (ex.: Latin-1) quando o cabeçalho HTTP `Content-Type` não declara `charset=utf-8` explicitamente, mesmo a página sendo UTF-8 de fato (isso é um comportamento conhecido de algumas bibliotecas HTTP em Python quando não se força a detecção correta).
- A página declara um charset diferente do que realmente usa (site mal configurado) e o scraper confia cegamente na declaração.

### Por que isso importa pro Classifier (e pro resto do pipeline)

Confirmei no código: o Classifier **não faz nenhum tratamento de encoding** no texto que recebe (`src/payload.py`/`src/segmentation.py` tratam `full_text` como string já pronta). Ou seja, se o texto chega corrompido do scraper, ele **permanece corrompido** em todo o resto do pipeline — no parágrafo salvo em `tabela_classificacao`, na notificação pro Analyser, potencialmente na comparação de nome de entidade (o `entity_matcher` já teve que lidar com isso: 49 ocorrências de `TarcÃsio` causaram desempate errado de alias, ver `data/annotation/pendencias-tecnicas.md`).

**Recomendação**: corrigir na fonte (scraper), não tentar remendar no Classifier. Remendar aqui exigiria adivinhar quando um texto está corrompido (heurística frágil, vai ter falso positivo/negativo) — o scraper sabe exatamente de onde veio o byte original, é o lugar certo pra garantir o charset certo na hora de decodificar a resposta HTTP.

---

## 2. Uma "tabela de entidades" também no scraper? Minha opinião

Você perguntou se acho que vai precisar. Acho que sim, mas não do jeito mais óbvio (copiar a tabela inteira). Explico o raciocínio:

Com o faseamento (seção 3), o scraper precisa saber **quem procurar** — nomes de candidato/partido pra usar como termo de busca ou filtro. Isso significa que o scraper também precisa conhecer, de alguma forma, o mesmo conjunto de entidades que o Classifier usa (26 candidatos a presidente/vice + 14 partidos, hoje).

O que eu **não recomendo**: o scraper acessar `entidade_matching`/`app_db2` diretamente. Isso quebraria uma regra que este projeto já decidiu com cuidado em outro lugar (`context.md` raiz, seção 19.2): nenhum componente acessa direto o banco interno de outro — o `Scraper DB` e o `System DB` (`app_db2`) são mundos propositalmente separados, e essa separação foi defendida explicitamente na ADR 0001 (Scraper→Classifier vai por RabbitMQ, nunca banco direto). Furar essa regra pro caso do scraper ler `app_db2` ia na contramão do que o projeto já decidiu.

O que eu **recomendo**: o scraper ter sua própria lista pequena (nomes/aliases dos 26 candidatos + 14 partidos), mas essa lista **derivada da mesma fonte** que o Classifier usa (TSE + `ds_cargo IN ('PRESIDENTE', 'VICE-PRESIDENTE')`) — não uma curadoria manual paralela. Como fazer isso na prática, três opções (preciso da sua decisão, ou de quem mantiver o scraper):

1. **Export periódico**: o Classifier (ou quem tiver acesso ao `app_db2`) gera um arquivo (JSON/CSV) com a lista atual e alguém coloca isso onde o scraper lê (repositório, bucket, o que for mais simples). Baixo acoplamento, mas alguém precisa lembrar de regerar quando a lista mudar.
2. **Endpoint de leitura**: alguém expõe uma consulta somente-leitura (view, API pequena) que o scraper chama pra pegar a lista atualizada. Mais trabalho de implementar, mas nunca fica desatualizado.
3. **Lista manual duplicada no scraper**: eu **não recomendo** essa opção — foi exatamente o problema que a gente acabou de resolver aqui (curadoria manual divergindo do dado real do TSE). Se o scraper mantiver sua própria lista sem vínculo com a fonte, as duas listas vão divergir cedo ou tarde (troca de vice, nova coligação, etc.) — e ninguém vai perceber até um candidato sumir da cobertura.

Meu palpite, sem forçar: a opção 1 (export periódico simples) resolve o problema real com o menor esforço, dado que a lista muda pouco (é uma eleição, não atualiza todo dia). Mas quem decide isso com propriedade é quem for implementar o lado do scraper.

### Atualização (2026-08-29): formato decidido e export implementado

A opção 1 foi escolhida e implementada. `scripts/export_target_entities.py` conecta em `app_db2` (só leitura), reaproveita `entities_store.load_active_entities_from_db` (mesmo filtro v1 já em produção) e escreve `data/exports/target_entities.yaml` -- 40 entidades hoje (26 políticos + 14 partidos), validado contra o banco real.

Formato do YAML (`schema_version: 1`):

```yaml
generated_at: "<timestamp ISO 8601 UTC>"
schema_version: 1
source: "classifier-prisma/entidade_matching (TSE 2026, escopo v1: presidente + vice-presidente)"
entities:
  - entity_id: "<nr_titulo_eleitoral_candidato ou nr_partido, como string>"
    entity_type: "politico"  # ou "partido"
    cargo: "PRESIDENTE"  # ou "VICE-PRESIDENTE"; null quando entity_type == "partido"
    nome_principal: "<nome_principal de entidade_matching>"
    aliases: ["<cada alias>"]
```

**Cadência: geração sob demanda, não agendada.** A lista muda por evento raro do TSE (troca de vice, nova coligação, impugnação), não por tempo -- não faz sentido um cron regerando isso todo dia. Rodar `scripts/export_target_entities.py` de novo (e copiar o arquivo pro `scrapping-prisma`) quando: (a) uma candidatura do escopo v1 mudar de fato, ou (b) alguém desconfiar que a lista pode estar desatualizada. Quem mantém `scrapping-prisma` copia manualmente `data/exports/target_entities.yaml` (deste repositório) para `config/target_entities.yaml` (lá) -- não há automação entre os dois repositórios, de propósito (baixo acoplamento, ver opção 1 acima).

**Decisão de implementação**: `Entity` (`src/entities_store.py`) não carrega `ds_cargo` -- `src/entity_matcher.py` nunca precisou desse campo em produção. Em vez de alterar `load_active_entities_from_db` (função usada em produção, risco desnecessário para uma necessidade só do export), o script faz uma segunda query pequena e isolada (`load_cargo_by_titulo`, dentro do próprio script) buscando `ds_cargo` pelos ids de político já carregados -- mesmo espírito de `load_real_entities_full_scope` em `scripts/benchmark_entity_matcher.py` (leitura extra isolada no script, sem tocar em `src/entities_store.py`).

O arquivo gerado NÃO é versionado neste repositório (`data/exports/` está no `.gitignore`) -- é um artefato regenerável, versionar geraria diff a cada execução (`generated_at` muda sempre) sem valor real.

---

## 3. Faseamento: raspar só notícia de presidente/vice + partidos vinculados

Decisão já tomada pela equipe (2026-08-28): a v1 do Classifier processa só candidatos a presidente/vice-presidente e os partidos deles — não o universo inteiro de políticos. Pra essa fase fazer sentido de ponta a ponta, o scraper também precisa filtrar (ou pelo menos priorizar) a coleta pra esse mesmo recorte — senão uma fração grande do que for raspado nunca vai gerar classificação nenhuma (não é bug, é escopo, mas dá a impressão de sistema quebrado se ninguém souber que é assim de propósito).

**Ponto crítico, já registrado por dois agentes independentes nesta sessão**: se o scraper definir "quem é presidenciável" com um critério próprio, diferente do critério do Classifier (`ds_cargo` do TSE), as duas listas podem divergir. Recomendação: os dois usarem o **mesmo critério de origem** (TSE, `ds_cargo IN ('PRESIDENTE', 'VICE-PRESIDENTE')`, partido via vínculo de candidatura) — não duas definições independentes de "presidenciável". Isso conecta direto com a seção 2: a lista que o scraper usa pra filtrar/buscar deveria ser a mesma exportada/consultada dali.

**O que ainda não está definido** (fora do que eu posso decidir sozinho):
- Se o filtro no scraper é na *busca* (só procurar notícia mencionando esses nomes) ou na *coleta* (coletar tudo, descartar depois do que não menciona ninguém do escopo) — têm implicações de custo/cobertura diferentes.
- O que fazer com notícia que menciona candidato E outro político fora do escopo no mesmo texto (ex.: matéria sobre debate com vários candidatos, incluindo governador) — descartar a notícia inteira, ou coletar mesmo assim e deixar o Classifier simplesmente não gerar linha pra quem está fora do escopo? Essa segunda opção é o que já acontece hoje no Classifier (sem ação nenhuma do scraper), então pode ser o caminho mais simples se o volume de coleta não for um problema.

---

## Resumo / checklist

| Item | Ação recomendada | Quem decide |
|---|---|---|
| Mojibake (9,1% dos artigos) | Investigar decodificação de charset na coleta HTTP do scraper | Quem mantém `scrapping-prisma` |
| Lista de entidades pro scraper | ✅ Implementado (2026-08-29): `scripts/export_target_entities.py` gera `data/exports/target_entities.yaml` (40 entidades), copiar manualmente pro `scrapping-prisma` | Quem mantiver o scraper copia o arquivo |
| Faseamento da coleta | Scraper filtrar/priorizar por presidente/vice + partidos, usando o mesmo critério (`ds_cargo`) do Classifier | Bea + quem mantiver o scraper |
| Notícia com entidade fora de escopo junto | Definir se descarta a notícia ou deixa o Classifier ignorar a parte fora de escopo (mais simples) | A decidir |
