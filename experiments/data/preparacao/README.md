# Amostra provisória para revisão

Bea decidiu manter as 60 notícias atuais, usando o CSV disponível `data/raw/articles_202608191040.csv`, de 19/08/2026. A proposta em [`../preparacao-revisada-20261112/`](../preparacao-revisada-20261112/) contém 60 IDs únicos e 90 atribuições; permanece **PROVISÓRIA**, com `scope_review` **PENDENTE** como registro do gerador. Bea decidiu não substituir candidatos nem corrigir textos nesta rodada; as limitações estão aceitas e não tornam a amostra um gabarito ou split final.

Limitações aceitas nesta rodada: sete notícias com foco fora da lista (`445, 110, 325, 358, 354, 333, 390`); ID `306` ambíguo; cinco casos de foco misto (`408, 435, 406, 418, 457`). O ID `373` trata de convenção do PT, que está no escopo. Alertas de integridade: `178` contém bloco repetido junto de `445`; `139` tem texto interrompido e reiniciado; `57` e `501` têm mojibake; `220` contém lista “Mais lidas”. Nada foi corrigido ou excluído. As recomendações futuras estão em [`data-quality-improvements.md`](data-quality-improvements.md). A anotação ainda não começou; não há planilhas definitivas, gabarito ou split final.

## Origem e exclusões

O CSV de 19/08/2026 contém 540 registros, dos quais 472 têm extração bem-sucedida. A execução isolada do código e das configurações do commit `fb85d8d933d7d42edac287af98a6b951f041884f` recuperou os 471 artigos elegíveis da rodada 1. O prefixo de 150 IDs sorteados com semente 42 coincidiu exatamente com os IDs de `data/annotation/manifest.csv`. Os 321 restantes são, portanto, reconstruíveis. Os hashes das seis fontes históricas estão em `historical_eligibility.json`.

Usar as configurações atuais para essa reconstrução daria 463 elegíveis; três notícias do manifesto deixariam de ser elegíveis. Por isso, `historical_eligible_ids.txt` preserva a elegibilidade histórica.

Das 321 reservadas, saíram quatro notícias do piloto: 146, 159, 160 e 175. A quinta, 145, já pertence à rodada 1. A deduplicação retirou também a 200, duplicata da 190 da rodada 1; a 243, duplicata da 1; e a 308, duplicata da 301. Restaram 314 notícias independentes segundo os critérios automáticos adotados.

A deduplicação agrupa transitivamente IDs que compartilham URL canônica ou texto completo. URLs ignoram esquema, fragmento, barra final e parâmetros conhecidos de rastreamento. Textos são comparados após normalização Unicode, caixa e espaços. Não detecta reescritas, resumos ou republicações com alterações no conteúdo; esses casos precisam de revisão humana.

## Seleção e atribuição

A seleção usa embaralhamento com semente 42 sobre os representantes ordenados dos grupos, sem cotas por veículo, candidato ou tamanho. Não escolhe notícias a partir de rótulos de teor. O representante de cada grupo é o menor ID em ordem lexicográfica.

São seis notícias compartilhadas pelos seis anotadores e 54 exclusivas, nove para cada pessoa. Cada lista individual tem 15 notícias; `assignments.csv` contém 90 atribuições. Os nomes são Anderson, Beatriz, Cristovam, Gustavo, Lucas e Nicolas. As seis compartilhadas não aparecem no conjunto das exclusivas.

`candidates.csv` registra veículo, URL, hash do texto, tamanho em caracteres, número de parágrafos, compartilhamento e estado provisório. `metadata.json` contém as contagens por veículo, distribuição de tamanhos, hashes das entradas e saídas e informações do snapshot. Os nomes dos veículos são os da fonte; por exemplo, `G1` e `g1.globo.com` permanecem separados.

O snapshot histórico usado na seleção foi gerado em **29/08/2026 às 19:29:23 UTC**, com 40 entidades e 73 aliases explícitos. Ele foi mantido para preservar a reprodução da seleção e de `metadata.json`. Um snapshot separado foi gerado em `experiments/data/entidades.yaml` em **10/11/2026**, a partir de `prisma-dev`, em modo somente leitura. Também contém 40 entidades e 73 aliases, com conteúdo coincidente com o snapshot de agosto. `snapshot-audit.json` registra origem, contagens e hash. A revalidação não reescreveu os CSVs de seleção nem seus metadados.

## Revisão humana do escopo

`candidate-revalidation.json` registra a revalidação automática da seleção original. A proposta mantida por Bea está em [`../preparacao-revisada-20261112/`](../preparacao-revisada-20261112/). O `scope_review` permanece PENDENTE; essa marca registra a revisão automática e não revoga a decisão de aceitar as limitações da rodada. Não substituir as sete candidatas fora do escopo nem corrigir os textos atuais.

Cinco casos de foco misto aceitos como limitação nesta rodada: `408` (compartilhada; Tarcísio e cobertura substancial de Flávio), `435` (Nicolas; entrevista de Tarcísio com seção sobre Flávio/Lula), `406` (Gustavo), `418` (Nicolas; empréstimo de SP e debate sobre governos Lula/Flávio) e `457` (Anderson; apoio a Flávio no título e debate estadual no corpo). `373` trata de convenção do PT, partido que está no escopo.

Próxima etapa: gerar seis planilhas, uma para cada anotador, com os 15 IDs do respectivo arquivo `ids_<nome>.txt` na pasta da proposta. Use `experiments/gold.py gerar`, o CSV `data/raw/articles_202608191040.csv` e o snapshot `experiments/data/entidades.yaml`. Não substituir candidatos nem alterar textos desta rodada. Após gerar as planilhas, não corrigir texto, pois isso mudaria offsets. `scope_review` permanece PENDENTE como registro do gerador; a anotação ainda não começou.

## Reproduzir e verificar

Na raiz do repositório, com as dependências existentes instaladas:

```sh
.venv/bin/python experiments/prepare_data.py
.venv/bin/python -m pytest -q tests/experiments/test_prepare_data.py
```

O primeiro comando regenera os CSVs, listas e metadados desta pasta. O segundo verifica contagens, atribuições, exclusões por identidade e duplicação transitiva, ausência de IDs de origem, pool insuficiente e reprodução dos arquivos sem rótulos ou split. Não acessam banco nem alteram o conjunto anotado.

Na geração histórica desta amostra, quatro testes passaram. A auditoria dos arquivos confirmou 60 IDs únicos, seis compartilhadas, nove exclusivas por anotador e ausência de coincidência de IDs, URLs canônicas e hashes de texto com a rodada 1 e o piloto. Uma segunda execução reproduziu os arquivos byte a byte, inclusive os metadados. A amostra tem entre 555 e 8.505 caracteres por notícia, com mediana de 3.059. A revalidação posterior com o snapshot de `prisma-dev` é separada e não altera essa proveniência.

Gerar as seis planilhas por anotador com `gold.py gerar`, usando os 15 IDs de cada `ids_<nome>.txt`, o CSV de 19/08 e o snapshot de `prisma-dev`. Confirmar disponibilidade dos anotadores. Bea executará o comando fornecido e trará a saída para conferência. Esta amostra não constitui gabarito consensual ou split congelado.
