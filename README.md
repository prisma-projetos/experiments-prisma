# PRISMA — Documentação e Experimentos

Este repositório centraliza a documentação técnica, os artefatos metodológicos e os resultados experimentais do projeto **PRISMA**, um sistema distribuído para coleta, classificação e análise de notícias políticas utilizando Modelos de Linguagem (LLMs).

Ele atua como ponto de entrada oficial do projeto, reunindo os experimentos conduzidos e os links para todos os módulos que compõem a arquitetura.

## Estrutura deste Repositório

* [`docs/`](./docs) — Documentação técnica, arquitetura do sistema e materiais de apoio.
* [`experiments/`](./experiments) — Scripts, datasets de avaliação, métricas e resultados obtidos nos experimentos.

## Módulos do Sistema

O PRISMA é dividido em módulos independentes, hospedados nesta mesma organização:

| Módulo | Tecnologia | Descrição |
| :--- | :--- | :--- |
| **[`scrapping-prisma`](https://github.com/prisma-projetos/scrapping-prisma)** | Python | Módulo responsável pela coleta (web scraping) de notícias em portais selecionados, configurável para temas ou figuras políticas específicas. |
| **[`classifier-prisma`](https://github.com/prisma-projetos/classifier-prisma)** | Python | Módulo de classificação das notícias coletadas, categorizando o conteúdo para as etapas seguintes do pipeline. |
| **[`analyser-prisma`](https://github.com/prisma-projetos/analyser-prisma)** | Python | Módulo de análise e sumarização baseado em LLMs, responsável por gerar resumos e análises de sentimento a partir das notícias classificadas. |
| **[`api-prisma`](https://github.com/prisma-projetos/api-prisma)** | Java | API de backend responsável pela orquestração dos dados, regras de negócio e exposição dos endpoints para a interface. |
| **[`app-prisma`](https://github.com/prisma-projetos/app-prisma)** | TypeScript | Aplicação web (frontend) para visualização das notícias, classificações, resumos e análises geradas pelo sistema. |

## Fluxo Geral do Pipeline

1. **Coleta (`scrapping-prisma`):** Extração de notícias a partir das fontes configuradas.
2. **Classificação (`classifier-prisma`):** Categorização e filtragem do conteúdo coletado.
3. **Análise (`analyser-prisma`):** Processamento com LLMs para geração de resumos e análise de sentimento.
4. **Disponibilização (`api-prisma` e `app-prisma`):** Persistência, consulta via API e visualização na interface web.
