<div align="center">

# experiments-prisma

**Documentação, decisões de arquitetura e experimentos do PRISMA**: protocolos de anotação, ADRs, scripts de avaliação, dados do piloto e resultados usados no artigo da disciplina.

![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.9-F7931E?logo=scikitlearn&logoColor=white)
![LaTeX](https://img.shields.io/badge/Artigo-LaTeX-008080?logo=latex&logoColor=white)
![Status](https://img.shields.io/badge/status-estudo_explorat%C3%B3rio-blue)

[Organização PRISMA](https://github.com/prisma-projetos) · [Relatório do artigo (PDF)](docs/artigo/relatorio-artigo.pdf)

</div>

---

## O que é este repositório

Este repositório reúne o **material de pesquisa** do PRISMA, separado dos módulos de código. Ele espelha as pastas `docs/` e `experiments/` do [`classifier-prisma`](https://github.com/prisma-projetos/classifier-prisma), onde os experimentos foram desenvolvidos, para que o artigo e as decisões de projeto possam ser consultados sem navegar pelo código de produção.

```
scrapping-prisma ──▶ classifier-prisma ──▶ analyser-prisma ──▶ api-prisma ──▶ app-prisma
                          ▲
                          └── experiments-prisma: avalia o reconhecimento de menções e a classificação de teor
```

## Sumário

- [O estudo](#o-estudo)
- [Resultados principais](#resultados-principais)
- [Estrutura](#estrutura)
- [Documentação](#documentação)
- [Decisões de arquitetura (ADRs)](#decisões-de-arquitetura-adrs)
- [Reproduzindo os experimentos](#reproduzindo-os-experimentos)
- [Trabalhos futuros](#trabalhos-futuros)
- [Repositórios do PRISMA](#repositórios-do-prisma)

## O estudo

**Estudo exploratório sobre o piloto de anotação**: **5 notícias e 92 parágrafos**, anotados de forma independente pela equipe segundo o [protocolo v2](docs/protocolo-anotacao-v2.md).

Ele responde a três perguntas:

1. **Concordância entre anotadores**: quão estável é a tarefa de marcar menções e teor?
2. **Menções indiretas**: qual parcela das referências a candidatos não usa o nome (por exemplo, "o ex-presidente" ou "a sigla")?
3. **Regras sem treino**: como se saem o *matcher* de produção, a heurística de menção mais recente e o léxico contra uma referência montada por voto da maioria (≥ 3 de 5 votos)?

A amostra de 60 notícias e os modelos treinados (TF-IDF e BERTimbau) ficaram para [trabalhos futuros](#trabalhos-futuros).

## Resultados principais

**Concordância** ([relatório](experiments/results/piloto-concordancia/report.md))

| Medida | Valor |
|---|---:|
| Fleiss κ do teor (4 categorias, 55 de 100 unidades completas) | 0,6841 |
| F1 médio de menções entre pares, exato / parcial | 0,7303 / 0,8196 |

**Referência consolidada** ([relatório](experiments/results/piloto-referencia/report.md))

| | |
|---|---:|
| Menções | 83, sendo **14 indiretas (cerca de 17%)** |
| Pares de teor | 72: 59 neutros, 12 negativos e 1 positivo |

**Avaliação das regras sem treino** ([relatório](experiments/results/piloto-avaliacao/report.md))

| Medida | Matcher (produção) | Menção mais recente |
|---|---:|---:|
| Detecção, F1 exato | 0,5775 | **0,6289** |
| Trecho + entidade, F1 exato | **0,5775** | 0,5660 |
| Menções indiretas, revocação | 0 de 14 | **9 de 14** |
| Fim a fim com léxico, F1 macro | 0,2555 | **0,2713** |

Teor isolado (léxico nos 72 pares): F1 macro de 0,3918 e F1 do neutro de 0,8276.

> **Limitações:** com um único par positivo, o F1 positivo e o F1 macro são instáveis. Os aliases não incluem formas curtas ("Flávio", "Caiado", "Kassab") e foram mantidos assim para não ajustar o sistema ao conjunto avaliado. O custo foi medido num Apple M4, e não na VPS de produção.

## Estrutura

```
├── docs/
│   ├── adr/                              # decisões de arquitetura 0001–0004
│   ├── artigo/relatorio-artigo.{tex,pdf} # relatório e roteiro do artigo
│   ├── protocolo-anotacao{,-v2}.md       # regras de anotação
│   ├── decisoes-experimentos.md          # D1…D17: o que foi escolhido e por quê
│   ├── plano-implementacao-experimentos.md
│   ├── CONTINUIDADE-EXPERIMENTOS.md      # como retomar o trabalho
│   ├── dicionario-dados-analyser.{md,pdf}
│   ├── pesquisa-correferencia.md
│   ├── propostas-mudancas-scraper.md
│   └── scraper-como-atualizar-target-entities.md
└── experiments/
    ├── consolidate.py · evaluate.py · agreement.py   # fluxo do artigo
    ├── gold.py · metrics.py · mentions.py · teor.py · tfidf.py
    ├── prepare_data.py · export_snapshot.py
    ├── requirements-ml.lock.txt                      # ambiente travado
    ├── data/
    │   ├── piloto_ids.txt · entidades.yaml           # 5 notícias; snapshot de 40 entidades / 73 aliases
    │   ├── anotacao/piloto/ · anotacao/backups/      # planilhas revisadas + originais preservados
    │   └── preparacao*/                              # amostra de 60 notícias (futuro)
    └── results/
        ├── piloto-concordancia/
        ├── piloto-referencia/ · piloto-referencia-final/
        ├── piloto-avaliacao/
        └── environment.json                          # versões usadas na execução
```

## Documentação

| Documento | Para que serve |
|---|---|
| [`experiments/README.md`](experiments/README.md) | Passo a passo dos experimentos, opções das CLIs e dados |
| [`docs/protocolo-anotacao-v2.md`](docs/protocolo-anotacao-v2.md) | Como anotar menções (diretas e indiretas) e teor |
| [`docs/decisoes-experimentos.md`](docs/decisoes-experimentos.md) | Registro datado das decisões de método (D1–D17) |
| [`docs/plano-implementacao-experimentos.md`](docs/plano-implementacao-experimentos.md) | Plano original dos experimentos |
| [`docs/CONTINUIDADE-EXPERIMENTOS.md`](docs/CONTINUIDADE-EXPERIMENTOS.md) | Estado atual e próximos passos |
| [`docs/pesquisa-correferencia.md`](docs/pesquisa-correferencia.md) | Pesquisa sobre correferência |
| [`docs/dicionario-dados-analyser.md`](docs/dicionario-dados-analyser.md) | Contrato de dados classifier → analyser |
| [`docs/propostas-mudancas-scraper.md`](docs/propostas-mudancas-scraper.md) | Alinhamento de escopo entre scraper e classifier |
| [`docs/artigo/relatorio-artigo.pdf`](docs/artigo/relatorio-artigo.pdf) | Mudança de escopo, resultados e esqueleto do artigo |

## Decisões de arquitetura (ADRs)

| ADR | Decisão | Status |
|---|---|---|
| [0001](docs/adr/0001-scraper-classifier-rabbitmq-outbox.md) | RabbitMQ entre scraper e classifier, com *outbox* transacional no scraper | Aceito |
| [0002](docs/adr/0002-system-db-compartilhado-outbox-analyser.md) | System DB compartilhado e notificação ao analyser via outbox | Parcialmente superado |
| [0003](docs/adr/0003-notificacao-analyser-publicacao-direta.md) | Publicação direta classifier → analyser, sem outbox | Superado pela 0004 |
| [0004](docs/adr/0004-outbox-proprio-para-notificacao-analyser.md) | Outbox próprio (`classifier_analyser_outbox`) + publisher agendado | **Vigente** |

## Reproduzindo os experimentos

Os scripts importam módulos de produção (`entity_matcher`, `entities_store`, `lexicon`) e leem `config/lexicon.yaml`. Por isso, **reexecute-os a partir do [`classifier-prisma`](https://github.com/prisma-projetos/classifier-prisma)**, que contém `src/`, `config/` e esta mesma pasta `experiments/`. Os resultados versionados aqui servem para consulta e auditoria.

```sh
git clone git@github.com:prisma-projetos/classifier-prisma.git && cd classifier-prisma

python3 -m venv .venv-experiments
.venv-experiments/bin/python -m pip install -r experiments/requirements-ml.lock.txt

.venv-experiments/bin/python experiments/consolidate.py consolidar                                   # 1. voto da maioria
.venv-experiments/bin/python experiments/consolidate.py aplicar --saida experiments/results/piloto-referencia-final   # 2. desempates
.venv-experiments/bin/python experiments/evaluate.py                                                 # 3. avaliação

.venv-experiments/bin/python -m pytest tests/experiments -q                                          # 118 testes
```

- **Nenhuma CLI sobrescreve resultados.** Para gerar de novo, use uma pasta `--saida` nova.
- As entradas são conferidas por **SHA-256**, e a avaliação usa *bootstrap* por notícia (1000 reamostragens, semente 42).
- O ambiente usado (Python 3.14.3, scikit-learn 1.9.1, NumPy 2.5.4, SciPy 1.18.1) está registrado em `experiments/results/environment.json`.

## Trabalhos futuros

A amostra de **60 notícias** já está preparada em [`experiments/data/preparacao-revisada-20261112/`](experiments/data/preparacao-revisada-20261112/), com 90 atribuições: 6 notícias compartilhadas e 9 exclusivas por anotador. Próximos passos:

1. Gerar as planilhas por anotador (`gold.py gerar`) e validar cada uma.
2. Adjudicar as notícias compartilhadas e consolidar o gabarito.
3. Congelar o split **39/6/15** por notícia, com hashes.
4. Treinar e avaliar **TF-IDF** e **BERTimbau** (REM com etiquetas `DIR`/`IND` e classificação de teor) no conjunto de teste congelado.

## Repositórios do PRISMA

| Repositório | Papel |
|---|---|
| [`.github`](https://github.com/prisma-projetos) | Página da organização |
| [`scrapping-prisma`](https://github.com/prisma-projetos/scrapping-prisma) | Coleta de notícias |
| [`classifier-prisma`](https://github.com/prisma-projetos/classifier-prisma) | Identificação de entidades e classificação do teor |
| [`analyser-prisma`](https://github.com/prisma-projetos/analyser-prisma) | Resumos e panoramas com LLM |
| [`api-prisma`](https://github.com/prisma-projetos/api-prisma) | API REST somente leitura |
| [`app-prisma`](https://github.com/prisma-projetos/app-prisma) | Interface web |
| **`experiments-prisma`** | Documentação, ADRs e experimentos do artigo *(este)* |
