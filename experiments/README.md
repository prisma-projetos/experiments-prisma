# Experimentos do artigo

Ferramentas e dados para avaliar o reconhecimento de menções e a classificação de teor. As regras de anotação estão em [`docs/protocolo-anotacao-v2.md`](../docs/protocolo-anotacao-v2.md) e as escolhas de método, com o motivo de cada uma, em [`docs/decisoes-experimentos.md`](../docs/decisoes-experimentos.md). Para retomar o trabalho em outra sessão, leia [`docs/CONTINUIDADE-EXPERIMENTOS.md`](../docs/CONTINUIDADE-EXPERIMENTOS.md).

## Estado (19/11/2026)

O artigo da disciplina (entrega em 26/11/2026, sem publicação por enquanto) é um estudo exploratório sobre o piloto: 5 notícias, 92 parágrafos (D17). Ele mede três coisas: a concordância entre anotadores, a parcela de menções indiretas e o desempenho das regras sem treino (matcher de produção, heurística de menção mais recente e léxico) contra uma referência do piloto montada por voto da maioria.

A referência e a avaliação já foram geradas. A próxima etapa é escrever o artigo.

A amostra de 60 notícias, o split 39/6/15 e os modelos treinados (TF-IDF e BERTimbau) ficaram para trabalhos futuros. As ferramentas e a amostra preparada continuam aqui para isso (seção [Trabalhos futuros](#trabalhos-futuros-amostra-de-60-notícias)).

## Ambiente

Use `.venv-experiments`, separado do `.venv` principal (D13). Ele foi validado com Python 3.14.3, scikit-learn 1.9.1, NumPy 2.5.4 e SciPy 1.18.1. Para criar do zero:

```sh
python3 -m venv .venv-experiments
.venv-experiments/bin/python -m pip install -r experiments/requirements-ml.lock.txt
```

O `.venv` principal e os requisitos de produção seguem sem dependências de ML.

Todos os comandos abaixo rodam da raiz do repositório. Nenhuma CLI sobrescreve arquivos existentes: para gerar de novo, passe uma pasta `--saida` nova ou apague a anterior.

## Fluxo do artigo

### 1. Consolidar a referência por voto da maioria

```sh
.venv-experiments/bin/python experiments/consolidate.py consolidar
```

Lê as planilhas revisadas de `data/anotacao/piloto/` dos cinco votantes (Beatriz, Cristovam, Gustavo, Lucas e Nicolas; Anderson fica fora, ver D17) e confere por SHA-256 que elas não foram alteradas. Uma resposta entra com pelo menos 3 de 5 votos; referências genéricas de partido (D15) não contam. Gera em `results/piloto-referencia/`:

- `referencia-provisoria.jsonl`: referência antes dos desempates;
- `pendencias.xlsx`: casos sem maioria, com a coluna `decisao` para Bea preencher;
- `report.md` e `report.json`: votos, descartes, alertas e procedência.

### 2. Aplicar os desempates

Depois de preencher `pendencias.xlsx`:

```sh
.venv-experiments/bin/python experiments/consolidate.py aplicar --saida experiments/results/piloto-referencia-final
```

`--remover-teor PARAGRAPH_ID:ENTITY_ID` retira um par de teor da referência final e pode ser repetido. Exige `--motivo-remocao`, que fica registrado. O comando usado em 19/11/2026 foi:

```sh
.venv-experiments/bin/python experiments/consolidate.py aplicar \
  --saida experiments/results/piloto-referencia-final \
  --remover-teor 175-4:22 \
  --motivo-remocao "D15: a única menção ao PL no parágrafo é 'A sigla', referência genérica que não gera teor; decisão da Bea (19/11/2026)"
```

Gera em `results/piloto-referencia-final/`:

- `referencia.jsonl`: a referência usada na avaliação;
- `decisoes-desempate.json`: decisões, remoções, alertas e hashes das entradas.

### 3. Avaliar as regras sem treino

```sh
.venv-experiments/bin/python experiments/evaluate.py
```

Compara o matcher de produção, a menção mais recente e o léxico com `results/piloto-referencia-final/referencia.jsonl`, usando o snapshot `data/exports/target_entities.yaml` (o mesmo do piloto) e `config/lexicon.yaml`. Calcula menções, teor isolado, fim a fim, custo e lista os erros. Gera em `results/piloto-avaliacao/`:

- `report.md` e `report.json`;
- `predicoes-matcher-lexico.jsonl`, `predicoes-recency-lexico.jsonl` e `predicoes-lexico-pares-referencia.jsonl`.

Opções: `--referencia`, `--entidades`, `--lexico`, `--saida`, `--reamostragens` (padrão 1000), `--semente` (padrão 42) e `--repeticoes` (padrão 7). Veja `--help`.

## Resultados principais

Os números completos, com intervalos de confiança e limitações, estão nos relatórios. Os essenciais:

Concordância ([`results/piloto-concordancia/report.md`](results/piloto-concordancia/report.md)), calculada nos cinco originais do backup `20261102T180337Z`: Fleiss do teor (quatro categorias) de 0,6841 em 55 de 100 unidades completas; F1 médio de menções entre pares de 0,7303 (exato) e 0,8196 (parcial).

Referência ([`results/piloto-referencia/report.md`](results/piloto-referencia/report.md) e [`decisoes-desempate.json`](results/piloto-referencia-final/decisoes-desempate.json)): 83 menções, sendo 14 indiretas (cerca de 17%), e 72 pares de teor (59 neutros, 12 negativos, 1 positivo). Ficaram de fora 19 menções e 11 pares de teor sem maioria. Bea decidiu deixar fora o empate `T001` (160-16, Flávio) e remover o par 175-4 / PL.

Avaliação ([`results/piloto-avaliacao/report.md`](results/piloto-avaliacao/report.md)):

| Medida | Matcher (produção) | Menção mais recente |
|---|---:|---:|
| Detecção, F1 exato | 0,5775 | 0,6289 |
| Trecho + entidade, F1 exato | 0,5775 | 0,5660 |
| IND, revocação exata | 0 de 14 (só prevê DIR) | 9 de 14 |
| Fim a fim com léxico, F1 macro | 0,2555 | 0,2713 |

Teor isolado (léxico nos 72 pares da referência): F1 macro 0,3918; F1 do neutro 0,8276.

Pontos que precisam aparecer no artigo:

- Com um único par positivo, o F1 positivo e o F1 macro de teor são instáveis.
- Os aliases do snapshot não têm formas curtas como "Flávio", "Gaspar", "Caiado" e "Kassab", e por isso nenhum dos dois sistemas passa de 41 de 69 na revocação de DIR. Os aliases não foram alterados para não ajustar o sistema ao conjunto avaliado.
- O custo foi medido num Apple M4, não na VPS de produção.

## Testes

```sh
.venv-experiments/bin/python -m pytest tests/experiments -q
```

Última verificação (19/11/2026): 118 testes passaram.

## Outras ferramentas

- `agreement.py`: concordância descritiva do piloto; gerou `results/piloto-concordancia/`.
- `gold.py`: gera planilhas de anotação, valida as preenchidas e faz o split por notícia (`gerar`, `validar`, `split`; veja `--help`).
- `metrics.py`: funções de métrica usadas por todos os relatórios.
- `mentions.py`: `load_entities_snapshot` e `predict_mentions`, sem CLI. `include_party_descriptions` é obrigatório e deve ser `False` (D15).
- `teor.py`: `predict_lexicon` e o TF-IDF (`fit_tfidf`, `predict_tfidf`, `mark_target`, ver D14).
- `tfidf.py`: CLI de treino e predição do TF-IDF. Só foi exercitado com dados sintéticos.
- `prepare_data.py` e `export_snapshot.py`: preparação da amostra e exportação do snapshot de entidades.

## Dados

- `data/piloto_ids.txt`: as cinco notícias do piloto (145, 159, 146, 160, 175).
- `data/anotacao/piloto/`: planilhas atuais do piloto, já revisadas com D10. Não sobrescrever.
- `data/anotacao/backups/`: cópias preservadas e registros de alteração. O backup `20261102T180337Z` tem os originais de cinco anotadores; a planilha de Anderson está em `20261102T183539Z` e já tinha edição manual.
- `data/entidades.yaml`: snapshot de `prisma-dev` (10/11/2026), com 40 entidades e 73 aliases (D13).

## Trabalhos futuros: amostra de 60 notícias

A amostra está preparada em [`data/preparacao-revisada-20261112/`](data/preparacao-revisada-20261112/): 60 IDs únicos e 90 atribuições (seis notícias compartilhadas e nove exclusivas por anotador), a partir do CSV de 19/08/2026. Está marcada como provisória e `scope_review` segue pendente. Bea decidiu mantê-la como está (D16); as limitações aceitas e as melhorias recomendadas estão em [`data/preparacao/data-quality-improvements.md`](data/preparacao/data-quality-improvements.md).

Quando o trabalho for retomado, a ordem prevista é:

1. Gerar uma planilha por anotador com os 15 IDs de cada `ids_<nome>.txt`, usando `gold.py gerar`, `data/raw/articles_202608191040.csv` e `data/entidades.yaml`. Confirmar antes quem vai anotar.
2. Validar cada planilha preenchida de forma independente.
3. Adjudicar as seis notícias compartilhadas e consolidar o gabarito.
4. Congelar o split 39/6/15 por notícia com hashes, treinar os modelos e avaliar no teste congelado.

Para regenerar os artefatos da preparação (raramente necessário, porque os arquivos atuais guardam a proveniência de agosto):

```sh
.venv/bin/python experiments/prepare_data.py
.venv/bin/python -m pytest -q tests/experiments/test_prepare_data.py
```
