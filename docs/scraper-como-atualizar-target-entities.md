# Como atualizar `config/target_entities.yaml`

Este documento é pra ficar no repositório `scrapping-prisma`. Explica como gerar uma versão nova de `config/target_entities.yaml` — a lista de candidatos a presidente/vice-presidente e partidos vinculados que o scraper usa como termo de busca/filtro na coleta.

## O que é esse arquivo

`target_entities.yaml` **não é gerado neste repositório**. Ele vem do `classifier-prisma` (repositório irmão), que é quem tem acesso ao banco (`app_db2`) onde a lista oficial de candidatos vive (`entidade_matching`, importada do TSE). O `scrapping-prisma` não acessa esse banco diretamente — por decisão de arquitetura do projeto, nenhum componente lê o banco interno de outro (ver ADR 0001 do `classifier-prisma`). Por isso o processo é manual: alguém com acesso ao `classifier-prisma` gera o arquivo e ele é copiado pra cá.

## Quando gerar uma versão nova

**Sob demanda, não numa rotina fixa.** A lista muda por evento raro do TSE — troca de vice, nova coligação, candidatura impugnada, desistência — não por tempo. Não faz sentido agendar isso, e não há cron rodando pra isso em nenhum dos dois repositórios.

Gere uma versão nova quando:
- Alguém confirmar que uma candidatura do escopo (presidente ou vice) mudou de verdade.
- Houver suspeita concreta de que a lista está desatualizada (ex.: uma notícia sobre um candidato que não aparece no arquivo).

Não gere "por precaução" ou em intervalo fixo — é trabalho manual sem necessidade real.

## Como gerar

Precisa ter acesso ao repositório `classifier-prisma` e às credenciais do `app_db2` (`.env` de lá, já configurado por quem mantém o Classifier).

```bash
cd caminho/para/classifier-prisma
.venv/bin/python scripts/export_target_entities.py
```

Saída esperada no terminal:

```
Exportado: 26 políticos + 14 partidos = 40 entidades -> .../data/exports/target_entities.yaml
Lembre-se de copiar este arquivo manualmente para scrapping-prisma/config/target_entities.yaml.
```

(Os números podem mudar se a lista de candidatos mudar — o que importa é que os dois números aparecem e batem com o total.)

O script só faz leitura no banco — não altera nada em `app_db2`.

## Como aplicar aqui no scraper

1. Copie o arquivo gerado:
   ```bash
   cp caminho/para/classifier-prisma/data/exports/target_entities.yaml caminho/para/scrapping-prisma/config/target_entities.yaml
   ```
2. Confira o cabeçalho do arquivo copiado — tem `generated_at` (data/hora da geração) e `schema_version: 1`. Se `schema_version` for diferente de `1`, **pare** e confirme com quem mantém o `classifier-prisma` antes de seguir — pode ser um formato novo que este documento ainda não cobre.
3. Rode os testes do scraper que dependem desse arquivo (se existirem) antes de commitar.
4. Commit normal, mencionando o motivo da atualização (ex.: `chore: atualiza target_entities.yaml -- troca de vice do candidato X`).

## Formato do arquivo (referência rápida)

```yaml
generated_at: "2026-08-29T19:29:23Z"    # quando foi gerado
schema_version: 1
source: "classifier-prisma/entidade_matching (TSE 2026, escopo v1: presidente + vice-presidente)"
entities:
  - entity_id: "122418060191"    # chave do TSE (título eleitoral do político, ou número do partido)
    entity_type: politico         # "politico" ou "partido"
    cargo: PRESIDENTE             # "PRESIDENTE" ou "VICE-PRESIDENTE"; null quando é partido
    nome_principal: LUIZ INÁCIO LULA DA SILVA
    aliases:
      - LUIZ INÁCIO LULA DA SILVA
      - LULA
  - entity_id: "13"
    entity_type: partido
    cargo: null
    nome_principal: PARTIDO DOS TRABALHADORES
    aliases:
      - PT
      - PARTIDO DOS TRABALHADORES
```

Use os valores de `aliases` como termos de busca/filtro — são as variações de nome que o Classifier também usa pra reconhecer a entidade no texto, então manter os dois lados na mesma fonte evita que scraper e classifier "procurem" coisas diferentes.

## Se algo der errado

- **Contagem de entidades muito diferente do esperado** (ex.: de repente aparecem 200 em vez de ~40): não copie o arquivo — algo mudou no filtro do lado do Classifier (ex.: escopo da fase mudou de presidente/vice pra outro cargo) e vale confirmar antes de propagar isso pro scraper.
- **`schema_version` diferente de 1**: pare e converse com quem mantém o `classifier-prisma` — o formato pode ter mudado.
- **Dúvida sobre se uma mudança de candidatura é "real" o suficiente pra justificar regenerar**: melhor perguntar do que regenerar sem necessidade ou deixar de regenerar quando precisava.
