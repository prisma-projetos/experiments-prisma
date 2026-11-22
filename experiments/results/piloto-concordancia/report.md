# Concordância descritiva do piloto

- Cinco fontes precedem as intervenções automáticas. A cópia disponível de Anderson já havia sido editada manualmente; sua independência não pode ser comprovada.
- Beatriz anotou também trechos de parágrafo inteiro, incompatíveis com os limites de menção do protocolo. Esses trechos foram preservados e afetam especialmente o F1 exato.
- A análise principal usa os cinco originais preservados. A análise adicional inclui Anderson, com independência não comprovada. Nenhuma análise constitui gabarito consensual.
- As novas regras D10 a D12 não foram aplicadas às respostas. Em particular, nenhuma atribuição de 145-6 foi corrigida ou adjudicada.
- Ausência de teor não é neutro. Kappa usa quatro categorias, incluindo indeterminado, apenas em unidades com todos os anotadores presentes. F1 de teor dos sistemas usa três classes em metrics.py.
- O bootstrap reamostra notícias inteiras. Os cinco artigos do piloto limitam a interpretação dos intervalos; eles não corrigem a procedência ou as exclusões.

Notícias: 145, 159, 146, 160, 175. Bootstrap: 1000 reamostragens por notícia; semente 42; IC de 95%.

| Par (referência / previsão) | F1 exato | IC 95% | F1 parcial | IC 95% | F1 conjunto exato | F1 conjunto parcial |
|---|---:|---|---:|---|---:|---:|
| Beatriz / Cristovam | 0.4528 | [0.3846; 0.5152] | 0.6541 | [0.6046; 0.7314] | 0.4528 | 0.6541 |
| Beatriz / Gustavo | 0.4848 | [0.4324; 0.5645] | 0.6667 | [0.6143; 0.7363] | 0.4848 | 0.6667 |
| Beatriz / Lucas | 0.4878 | [0.4384; 0.5556] | 0.6585 | [0.6143; 0.7111] | 0.4878 | 0.6585 |
| Beatriz / Nicolas | 0.4920 | [0.4192; 0.5385] | 0.6631 | [0.6258; 0.6905] | 0.4920 | 0.6631 |
| Cristovam / Gustavo | 0.9293 | [0.7724; 1.0000] | 0.9596 | [0.8929; 1.0000] | 0.9293 | 0.9596 |
| Cristovam / Lucas | 0.9239 | [0.7722; 0.9859] | 0.9543 | [0.8928; 0.9859] | 0.9239 | 0.9543 |
| Cristovam / Nicolas | 0.8182 | [0.6535; 0.9198] | 0.8727 | [0.7644; 0.9315] | 0.8182 | 0.8727 |
| Gustavo / Lucas | 0.9754 | [0.9542; 0.9894] | 0.9754 | [0.9542; 0.9894] | 0.9754 | 0.9754 |
| Gustavo / Nicolas | 0.8673 | [0.8040; 0.9198] | 0.8938 | [0.8302; 0.9360] | 0.8673 | 0.8938 |
| Lucas / Nicolas | 0.8711 | [0.8018; 0.9299] | 0.8978 | [0.8468; 0.9393] | 0.8711 | 0.8978 |

Médias dos 10 pares dos cinco originais: exact_overall = 0.7303; exact_joint = 0.7303; partial_overall = 0.8196; partial_joint = 0.8196.

O F1 conjunto exige trecho e entidade corretos. A ligação condicional e os resultados por tipo estão no JSON; a direção da referência é explícita. O JSON inclui também IC dos F1 conjuntos.

## Cobertura e exclusões

| Anotador | Menções válidas | Trechos de parágrafo inteiro | Pares de teor válidos | Linhas com erro em menções / teor |
|---|---:|---:|---:|---:|
| Anderson | 106 | 0 | 88 | 0 / 0 |
| Beatriz | 63 | 1 | 58 | 51 / 49 |
| Cristovam | 96 | 0 | 86 | 0 / 0 |
| Gustavo | 102 | 0 | 95 | 0 / 0 |
| Lucas | 101 | 0 | 85 | 0 / 0 |
| Nicolas | 124 | 0 | 91 | 39 / 39 |

Fleiss principal (cinco originais, quatro categorias): 0.6841362562352322. Foram incluídas 55 de 100 unidades na união; 45 ficaram fora por ausência de pelo menos um rótulo válido. As contagens por unidade e os anotadores ausentes estão no JSON.

Linhas não vazias com erro técnico são excluídas pelo validador. Isso inclui linhas apenas com observações ou identificador, sem anotação completa; as contagens não representam necessariamente anotações tentadas. Unidades de teor duplicadas são excluídas por inteiro, sem escolher a primeira resposta. Avisos de normalização preservam os offsets localizados no texto original.

- Beatriz, mencoes: linhas 11, 13, 14, 15, 16, 25, 33, 38, 42, 45, 46, 47, 51, 52, 53, 58, 59, 60, 62, 63, 64, 66, 67, 68, 70, 71, 72, 73, 74, 78, 82, 85, 87, 88, 89, 90, 91, 92, 94, 95, 96, 97, 98, 99, 100, 101, 103, 104, 106, 110, 111.
- Beatriz, teor: linhas 7, 11, 13, 14, 15, 16, 23, 25, 29, 36, 39, 40, 41, 45, 52, 53, 54, 56, 57, 58, 60, 62, 64, 65, 66, 67, 68, 72, 76, 79, 81, 82, 83, 84, 85, 86, 88, 89, 90, 91, 92, 93, 94, 95, 97, 98, 100, 104, 105.
- Beatriz, teor duplicado excluído: 145-4 / 108563260302, linhas [6, 7].
- Nicolas, mencoes: linhas 22, 24, 25, 38, 68, 71, 72, 73, 82, 90, 91, 92, 95, 96, 97, 102, 105, 107, 108, 109, 110, 111, 115, 120, 127, 128, 129, 130, 131, 134, 135, 136, 137, 138, 139, 140, 141, 155, 156.
- Nicolas, teor: linhas 16, 18, 19, 28, 47, 50, 51, 52, 57, 65, 66, 67, 70, 71, 72, 75, 77, 79, 80, 81, 82, 83, 87, 91, 97, 98, 99, 100, 101, 104, 105, 106, 107, 108, 109, 110, 111, 123, 124.

## Análise adicional com Anderson

A independência da planilha de Anderson não foi comprovada. A tabela reúne os 15 pares para descrever a versão disponível, sem interpretar os seis como respostas independentes.

| Par | F1 exato | F1 parcial | F1 conjunto exato | F1 conjunto parcial |
|---|---:|---:|---:|---:|
| Anderson / Beatriz | 0.4970 | 0.6627 | 0.4970 | 0.6627 |
| Anderson / Cristovam | 0.8911 | 0.9406 | 0.8911 | 0.9406 |
| Anderson / Gustavo | 0.9327 | 0.9519 | 0.9327 | 0.9519 |
| Anderson / Lucas | 0.9275 | 0.9469 | 0.9275 | 0.9469 |
| Anderson / Nicolas | 0.8609 | 0.8870 | 0.8609 | 0.8870 |
| Beatriz / Cristovam | 0.4528 | 0.6541 | 0.4528 | 0.6541 |
| Beatriz / Gustavo | 0.4848 | 0.6667 | 0.4848 | 0.6667 |
| Beatriz / Lucas | 0.4878 | 0.6585 | 0.4878 | 0.6585 |
| Beatriz / Nicolas | 0.4920 | 0.6631 | 0.4920 | 0.6631 |
| Cristovam / Gustavo | 0.9293 | 0.9596 | 0.9293 | 0.9596 |
| Cristovam / Lucas | 0.9239 | 0.9543 | 0.9239 | 0.9543 |
| Cristovam / Nicolas | 0.8182 | 0.8727 | 0.8182 | 0.8727 |
| Gustavo / Lucas | 0.9754 | 0.9754 | 0.9754 | 0.9754 |
| Gustavo / Nicolas | 0.8673 | 0.8938 | 0.8673 | 0.8938 |
| Lucas / Nicolas | 0.8711 | 0.8978 | 0.8711 | 0.8978 |

Fleiss adicional: 0.729445194950389; 55 unidades completas de 100 na união; 45 excluídas. Os IC por par estão no JSON.

## Reprodução e procedência

```sh
.venv/bin/python experiments/agreement.py
```

Os arquivos de entrada foram lidos sem gravação, com SHA-256 conferido antes e depois. Caminhos, hashes de dados e código, configuração efetiva, exclusões com motivos e valores originais estão em `report.json`. O CSV fornece os textos segmentados; a ordem das colunas de Beatriz foi identificada pelos cabeçalhos.
