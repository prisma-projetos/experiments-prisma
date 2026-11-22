# Continuidade do experimento

Atualizado em 19/11/2026. Resumo para outro modelo ou colaborador retomar o trabalho. Comandos, saídas e números estão em [`experiments/README.md`](../experiments/README.md); o motivo de cada escolha está nas [decisões metodológicas](decisoes-experimentos.md), principalmente na D17. As regras de anotação estão no [protocolo](protocolo-anotacao-v2.md).

## Estado atual

- O artigo da disciplina (entrega em 26/11/2026, sem publicação por enquanto) é um estudo exploratório sobre o piloto: 5 notícias, 92 parágrafos (D17).
- A referência do piloto foi consolidada por voto da maioria de cinco anotadores (Anderson fica fora) e está em `experiments/results/piloto-referencia-final/referencia.jsonl`: 83 menções (14 indiretas) e 72 pares de teor (59 neutros, 12 negativos, 1 positivo).
- As regras sem treino foram avaliadas contra essa referência. O relatório está em `experiments/results/piloto-avaliacao/report.md`.
- A concordância entre anotadores já estava calculada em `experiments/results/piloto-concordancia/report.md`, sobre os originais do backup `20261102T180337Z`.
- Testes: 118 passaram em 19/11/2026 (`.venv-experiments/bin/python -m pytest tests/experiments -q`).
- A amostra de 60 notícias, o split 39/6/15 e os modelos treinados (TF-IDF e BERTimbau) ficaram para trabalhos futuros. A amostra preparada e as ferramentas continuam no repositório; a ordem prevista para retomar está no fim do `experiments/README.md`.

## Fluxo usado

Sempre com `.venv-experiments`, a partir da raiz:

```sh
.venv-experiments/bin/python experiments/consolidate.py consolidar
.venv-experiments/bin/python experiments/consolidate.py aplicar --saida experiments/results/piloto-referencia-final --remover-teor 175-4:22 --motivo-remocao "..."
.venv-experiments/bin/python experiments/evaluate.py
```

O primeiro gera a referência provisória e `pendencias.xlsx` em `experiments/results/piloto-referencia/`. O segundo aplica os desempates preenchidos por Bea e gera `referencia.jsonl` e `decisoes-desempate.json`. O terceiro gera `experiments/results/piloto-avaliacao/`. O motivo completo usado em `--motivo-remocao` está no README e em `decisoes-desempate.json`. Nenhum deles sobrescreve saídas existentes.

Decisões de Bea na consolidação: o empate `T001` (160-16, Flávio) ficou fora; o par 175-4 / PL foi removido porque a única referência ao partido é "A sigla" (D15); os alertas de teor sem menção em 145-7, 160-22 e 175-6 ficaram, por serem compatíveis com sujeito oculto.

## Regras que continuam valendo

- D10, partidos: nome completo conta; nome que também é palavra comum, como "Missão", exige "partido" antes; sigla exige artigo anterior, aceitando contrações ("do PT", "ao PL"); sigla entre parênteses é ignorada.
- D11, pronomes: o pronome vai para a entidade anterior mais próxima na notícia, incluindo partidos. Em `145-6`, as planilhas continuam ligando a Flávio, conforme a resposta humana original, embora a heurística preveja Lula. Não mudar.
- D12, normalização: remover acentos e pontuação só na representação usada para reconhecer entidades, preservando o texto original e os offsets.
- D15, referências genéricas: "o partido", "a legenda" e "a sigla" não são menção a nenhum partido e não geram teor.
- Não sobrescrever as planilhas de `experiments/data/anotacao/` nem alterar respostas originais para coincidir com uma heurística.
- A referência do piloto não é um gabarito adjudicado. Não chamá-la de gabarito final, nem chamar de final qualquer split.

## Instrução para a próxima sessão

A próxima etapa é escrever o artigo. Um relatório com o esqueleto do texto está sendo preparado em `docs/artigo/`; quando existir, comece por ele. As limitações que o texto precisa declarar estão na D17 e nos relatórios: referência por voto da maioria sobre planilhas revisadas, regras D10 a D12 formuladas olhando o piloto, mudança de protocolo depois do piloto (D15), apenas cinco notícias, um único par positivo e aliases curtos ausentes do snapshot.

Execução de código: por padrão, fornecer o comando para a Bea rodar; executar diretamente só quando ela pedir.
