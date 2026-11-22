# Plano de implementação dos experimentos do artigo

Plano para implementar o que o documento "PRISMA: plano de testes e assuntos para pesquisar" pede e chegar às tabelas do artigo. Escrito em 26/10/2026, a partir do código da `develop` (`4e273b9`).

Para um resumo de retomada entre sessões/modelos, consulte [`CONTINUIDADE-EXPERIMENTOS.md`](CONTINUIDADE-EXPERIMENTOS.md).

Tudo fica em `experiments/`. O `docker/Dockerfile` só copia `src/` e `config/`, então nada dessa pasta entra na imagem de produção, e as dependências de ML (torch, transformers, scikit-learn) ficam num `experiments/requirements.txt` separado.

## Situação em 12/11/2026

**Fase atual: gerar as planilhas de anotação da amostra mantida.** Bea decidiu manter as 60 notícias atuais como estão: não substituir candidatas nem corrigir textos nesta rodada. A proposta em [`experiments/data/preparacao-revisada-20261112/`](../experiments/data/preparacao-revisada-20261112/) contém 60 IDs únicos e 90 atribuições; está **PROVISÓRIA** e `scope_review` permanece **PENDENTE** como registro do gerador. As limitações de escopo e integridade foram aceitas para esta rodada e estão documentadas em [`experiments/data/preparacao/data-quality-improvements.md`](../experiments/data/preparacao/data-quality-improvements.md). A anotação ainda não começou; não há gabarito consensual nem split final.

| Frente | Estado em 12/11 | Verificação/pendência |
|---|---|---|
| Gabarito, métricas, menções, concordância, léxico e TF-IDF (`gold.py`, `metrics.py`, `mentions.py`, `agreement.py`, `teor.py`, `tfidf.py`) | Implementados; TF-IDF disponível somente no ambiente isolado. | 77 testes passaram com `.venv-experiments/bin/python -m pytest tests/experiments -q` (1,11 s). CLI e fluxo TF-IDF sintético com predição simulada foram verificados; não houve treino real com o gabarito final. O snapshot teve 25 testes de preparação/auditoria na execução informada. No piloto, as menções cobriram 92 parágrafos com offsets íntegros; em `145-6`, a recência liga “ele” a Lula, preservando o desacordo com a resposta humana de Flávio. |
| Concordância do piloto (`agreement.py`) | Relatório descritivo gerado em `experiments/results/piloto-concordancia/`. | Bootstrap de 1.000 reamostragens, semente 42; hashes e `inputs_unchanged` conferidos. Com os cinco originais de `180337Z`, Fleiss (quatro categorias, casos completos) = 0,6841 em 55 de 100 unidades; F1 médio entre pares = 0,7303 exato e 0,8196 parcial. Os intervalos são por par de anotadores; não há IC para kappa ou para o F1 médio agregado. A análise adicional com Anderson usa o arquivo de `183539Z`, cuja independência é incerta. |
| Dados | Amostra atual mantida para esta rodada. | A proposta em `experiments/data/preparacao-revisada-20261112/` contém 60 IDs únicos e 90 atribuições. Sete candidatas fora do escopo (`445, 110, 325, 358, 354, 333, 390`) e o ID `306` ambíguo permanecem; `408, 435, 406, 418, 457` têm foco misto e `373` é sobre PT, que está no escopo. Alertas de integridade: repetição em `178` junto de `445`, truncamento/reinício em `139`, mojibake em `57` e `501`, “Mais lidas” em `220`. Bea aceita essas limitações e não quer substituições nem correção de texto nesta rodada. Consulte `experiments/data/preparacao/data-quality-improvements.md`. `scope_review` fica PENDENTE como registro do gerador; amostra não congelada. |
| Planilhas de anotação | Próxima etapa; ainda não geradas. | Gerar seis planilhas, uma por anotador, com os 15 IDs do respectivo `ids_<nome>.txt`, usando `gold.py gerar`, `data/raw/articles_202608191040.csv` e `experiments/data/entidades.yaml`. A anotação ainda não começou. |
| Anotação independente, validação e adjudicação | Não iniciadas para a amostra definitiva. | Confirmar disponibilidade dos anotadores; validar as respostas individuais e adjudicar as seis notícias compartilhadas. Não presumir que todos os anotadores estão disponíveis. |
| Gabarito, split, treino e avaliação | Não executados. | Consolidar e validar o gold; depois gerar split 39/6/15 por notícia e registrar hashes. Treino e avaliação vêm após congelar gabarito e split. |

As planilhas de origem devem permanecer intactas. A análise disponível de concordância precisa distinguir os cinco arquivos preservados no backup `20261102T180337Z` da planilha de Anderson no backup `20261102T183539Z`, que já tinha edição manual; a independência dela é incerta. A escolha de Bea para `145-6` continua preservada: Flávio permanece como resposta humana, ainda que a regra de recência produza Lula. Não se deve recalcular o gabarito para acomodar a heurística.

O próximo avanço é gerar as seis planilhas por anotador, usando cada arquivo `ids_<nome>.txt` em `experiments/data/preparacao-revisada-20261112/`, com o comando `gold.py gerar`, o CSV de 19/08 e o snapshot `experiments/data/entidades.yaml`. Manter os 60 artigos e textos sem alteração. A proposta é provisória, `scope_review` permanece pendente e a anotação ainda não começou. Depois: preencher e validar as anotações independentes; adjudicar as seis notícias compartilhadas; consolidar e validar o gold; gerar split 39/6/15 com hashes; treinar e avaliar. D16 registra as limitações aceitas e as recomendações futuras. Nenhum prazo novo foi presumido. As estimativas antigas abaixo permanecem como histórico do planejamento original.

## Situação em 02/11/2026

**Fase atual: fechamento do piloto e preparação da anotação definitiva.** O piloto foi revisado, mas ainda não há gabarito consensual nem teste congelado.

Concluído:

- `experiments/gold.py` gera e valida planilhas e faz o split por notícia. Seus 15 testes passaram. A implementação do split não significa que a divisão definitiva já tenha sido produzida.
- As seis planilhas do piloto, com os mesmos 92 parágrafos das cinco notícias, foram revisadas e validadas. As condições de partidos de D10 foram aplicadas às planilhas.
- D10 a D12 documentam as novas condições de partidos, a ligação pronominal e a normalização para reconhecimento. A implementação experimental dessas regras está em andamento.
- Por decisão de Bea, o pronome "ele" de `145-6` permanece ligado a Flávio nas seis planilhas, preservando as respostas humanas originais nesse caso. D11 continua como orientação documental; não reatribuir automaticamente uma resposta independente para fazê-la coincidir com a heurística.

Em andamento: implementação de `metrics.py`, `mentions.py`, seus testes e a análise de concordância do piloto, por agentes responsáveis por essas frentes. Esses módulos não existiam no início desta etapa; a implementação só será considerada concluída após a verificação das entregas.

Registro histórico de 02/11: naquele momento, a confirmação sobre descrições indiretas de partido ("o partido", "a legenda", "a sigla") continuava pendente, e a amostra e o novo snapshot ainda não estavam prontos. Desde então, a seleção provisória de 60 notícias foi gerada com base na elegibilidade histórica, e um snapshot foi exportado de `prisma-dev` em modo somente leitura. A seleção original e `metadata.json` permanecem preservados com a proveniência de agosto; a revalidação com o snapshot novo é um artefato separado. As etapas e decisões atuais estão registradas na situação de 12/11 no início deste plano. Também faltam o gabarito consensual, o split final e seus hashes, os classificadores aplicados ao conjunto final, os treinos e a avaliação final.

### Procedência das planilhas e limites da concordância

As cópias e os registros de alteração estão em:

| Pasta de backup | Estado preservado |
|---|---|
| [`20261102T180337Z`](../experiments/data/anotacao/backups/20261102T180337Z/LEIA-ME.md) | Cinco planilhas anteriores à primeira intervenção automática. A planilha de Anderson já havia sido alterada manualmente por Bea e não está neste backup. |
| [`20261102T183539Z`](../experiments/data/anotacao/backups/20261102T183539Z/LEIA-ME.md) | Seis planilhas antes da aplicação de D10 e da revisão pronominal; já continham intervenções anteriores. |
| [`20261102T183900Z`](../experiments/data/anotacao/backups/20261102T183900Z/LEIA-ME.md) | Seis planilhas antes de restaurar a resposta original de `145-6`. |

As versões atuais e os dois backups mais recentes não representam respostas independentes. A independência da versão disponível de Anderson não pode ser comprovada, pois houve edição manual antes de seu primeiro backup. A versão original de Beatriz também contém trechos de parágrafo inteiro incompatíveis com os limites de menção do protocolo. A análise de concordância precisa declarar essas restrições, os arquivos utilizados e quaisquer exclusões; não presumir que será possível obter uma medida completa e confiável dos seis anotadores.

### Próximas ações

1. Confirmar a regra de descrições indiretas de partido e registrar a decisão no protocolo.
2. Concluir e verificar as métricas, a heurística e a análise de concordância, mantendo as limitações de procedência explícitas.
3. Exportar o snapshot definitivo e selecionar as 60 notícias, excluindo piloto e rodada 1; distribuir seis compartilhadas e nove exclusivas por anotador.
4. Anotar e validar a amostra, medir concordância antes da adjudicação e então consolidar o gabarito. Só depois gerar a divisão 39/6/15 e registrar os hashes.

As datas da seção 6 são as estimativas originais. Nenhum novo prazo foi acordado neste registro.

## 1. Pontos a decidir antes de 27/10

**Decidido em 26/10** (motivos em [`decisoes-experimentos.md`](decisoes-experimentos.md)): 1.1 → BIO + aliases + menção mais recente (D2); 1.2 → planilha com validador (D1); 1.4 → snapshot congelado (D4); 1.5 → 65/10/25 com as compartilhadas no teste e bootstrap (D3). Em 02/11, D10 a D12 revisaram condições para partidos, ligação pronominal e normalização para reconhecimento; ver 1.3.

Os itens 1.1 a 1.4 definem o formato do gabarito. As novas regras precisam estar aplicadas aos exemplos e aos testes antes da anotação definitiva. A aplicação nas planilhas e o estado da implementação estão registrados na situação de 02/11 acima.

### 1.1 O BERTimbau de REM só detecta, não liga

Um etiquetador BIO marca onde estão os trechos ("o presidente", "ele"), mas não diz a qual dos 40 candidatos cada um se refere. O documento chama a tarefa de "detectar e ligar", e a tabela de famílias só prevê o etiquetador.

Proposta:

- O BERTimbau marca os trechos com duas etiquetas: `DIR` (menção direta) e `IND` (indireta).
- Ligação dos trechos `DIR`: pelos aliases das entidades, observando as condições de elegibilidade de D10 e a normalização auxiliar de D12 no reconhecimento experimental. Reaproveitar os recursos do matcher que já atendem ao requisito.
- Ligação dos trechos `IND`: pela regra da menção mais recente, a mesma da baseline experimental. Para pronomes, D11 exige qualquer entidade anterior mais próxima, inclusive partido; as descrições mantêm o tratamento específico previsto na seção 5.

Com isso, a comparação entre a baseline de menção mais recente e o BERTimbau isola a detecção, porque a ligação é a mesma nos dois. O acerto da ligação sai como métrica separada. Como D11 também define o gabarito dos pronomes por proximidade, essa parcela da métrica mede aderência à convenção e não comprova resolução contextual de correferência.

Se sobrar tempo depois de 05/11, um segundo modelo pode fazer a ligação: um classificador de pares (trecho marcado, candidato citado antes na notícia) que responde sim ou não. Não recomendo colocar isso no caminho crítico, porque seria uma terceira rodada de treino em CPU.

Isso precisa entrar no texto do método, porque muda o que o sistema C mede.

### 1.2 Formato da anotação de trechos

O documento não diz onde a anotação é feita. Duas opções:

| | Planilha + validador | Label Studio na VPS |
|---|---|---|
| Como anota | uma linha por menção: parágrafo, texto do trecho, ocorrência (1ª, 2ª…), tipo, candidato. Teor numa segunda aba, uma linha por (parágrafo, candidato) | marca o trecho com o mouse, escolhe candidato e teor |
| Offsets | um script acha a posição do trecho no parágrafo e reclama quando não acha | exportados prontos |
| Infra | nenhuma | Docker na VPS, login para 6 pessoas, porta exposta (falar com o Anderson) |
| Risco | erro de digitação no trecho (o validador pega) | montar e testar em um dia |

Recomendo a planilha, por causa do prazo. O validador transforma a planilha no formato do item 3.1 e lista os erros por anotador, para corrigir no mesmo dia.

### 1.3 Protocolo revisado após o piloto

O protocolo está em [`protocolo-anotacao-v2.md`](protocolo-anotacao-v2.md). As planilhas de Anderson, Beatriz e Nicolas são a referência escolhida para discutir exemplos, sem excluir os demais anotadores nem tratar suas respostas como consenso automático. Usar os originais anteriores às correções para medir concordância independente.

Regras definidas em 02/11:

- **Partidos:** aceitar nome completo; exigir "partido" antes de nomes que também sejam palavras comuns; exigir artigo antes de sigla, incluindo contrações; ignorar siglas entre parênteses. Em "o PT, Lula (PT)", há uma menção a PT. A ocorrência ignorada não gera teor por si só.
- **Pronomes admitidos:** ligar à entidade anterior mais próxima na mesma notícia, inclusive partido. Sem antecedente identificado, não inventar uma ligação.
- **Reconhecimento:** usar representação auxiliar sem acentos e com pontuação substituída por separadores; normalizar aliases do mesmo modo. Primeiro identificar exclusões entre parênteses no original; depois normalizar, mantendo correspondência de posições. Essa limpeza não se aplica automaticamente ao teor.

**Registro de 02/11:** naquele momento, a regra para descrições indiretas de partido permanecia pendente. D15, em 12/11, resolveu a questão: "a legenda", "o partido" e "a sigla" não identificam nem geram teor para um partido. Os demais pontos marcados `[piloto]` permanecem identificados no protocolo. Aplicar a regra vigente na preparação das planilhas definitivas.

### 1.4 Lista das 40 entidades congelada

`config/entities.yaml` tem 10 entidades; a produção lê as 40 do banco (`entidade_matching`). Se a lista mudar no meio do experimento, os resultados deixam de ser comparáveis. Fazer um snapshot com `scripts/export_target_entities.py` (ele já exporta os aliases) e salvar em `experiments/data/entidades.yaml`. O Gustavo pode gerar junto com a amostra.

### 1.5 Tamanho do teste

60 notícias com 15% de teste dão 9 notícias, cerca de 150 parágrafos (a média medida no corpus é 17 parágrafos por notícia). Com essa quantidade, o positivo e o negativo devem ficar com algumas dezenas de pares cada, e uma diferença de poucos pontos de F1 entre dois sistemas não vai significar nada.

Sugestões, em ordem de custo:

1. Intervalo de confiança por bootstrap reamostrando notícias (não parágrafos) em todas as tabelas. Custo: algumas linhas no código das métricas. Recomendo fazer de qualquer jeito.
2. Colocar as 6 notícias compartilhadas no teste, porque elas terão o rótulo mais confiável depois de resolvidas as divergências.
3. Aumentar o teste para cerca de 25% e reduzir a validação para 10%. O BERTimbau vai rodar com configuração-padrão, então a validação só serve para escolher a época. O treino de teor ainda tem os 1.054 pares da rodada 1.

A parcela de menções indiretas (pergunta 1) não depende de treino, então pode ser calculada no gabarito inteiro, e não só no teste.

## 2. Estrutura de `experiments/`

```
experiments/
  README.md            como rodar cada etapa e reproduzir as tabelas
  requirements.txt     scikit-learn, torch (CPU), transformers
  data/
    entidades.yaml     snapshot das 40 entidades (1.4)
    anotacao/          planilhas devolvidas pelos anotadores
    gold.jsonl         gabarito no formato 3.1, gerado pelo gold.py
    split.json         notícia → train/validation/test
  gold.py              planilhas → gold.jsonl, validação, split, concordância
  mentions.py          spans do matcher e menção mais recente
  teor.py              léxico (produção) e TF-IDF
  bert_teor.py         treino e predição do BERTimbau de teor
  bert_rem.py          treino e predição do BERTimbau de REM
  metrics.py           todas as métricas do item 4
  run.py               avaliação de cada etapa, 4 sistemas, tempo
  results/             predições, tabelas e metadados de cada execução
tests/experiments/     testes das métricas, do validador e da heurística
```

Um arquivo por responsabilidade, sem pacote nem classe base. Os módulos de produção (`entity_matcher`, `lexicon`, `segmentation`) são importados de `src/`, como `scripts/build_annotation_batches.py` já faz, e nunca são editados.

## 3. Contratos de dados

Definir isto antes de qualquer código deixa o Lucas (métricas, TF-IDF) e a Bea (heurística, estrutura) trabalharem ao mesmo tempo.

### 3.1 Gabarito (`gold.jsonl`, uma linha por parágrafo)

```json
{
  "article_id": "150",
  "paragraph_index": 3,
  "text": "O presidente afirmou que ...",
  "split": "test",
  "mentions": [
    {"start": 0, "end": 12, "text": "O presidente", "type": "IND", "entity_id": "123"}
  ],
  "teor": {"123": "positivo"}
}
```

- Os parágrafos vêm de `segmentation.segment()`, o mesmo segmentador da produção, para os índices baterem com o que o sistema A vê.
- `start`/`end` são offsets de caractere no `text`.
- `text` mantém pontuação e acentos originais. A representação auxiliar de reconhecimento de D12 não substitui esse campo. Ao reconhecer um trecho na representação normalizada, converter suas posições de volta ao original e gravar o trecho com sua grafia original.
- Parágrafos sem menção e sem teor também entram (listas vazias), porque o sistema pode prever menção neles.

### 3.2 Predição de menções

```json
{"article_id": "150", "paragraph_index": 3, "start": 0, "end": 12, "type": "IND", "entity_id": "123", "system": "recency"}
```

### 3.3 Predição de pares (fim a fim)

```json
{"article_id": "150", "paragraph_index": 3, "entity_id": "123", "teor": "positivo", "system": "D"}
```

## 4. Métricas (definições para o código e para o artigo)

**Menções**
- Casamento um para um entre trecho previsto e trecho do gabarito. Exato: mesmos `start` e `end`. Parcial: sobreposição de pelo menos um caractere.
- Precisão, revocação e F1, no geral e separados por tipo. A revocação usa o tipo do gabarito; a precisão usa o tipo previsto (o matcher sempre prevê `DIR`, a heurística sempre `IND`).
- Ligação: entre os trechos casados, a fração com o `entity_id` certo. Também o F1 exigindo trecho e candidato certos ao mesmo tempo.
- Para pronomes, interpretar o acerto de ligação como aderência à convenção de D11, pois o próprio gabarito usa a entidade anterior mais próxima. Não apresentá-lo isoladamente como evidência de correferência contextual.

**Teor (etapa isolada)**
- Entrada: as menções do gabarito, para não misturar erro de menção com erro de teor.
- F1 por classe, F1 macro e matriz de confusão (scikit-learn já tem as três).

**Fim a fim**
- Unidade: o trio (notícia, parágrafo, candidato).
- Para cada classe c: VP = par presente nos dois com teor c nos dois; FP = previsto com c e ausente no gabarito ou com outro teor; FN = c no gabarito e ausente na predição ou com outro teor. F1 macro = média das três classes.
- Saldo por candidato: contagem de positivo, negativo e neutro por candidato, previsto contra gabarito, com a diferença absoluta.

**Concordância**
- Kappa de Fleiss para o teor nas 6 notícias compartilhadas. É uma fórmula de poucas linhas, não justifica instalar o statsmodels só para isso; o teste confere contra um exemplo publicado.
- F1 entre anotadores para os trechos: média do F1 de cada par de anotadores, tratando um como gabarito do outro.

**Intervalos**: bootstrap por notícia (1.000 reamostragens, semente fixa) em todas as tabelas.

**Custo**: segundos por 1.000 parágrafos na VPS, com `torch.set_num_threads(2)` para todos os sistemas, medido em 3 repetições.

## 5. Como cada sistema funciona

| Peça | Implementação |
|---|---|
| Matcher por nome | `entity_matcher.match_entities` de produção, sem mudança, para os pares. Para métricas de trecho, uma função em `mentions.py` acha a posição de cada ocorrência dos aliases que casaram (a função de produção devolve só o alias, sem posição, e só uma vez por entidade). |
| Menção mais recente | Percorre a notícia em ordem. Lista fixa de termos indiretos definida com o piloto e o treino, nunca olhando o teste. Pronomes admitidos → qualquer entidade anterior mais próxima, inclusive partido (D11). Descrição de pessoa → última pessoa nomeada. Termos descritivos de partido dependem da confirmação de D10; se admitidos, a ligação prevista é ao último partido nomeado. |
| Léxico | `lexicon.classify_paragraph` de produção. Dá o mesmo teor a todos os candidatos do parágrafo, como hoje. |
| TF-IDF | `TfidfVectorizer` + `LogisticRegression(class_weight="balanced")` do scikit-learn. Para separar candidatos no mesmo parágrafo, o trecho da menção é trocado por um marcador (`[ALVO]`) antes de vetorizar. |
| BERTimbau teor | `neuralmind/bert-base-portuguese-cased`, classificação de sequência com o candidato marcado (`[ALVO] … [/ALVO]` em volta do trecho da menção), até 256 tokens. Treino: gabarito novo (treino) + os 1.054 pares da rodada 1, sem os `nao_relacionado` e `indeterminado`. |
| BERTimbau REM | mesmo modelo, classificação de tokens BIO com `DIR` e `IND`. Ligação como em 1.1. |

A normalização auxiliar e os filtros de D10 a D12 são requisitos de implementação experimental. O matcher já trata acentos e limites de palavra; reaproveitar esses recursos antes de acrescentar processamento. Manter os textos originais para segmentação, offsets e entrada dos classificadores de teor. A revisão não prescreve remover pontuação ou acentos da entrada do BERTimbau de tokens.

O sistema A continua recebendo o texto original e executando a produção sem mudanças. Não acrescentar silenciosamente os novos filtros ou uma limpeza à sua entrada: isso criaria uma variante. Ao avaliá-lo, registrar que o novo gabarito exclui ocorrências de partido que a produção pode reconhecer. A mesma definição de matcher de produção vale para a peça compartilhada por A e B.

Combinações do teste central:

| Sistema | Menções | Teor | Onde o teor é marcado |
|---|---|---|---|
| A | matcher | léxico | parágrafo inteiro |
| B | matcher | BERTimbau | trecho do alias encontrado |
| C | BERTimbau REM + ligação | léxico | parágrafo inteiro |
| D | BERTimbau REM + ligação | BERTimbau | trecho previsto |

Como todo sistema grava predições no formato 3.2/3.3, o 3 × 3 do documento é só mais combinações no `run.py`, sem treino novo.

## 6. Etapas, com verificação

| # | Etapa | Quem | Até | Verifica com |
|---|---|---|---|---|
| 1 | Decidir 1.1 a 1.5 com a equipe | todos | 27/10 | decisões registradas no protocolo |
| 2 | Snapshot das 40 entidades + amostra das 60 notícias + 5 do piloto, já segmentadas | Gustavo | 26-27/10 | 40 entidades no arquivo; notícias da amostra fora das 150 da rodada 1 |
| 3 | `gold.py`: planilha → `gold.jsonl`, relatório de erros por anotador, split por notícia | Bea | 27/10 | roda no piloto; todo trecho anotado tem offset; nenhuma notícia em dois splits |
| 4 | `metrics.py` + testes com casos feitos à mão (exato, parcial, ligação, pares, Fleiss, bootstrap) | Lucas | 29/10 | testes passam; Fleiss bate com o exemplo de referência |
| 5 | `mentions.py`: spans do matcher e menção mais recente + testes de D10 a D12 | Bea | 30/10 | testar dois candidatos alternados, partido como antecedente mais próximo, siglas com artigo/contração e entre parênteses, nomes comuns, acentos, pontuação e offsets originais; avaliação no treino roda |
| 6 | `teor.py`: léxico e TF-IDF | Lucas | 01/11 | A no treino dá números próximos do levantamento de 29/09 (macro-F1 ≈ 0,41 do léxico), ressalvando que o gabarito mudou |
| 7 | Concordância e resolução de divergências; congelar teste (hash do `gold.jsonl` e do `split.json` registrado) | todos | 31/10 | kappa e F1 entre anotadores calculados; hash anotado no README |
| 8 | Rodada curta de treino na VPS (100 exemplos, 1 época) para medir tempo e memória | Anderson e Bea | 01/11 | tempo por época e pico de RAM medidos; decide nº de épocas |
| 9 | `bert_teor.py` e `bert_rem.py`: treino de madrugada, 2 threads | Anderson e Bea | 05/11 | F1 na validação acima do TF-IDF/heurística; modelo salvo com hash e config |
| 10 | `run.py`: etapas isoladas, 4 sistemas, tempo, metadados (commit, hashes, versões das libs) | Lucas e Bea | 06/11 | uma execução gera todas as tabelas do documento com IC |
| 11 | Rodar no teste uma única vez | Lucas e Bea | 07/11 | `results/` versionado com o commit usado |
| 12 | Análise de erros por tipo de menção e caso difícil | Lucas e Bea | 07/11 | amostra de erros classificada por categoria |

Os passos 3 a 6 andam junto com a anotação, usando o piloto e o que já estiver anotado de treino. Ninguém roda nada no teste antes do passo 11.

As datas da tabela são as estimativas de 26/10. O fechamento do protocolo após o piloto, em 02/11, exige replanejar as etapas dependentes; esta revisão não registra novos prazos como se tivessem sido acordados.

Pela regra do projeto, a implementação de cada passo vai para um agente (backend-engineer para o código, test-engineer para os testes), e a conversa principal só verifica o resultado contra a coluna "Verifica com".

## 7. Riscos

- **Treino em CPU estourar o prazo.** Se a rodada curta do passo 8 indicar mais de 3 horas por treino, reduzir para 128 tokens ou para menos épocas. Uma máquina com GPU de alguém resolve.
- **Uma única semente.** Com pouco dado, o F1 do BERTimbau varia bastante entre sementes. Se houver tempo, 3 sementes no modelo de teor e reportar média e desvio. Se não, registrar como limitação.
- **Vazamento.** A lista de termos da heurística, o marcador do TF-IDF e o número de épocas precisam ser definidos sem ver o teste. O hash do passo 7 serve para provar isso.
- **Segmentação.** Itens de lista viram parágrafos soltos (C5 em `Melhorias_Classifier_Prisma.md`). Manter a segmentação de produção para o sistema A ser fiel, e citar no artigo.
- **Python.** A `.venv` local está em Python 3.14. Conferir a versão na VPS e se há wheel de torch CPU para ela antes do passo 8.
- **Desempenho da VPS.** Treino no mesmo servidor do Classifier e da API: madrugada, threads limitadas e acompanhamento do Anderson.
