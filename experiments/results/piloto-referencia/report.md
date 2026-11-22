# Referência provisória do piloto por voto da maioria

Gerado por `experiments/consolidate.py consolidar`. A referência fica provisória até Bea decidir as pendências de `pendencias.xlsx` e rodar `aplicar`. Não é um gabarito adjudicado (D17).

## Configuração

- Votantes (5): Beatriz, Cristovam, Gustavo, Lucas, Nicolas.
- Uma unidade entra na referência com pelo menos 3 votos.
- Fora da votação: Anderson. D17: planilha editada por Bea antes do primeiro backup; contaria o critério dela duas vezes.
- Notícias: 145, 159, 146, 160, 175.

## Unidades aceitas

| Unidade | 5/5 | 4/5 | 3/5 | Total |
|---|---:|---:|---:|---:|
| Menção (trecho + entidade) | 79 | 1 | 3 | 83 |
| Teor (parágrafo + entidade) | 60 | 12 | 1 | 73 |

Na menção, a coluna conta quem marcou exatamente o mesmo trecho com a mesma entidade; o tipo segue a maioria de quem marcou. No teor, conta quem deu o rótulo escolhido. Ausência de rótulo não conta como neutro.

## Pendências para Bea

| Tipo | Quantidade |
|---|---:|
| mencao_tipo | 0 |
| mencao_limites | 0 |
| mencao_entidades | 0 |
| teor_empate | 1 |

- T001 (teor_empate), 160-16: entidade: FLAVIO NANTES BOLSONARO; negativo: Beatriz, Cristovam; neutro: Nicolas; sem rótulo: Gustavo, Lucas

## Descartes (sem maioria)

Menções: 19. Pares de teor com menos de 3 rótulos: 11.

- 145-2 "O candidato" [0:11] -> FLAVIO NANTES BOLSONARO; votos: Lucas, Nicolas (sem maioria, descartado)
- 145-4 "seu vice" [115:123] -> ALFREDO GASPAR DE MENDONÇA NETO; votos: Nicolas (sem maioria, descartado)
- 145-10 "ameaça bolsonarista" [2:21] -> FLAVIO NANTES BOLSONARO; votos: Nicolas (sem maioria, descartado)
- 159-1 "candidato" [12:21] -> FLAVIO NANTES BOLSONARO; votos: Nicolas (sem maioria, descartado)
- 159-1 "seu principal adversário" [184:208] -> LUIZ INÁCIO LULA DA SILVA; votos: Gustavo, Nicolas (sem maioria, descartado)
- 159-2 "o governo petista" [17:34] -> LUIZ INÁCIO LULA DA SILVA; votos: Beatriz, Nicolas (sem maioria, descartado)
- 159-6 "Seu filho mais velho" [165:185] -> FLAVIO NANTES BOLSONARO; votos: Beatriz, Nicolas (sem maioria, descartado)
- 159-6 "seu vice" [241:249] -> ALFREDO GASPAR DE MENDONÇA NETO; votos: Beatriz, Nicolas (sem maioria, descartado)
- 159-11 "seu filho mais velho" [219:239] -> FLAVIO NANTES BOLSONARO; votos: Beatriz, Nicolas (sem maioria, descartado)
- 146-6 "de seu filho" [121:133] -> FLAVIO NANTES BOLSONARO; votos: Beatriz (sem maioria, descartado)
- 146-6 "seu filho" [124:133] -> FLAVIO NANTES BOLSONARO; votos: Nicolas (sem maioria, descartado)
- 146-6 "o senador" [135:144] -> FLAVIO NANTES BOLSONARO; votos: Lucas, Nicolas (sem maioria, descartado)
- 160-16 "desses partidos" [9:24] -> PARTIDO DOS TRABALHADORES; votos: Nicolas (sem maioria, descartado)
- 160-16 "do seu filho" [57:69] -> FLAVIO NANTES BOLSONARO; votos: Beatriz (sem maioria, descartado)
- 160-16 "seu filho" [60:69] -> FLAVIO NANTES BOLSONARO; votos: Nicolas (sem maioria, descartado)
- 160-18 "do senador" [220:230] -> FLAVIO NANTES BOLSONARO; votos: Beatriz, Nicolas (sem maioria, descartado (sobrepõe trecho aceito))
- 160-21 "argumentos petistas" [35:54] -> PARTIDO DOS TRABALHADORES; votos: Nicolas (sem maioria, descartado)
- 175-6 "do governo" [22:32] -> LUIZ INÁCIO LULA DA SILVA; votos: Beatriz, Nicolas (sem maioria, descartado)
- 175-6 "a gestão federal" [64:80] -> LUIZ INÁCIO LULA DA SILVA; votos: Nicolas (sem maioria, descartado)
- teor 145-10 / FLAVIO NANTES BOLSONARO: Nicolas=negativo (sem maioria, descartado)
- teor 160-16 / PARTIDO DOS TRABALHADORES: Cristovam=neutro, Nicolas=neutro (sem maioria, descartado)
- teor 160-21 / PARTIDO DOS TRABALHADORES: Nicolas=neutro (sem maioria, descartado)
- teor 160-31 / FLAVIO NANTES BOLSONARO: Gustavo=neutro (sem maioria, descartado)
- teor 160-32 / FLAVIO NANTES BOLSONARO: Gustavo=negativo (sem maioria, descartado)
- teor 160-33 / FLAVIO NANTES BOLSONARO: Gustavo=neutro (sem maioria, descartado)
- teor 160-34 / FLAVIO NANTES BOLSONARO: Gustavo=neutro (sem maioria, descartado)
- teor 160-35 / FLAVIO NANTES BOLSONARO: Gustavo=negativo (sem maioria, descartado)
- teor 160-36 / FLAVIO NANTES BOLSONARO: Gustavo=neutro (sem maioria, descartado)
- teor 160-37 / FLAVIO NANTES BOLSONARO: Gustavo=neutro (sem maioria, descartado)
- teor 160-38 / FLAVIO NANTES BOLSONARO: Gustavo=neutro (sem maioria, descartado)

## Exclusões antes da votação

Referências genéricas de partido (D15): 10. Trechos de parágrafo inteiro, que não contam como voto: 0.

- D15, Beatriz: 175-3 "A legenda" [97:106] -> PARTIDO LIBERAL
- D15, Beatriz: 175-4 "A sigla" [0:7] -> PARTIDO LIBERAL
- D15, Cristovam: 175-3 "A legenda" [97:106] -> PARTIDO LIBERAL
- D15, Cristovam: 175-4 "A sigla" [0:7] -> PARTIDO LIBERAL
- D15, Gustavo: 175-3 "A legenda" [97:106] -> PARTIDO LIBERAL
- D15, Gustavo: 175-4 "A sigla" [0:7] -> PARTIDO LIBERAL
- D15, Lucas: 175-3 "A legenda" [97:106] -> PARTIDO LIBERAL
- D15, Lucas: 175-4 "A sigla" [0:7] -> PARTIDO LIBERAL
- D15, Nicolas: 175-3 "A legenda" [97:106] -> PARTIDO LIBERAL
- D15, Nicolas: 175-4 "A sigla" [0:7] -> PARTIDO LIBERAL

## Duplicatas

Menção repetida pelo mesmo votante conta um voto. Se as repetições tiverem tipos diferentes, o voto de tipo desse votante não conta. Teor duplicado de um votante exclui a unidade inteira desse votante, como em `agreement.py`.


## Alertas de inconsistência (sem resolução automática)

O protocolo exige linha de teor para toda entidade com menção no parágrafo. Teor sem menção pode ser legítimo (sujeito oculto), por isso também é só alerta. Pendências abertas podem gerar alertas que somem depois de `aplicar`.

- Menção sem teor: 0.
- Teor sem menção: 4.
  - 145-7 / FLAVIO NANTES BOLSONARO (neutro)
  - 160-22 / FLAVIO NANTES BOLSONARO (neutro)
  - 175-4 / PARTIDO LIBERAL (neutro), com referência genérica D15 excluída no parágrafo
  - 175-6 / LUIZ INÁCIO LULA DA SILVA (negativo)
- Menções aceitas sobrepostas: 0.

## Linhas com erro do validador

Linhas com erro técnico ficam fora, como em `gold.py validar`. Motivos e valores originais estão em `report.json` (`coverage`).

| Votante | Menções válidas | Pares de teor válidos | Linhas com erro em menções / teor |
|---|---:|---:|---:|
| Beatriz | 92 | 74 | 0 / 0 |
| Cristovam | 83 | 75 | 0 / 0 |
| Gustavo | 85 | 81 | 0 / 0 |
| Lucas | 85 | 71 | 0 / 0 |
| Nicolas | 101 | 77 | 0 / 0 |

## Pontos em aberto para Bea

- A aba de teor não diz qual trecho motivou a linha. Um teor de partido gerado só por referência genérica (D15) não é detectável automaticamente; ele aparece como alerta de teor sem menção, marcado quando houve exclusão D15 da mesma entidade no parágrafo.
- Trechos minoritários sobrepostos a um trecho aceito da mesma entidade são descartados, porque a regra exige o trecho exato. Se outra entidade sem trecho aceito somar 3 votantes no grupo, vira pendência.
- Menção repetida pelo mesmo votante com tipos diferentes: o trecho conta um voto, mas o voto de tipo desse votante não conta. Não havia regra para isso.
- A exclusão D15 só reconhece o trecho inteiro igual a artigo/contração + partido, legenda ou sigla (singular ou plural). Trechos maiores, como "o partido do presidente", passam pela votação normal.

## Limitações

- A referência não é um gabarito adjudicado nem vem de respostas totalmente independentes: as planilhas atuais passaram por revisão (D17).
- As regras D10 a D12 foram formuladas olhando o piloto, o que tende a favorecer a heurística avaliada nele.
- O protocolo mudou depois do piloto (D15). As respostas originais não foram alteradas; a exclusão de referências genéricas acontece só aqui.
- Cinco notícias não permitem generalização.

## Procedência

Entradas lidas sem gravação, com SHA-256 conferido antes e depois.

| Entrada | Caminho | SHA-256 |
|---|---|---|
| Beatriz | `experiments/data/anotacao/piloto/beatriz.xlsx` | `ec758f1901da0761107a99c7c094f5fd199478358ab80e1e373fd473580bc50c` |
| Cristovam | `experiments/data/anotacao/piloto/cristovam (1).xlsx` | `d960e2878ff07be580ace8065a1f80d18a198b5d2cf41c7d11f9507f6afcb00a` |
| Gustavo | `experiments/data/anotacao/piloto/gustavo - Planilha.xlsx` | `a90690a83a79aa524de4e2e18bba0573c3e837b785bc7ac809070c33163e8751` |
| Lucas | `experiments/data/anotacao/piloto/Lucas - Planilha.xlsx` | `dd23828164eded9def096f492508d14815520a301ef12987197532c175874a9e` |
| Nicolas | `experiments/data/anotacao/piloto/nicolas.xlsx` | `7ca3daa38d0735d491444e5288d57fb63858d7b84b196891490a83a0d138a486` |
| raw_csv | `data/raw/articles_202608191040.csv` | `0b96e39e31337d36963914335143c69cdf84619ad8a716beafe0c938fef821d2` |
| entities | `data/exports/target_entities.yaml` | `ff74cfb3c03cdee4889d85430007f14721360b0eb62f8ca747f18caa7595431e` |
| pilot_ids | `experiments/data/piloto_ids.txt` | `32a9dcf03c95254468b231fab4e831e12cf0c72f50757e20f10106a389b87466` |
| gold_code | `experiments/gold.py` | `e534066c94e5fcb45631288f47c862d082b31deca990db9690699bb92450c34a` |
| agreement_code | `experiments/agreement.py` | `7a78261bd622e4c9e52e6a1ce1a603ebeef8413688b9752cffae515f6ec89833` |
| consolidate_code | `experiments/consolidate.py` | `258668f766e9d872a37532d94283404be245a3ac7b3dc996a86b974d0976737d` |
| saída | `referencia-provisoria.jsonl` | `8e9568970147b83ecb58a26bef5980e3b52b8d51792e1b775425c6812f643b1a` |

```sh
.venv-experiments/bin/python experiments/consolidate.py consolidar
```
