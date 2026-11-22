# Avaliação das regras sem treino no piloto

Referência: voto da maioria do piloto (D17), 92 parágrafos de 5 notícias (145, 159, 146, 160, 175). Menções: 83 (69 DIR, 14 IND). Pares de teor: 72. Descrições genéricas de partido desligadas (D15).

## Limitações

- A referência tem só 5 notícias (92 parágrafos). O bootstrap reamostra notícias inteiras; com 5 unidades os intervalos são grosseiros e não permitem generalização.
- Há um único par de teor positivo na referência: F1 positivo e F1 macro são instáveis e dependem de um acerto ou erro.
- A referência vem de voto da maioria sobre planilhas revisadas, não de gabarito adjudicado (D17). As regras D10 a D12 foram formuladas olhando o piloto, o que tende a favorecer a heurística de menção mais recente.
- O matcher de produção só prevê menções diretas; seus resultados de IND são zero por construção.
- O tempo foi medido nesta máquina, não na VPS de produção; serve para comparar os sistemas entre si, não para estimar custo absoluto em produção.

## 1. Menções

IC 95% por bootstrap percentil reamostrando notícias inteiras (1000 reamostragens, semente 42). **Atenção: só há 5 notícias**, então os intervalos são largos e pouco informativos.

### Detecção (geral, sem exigir entidade nem tipo)

| Sistema | Modo | TP | FP | FN | P | R | F1 | IC 95% F1 |
|---|---|---:|---:|---:|---:|---:|---:|---|
| Matcher (produção) | exato | 41 | 18 | 42 | 0.6949 | 0.4940 | 0.5775 | [0.4949; 0.6515] |
| Matcher (produção) | parcial | 41 | 18 | 42 | 0.6949 | 0.4940 | 0.5775 | [0.4949; 0.6515] |
| Menção mais recente | exato | 50 | 26 | 33 | 0.6579 | 0.6024 | 0.6289 | [0.5745; 0.7290] |
| Menção mais recente | parcial | 51 | 25 | 32 | 0.6711 | 0.6145 | 0.6415 | [0.5972; 0.7317] |

### Por tipo

Uma confusão DIR/IND conta como FP no tipo previsto e FN no tipo da referência.

| Sistema | Modo | Tipo | TP | FP | FN | P | R | F1 | IC 95% F1 |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| Matcher (produção) | exato | DIR | 41 | 18 | 28 | 0.6949 | 0.5942 | 0.6406 | – |
| Matcher (produção) | exato | IND | 0 | 0 | 14 | 0.0000 | 0.0000 | 0.0000 | [0.0000; 0.0000] |
| Matcher (produção) | parcial | DIR | 41 | 18 | 28 | 0.6949 | 0.5942 | 0.6406 | – |
| Matcher (produção) | parcial | IND | 0 | 0 | 14 | 0.0000 | 0.0000 | 0.0000 | [0.0000; 0.0000] |
| Menção mais recente | exato | DIR | 41 | 1 | 28 | 0.9762 | 0.5942 | 0.7387 | – |
| Menção mais recente | exato | IND | 9 | 25 | 5 | 0.2647 | 0.6429 | 0.3750 | [0.0645; 0.6061] |
| Menção mais recente | parcial | DIR | 41 | 1 | 28 | 0.9762 | 0.5942 | 0.7387 | – |
| Menção mais recente | parcial | IND | 10 | 24 | 4 | 0.2941 | 0.7143 | 0.4167 | [0.1935; 0.6061] |

### Ligação e joint (trecho + entidade)

Ligação: acurácia da entidade entre os trechos casados na detecção. Joint: exige trecho e entidade, sem exigir tipo.

| Sistema | Modo | Trechos casados | Ligação correta | Acurácia da ligação | Joint P | Joint R | Joint F1 |
|---|---|---:|---:|---:|---:|---:|---:|
| Matcher (produção) | exato | 41 | 41 | 1.0000 | 0.6949 | 0.4940 | 0.5775 |
| Matcher (produção) | parcial | 41 | 41 | 1.0000 | 0.6949 | 0.4940 | 0.5775 |
| Menção mais recente | exato | 50 | 45 | 0.9000 | 0.5921 | 0.5422 | 0.5660 |
| Menção mais recente | parcial | 51 | 46 | 0.9020 | 0.6053 | 0.5542 | 0.5786 |

## 2. Teor isolado (léxico nos pares da referência)

**Atenção: há 1 par positivo na referência**; F1 positivo e F1 macro são instáveis. `metrics.teor_scores` não devolve acurácia, então ela não é reportada.

Distribuição das classes na referência:

| Classe | Pares |
|---|---:|
| positivo | 1 |
| negativo | 12 |
| neutro | 59 |
| indeterminado | 0 |

| Classe | TP | FP | FN | P | R | F1 |
|---|---:|---:|---:|---:|---:|---:|
| positivo | 0 | 4 | 1 | 0.0000 | 0.0000 | 0.0000 |
| negativo | 4 | 7 | 8 | 0.3636 | 0.3333 | 0.3478 |
| neutro | 48 | 9 | 11 | 0.8421 | 0.8136 | 0.8276 |

F1 macro: 0.3918.

Matriz de confusão (linhas: referência; colunas: previsto; pares sem previsão ficam fora da matriz):

| Referência \ Previsto | positivo | negativo | neutro | sem previsão |
|---|---:|---:|---:|---:|
| positivo | 0 | 0 | 1 | 0 |
| negativo | 0 | 4 | 8 | 0 |
| neutro | 4 | 7 | 48 | 0 |

Cobertura: 72 pares na referência, 72 pares previstos avaliados, 0 previstos fora da referência, 0 abstenções, 0 indeterminados excluídos.

## 3. Fim a fim (menções previstas + léxico)

Pares previstos fora da referência contam como FP; pares da referência sem previsão contam como FN.

### Matcher (produção) + léxico

| Classe | TP | FP | FN | P | R | F1 |
|---|---:|---:|---:|---:|---:|---:|
| positivo | 0 | 2 | 1 | 0.0000 | 0.0000 | 0.0000 |
| negativo | 3 | 6 | 9 | 0.3333 | 0.2500 | 0.2857 |
| neutro | 25 | 20 | 34 | 0.5556 | 0.4237 | 0.4808 |

F1 macro: 0.2555.

Matriz de confusão (linhas: referência; colunas: previsto; pares sem previsão ficam fora da matriz):

| Referência \ Previsto | positivo | negativo | neutro | sem previsão |
|---|---:|---:|---:|---:|
| positivo | 0 | 0 | 1 | 0 |
| negativo | 0 | 3 | 6 | 3 |
| neutro | 2 | 4 | 25 | 28 |

Cobertura: 72 pares na referência, 56 pares previstos avaliados, 15 previstos fora da referência, 0 abstenções, 0 indeterminados excluídos.

### Menção mais recente + léxico

| Classe | TP | FP | FN | P | R | F1 |
|---|---:|---:|---:|---:|---:|---:|
| positivo | 0 | 2 | 1 | 0.0000 | 0.0000 | 0.0000 |
| negativo | 3 | 5 | 9 | 0.3750 | 0.2500 | 0.3000 |
| neutro | 28 | 22 | 31 | 0.5600 | 0.4746 | 0.5138 |

F1 macro: 0.2713.

Matriz de confusão (linhas: referência; colunas: previsto; pares sem previsão ficam fora da matriz):

| Referência \ Previsto | positivo | negativo | neutro | sem previsão |
|---|---:|---:|---:|---:|
| positivo | 0 | 0 | 1 | 0 |
| negativo | 0 | 3 | 6 | 3 |
| neutro | 2 | 5 | 28 | 24 |

Cobertura: 72 pares na referência, 60 pares previstos avaliados, 15 previstos fora da referência, 0 abstenções, 0 indeterminados excluídos.

### Saldo por entidade (contagem de pares por classe)

Ref = referência; M = matcher + léxico; R = recency + léxico. Formato positivo/negativo/neutro.

| Entidade | Ref | M | R |
|---|---|---|---|
| ALFREDO GASPAR DE MENDONÇA NETO | 0/0/4 | 0/0/3 | 0/1/5 |
| ANTONIO CARLOS SILVA | 0/0/0 | 0/0/1 | 0/0/1 |
| FLAVIO NANTES BOLSONARO | 1/5/34 | 1/2/11 | 1/2/23 |
| GILBERTO KASSAB | 0/0/1 | 0/0/0 | 0/0/0 |
| LUIZ INÁCIO LULA DA SILVA | 0/6/6 | 1/3/7 | 1/3/10 |
| PARTIDO DOS TRABALHADORES | 0/1/2 | 0/1/5 | 0/1/2 |
| PARTIDO LIBERAL | 0/0/7 | 0/2/14 | 0/0/7 |
| PARTIDO SOCIAL DEMOCRÁTICO | 0/0/0 | 0/0/2 | 0/0/0 |
| RENAN ANTONIO FERREIRA DOS SANTOS | 0/0/1 | 0/1/0 | 0/1/0 |
| ROMEU ZEMA NETO | 0/0/1 | 0/0/1 | 0/0/1 |
| RONALDO RAMOS CAIADO | 0/0/3 | 0/0/1 | 0/0/1 |

## 4. Custo

Mediana de 7 execuções sobre os 92 parágrafos, normalizada para mil parágrafos (`time.perf_counter`). Medido nesta máquina, não na VPS: macOS-26.6.2-arm64-arm-64bit-Mach-O, CPU Apple M4 (10 núcleos lógicos), Python 3.14.3. Carregar entidades fica fora do tempo; carregar o léxico fica dentro.

| Sistema | Mediana (s, 92 parágrafos) | s / 1000 parágrafos |
|---|---:|---:|
| Matcher (só menções) | 0.0152 | 0.1648 |
| Menção mais recente (só menções) | 0.3781 | 4.1101 |
| Léxico (pares da referência) | 0.0023 | 0.0248 |
| Matcher + léxico | 0.0176 | 0.1915 |
| Menção mais recente + léxico | 0.3807 | 4.1379 |

## 5. Listagem de erros (sem interpretação)

### IND da referência perdidas: Matcher (produção) (14)

Perdida = nenhuma menção prevista com interseção e mesma entidade. A coluna seguinte mostra a previsão que se sobrepõe, se houver.

| Parágrafo | Trecho | Entidade | Previsão sobreposta | Contexto |
|---|---|---|---|---|
| 145-1 | "O bolsonarista" [0:14] | FLAVIO NANTES BOLSONARO | – | O bolsonarista discursou aos apoiadores de um trio elétrico, usa… |
| 145-3 | "O senador" [0:9] | FLAVIO NANTES BOLSONARO | – | O senador escolheu a praia de Copacabana, na zona sul do Ri… |
| 145-4 | "Ele" [89:92] | FLAVIO NANTES BOLSONARO | – | …ando um colete à prova de balas sob uma camiseta. Ele estava acompanhado do seu vice na chapa, Alfredo … |
| 145-5 | "O senador" [0:9] | FLAVIO NANTES BOLSONARO | – | O senador se apresentou como uma continuidade do projeto po… |
| 145-6 | "ele" [129:132] | FLAVIO NANTES BOLSONARO | – | … e fez críticas ao governo Lula (PT) que, segundo ele, briga com todo mundo, mas não é capaz de enfrent… |
| 145-8 | "o único candidato" [41:58] | FLAVIO NANTES BOLSONARO | – | Na política externa, se classificou como o único candidato capaz de negociar com grandes potências como Esta… |
| 159-1 | "O senador" [0:9] | FLAVIO NANTES BOLSONARO | – | O senador e candidato à Presidência, Flávio Bolsonaro (PL),… |
| 159-5 | "Candidato" [0:9] | FLAVIO NANTES BOLSONARO | – | Candidato do PL disse que vai classificar milícias como org… |
| 159-5 | "ele" [324:327] | FLAVIO NANTES BOLSONARO | – | …cretário de Estado dos EUA, Marco Rubio, com quem ele esteve reunido na Casa Branca. O governo Lula é c… |
| 159-9 | "o seu candidato" [16:31] | ALFREDO GASPAR DE MENDONÇA NETO | – | Flávio defendeu o seu candidato a vice, Alfredo Gaspar (PL), da acusação de estup… |
| 159-10 | "ele" [102:105] | ALFREDO GASPAR DE MENDONÇA NETO | – | …ausa de seu trabalho na CPMI do INSS, uma vez que ele estava investigando o filho do presidente Lula. G… |
| 159-10 | "Ele" [203:206] | ALFREDO GASPAR DE MENDONÇA NETO | – | … Gaspar diz que é inocente e alvo de uma armação. Ele afirma estar disposto a fazer teste de DNA e se c… |
| 160-18 | "senador" [223:230] | FLAVIO NANTES BOLSONARO | – | …ara um público amplo nas redes sociais do PL e do senador. |
| 175-10 | "O candidato" [0:11] | FLAVIO NANTES BOLSONARO | – | O candidato afirmou que pretende organizar as contas públicas… |

### IND da referência perdidas: Menção mais recente (9)

Perdida = nenhuma menção prevista com interseção e mesma entidade. A coluna seguinte mostra a previsão que se sobrepõe, se houver.

| Parágrafo | Trecho | Entidade | Previsão sobreposta | Contexto |
|---|---|---|---|---|
| 145-1 | "O bolsonarista" [0:14] | FLAVIO NANTES BOLSONARO | – | O bolsonarista discursou aos apoiadores de um trio elétrico, usa… |
| 145-5 | "O senador" [0:9] | FLAVIO NANTES BOLSONARO | "O senador" (IND) -> ALFREDO GASPAR DE MENDONÇA NETO | O senador se apresentou como uma continuidade do projeto po… |
| 145-6 | "ele" [129:132] | FLAVIO NANTES BOLSONARO | "ele" (IND) -> LUIZ INÁCIO LULA DA SILVA | … e fez críticas ao governo Lula (PT) que, segundo ele, briga com todo mundo, mas não é capaz de enfrent… |
| 145-8 | "o único candidato" [41:58] | FLAVIO NANTES BOLSONARO | – | Na política externa, se classificou como o único candidato capaz de negociar com grandes potências como Esta… |
| 159-1 | "O senador" [0:9] | FLAVIO NANTES BOLSONARO | "O senador" (IND) -> LUIZ INÁCIO LULA DA SILVA | O senador e candidato à Presidência, Flávio Bolsonaro (PL),… |
| 159-5 | "Candidato" [0:9] | FLAVIO NANTES BOLSONARO | – | Candidato do PL disse que vai classificar milícias como org… |
| 159-5 | "ele" [324:327] | FLAVIO NANTES BOLSONARO | "ele" (IND) -> PARTIDO LIBERAL | …cretário de Estado dos EUA, Marco Rubio, com quem ele esteve reunido na Casa Branca. O governo Lula é c… |
| 159-9 | "o seu candidato" [16:31] | ALFREDO GASPAR DE MENDONÇA NETO | – | Flávio defendeu o seu candidato a vice, Alfredo Gaspar (PL), da acusação de estup… |
| 159-10 | "Ele" [203:206] | ALFREDO GASPAR DE MENDONÇA NETO | "Ele" (IND) -> LUIZ INÁCIO LULA DA SILVA | … Gaspar diz que é inocente e alvo de uma armação. Ele afirma estar disposto a fazer teste de DNA e se c… |

### Menções previstas falsas (FP) da menção mais recente, modo exato (26)

| Parágrafo | Trecho | Tipo | Entidade | FP também no parcial | Contexto |
|---|---|---|---|---|---|
| 145-3 | "o ex-presidente" [140:155] | IND | FLAVIO NANTES BOLSONARO | sim | …etindo os moldes de campanha utilizados pelo pai, o ex-presidente Jair Bolsonaro (PL). |
| 145-4 | "do candidato" [152:164] | IND | ALFREDO GASPAR DE MENDONÇA NETO | sim | …ompanhado do seu vice na chapa, Alfredo Gaspar, e do candidato a governador Douglas Ruas, além da mãe, Rogéria, … |
| 159-1 | "o presidente" [220:232] | IND | FLAVIO NANTES BOLSONARO | sim | …para criticar seu principal adversário nas urnas, o presidente Lula (PT). |
| 159-6 | "o ex-presidente" [133:148] | IND | FLAVIO NANTES BOLSONARO | sim | …voca o discurso nacionalista que, em 2018, elegeu o ex-presidente Jair Bolsonaro. Seu filho mais velho foi anunciad… |
| 159-7 | "o presidente" [64:76] | IND | ALFREDO GASPAR DE MENDONÇA NETO | sim | …ara apoiadores cantarem "volta, Bolsonaro". "Hoje o presidente Bolsonaro não pode estar aqui com a gente, mas co… |
| 159-7 | "o presidente" [221:233] | IND | ALFREDO GASPAR DE MENDONÇA NETO | sim | …ro junto com vocês mandar um recado: imaginem que o presidente Bolsonaro está nos vendo nesse momento, vamos hom… |
| 159-8 | "ele" [111:114] | IND | PARTIDO LIBERAL | sim | …a eleger, no estado, Douglas Ruas para o governo —ele está atrás do ex-prefeito Eduardo Paes (PSD) nas … |
| 159-10 | "do presidente" [134:147] | IND | ALFREDO GASPAR DE MENDONÇA NETO | sim | …INSS, uma vez que ele estava investigando o filho do presidente Lula. Gaspar diz que é inocente e alvo de uma arm… |
| 159-11 | "o ex-presidente" [22:37] | IND | LUIZ INÁCIO LULA DA SILVA | sim | Bolsonaristas citaram o ex-presidente Jair Bolsonaro. Antes de Flávio discursar para o … |
| 159-11 | "do ex-presidente" [146:162] | IND | LUIZ INÁCIO LULA DA SILVA | sim | …membros do PL relembraram inúmeras vezes a figura do ex-presidente, citando sua prisão e dizendo que foi ele quem es… |
| 159-11 | "ele" [201:204] | IND | LUIZ INÁCIO LULA DA SILVA | sim | …-presidente, citando sua prisão e dizendo que foi ele quem escolheu seu filho mais velho para encabeçar… |
| 146-3 | "ele" [222:225] | IND | LUIZ INÁCIO LULA DA SILVA | sim | …TJ-MA) em atividades particulares. Na publicação, ele aparece ao lado da traseira de uma SUV, em uma pr… |
| 146-6 | "O ex-presidente" [0:15] | IND | LUIZ INÁCIO LULA DA SILVA | sim | O ex-presidente Jair Bolsonaro (PL) cumpre prisão domiciliar em B… |
| 146-6 | "o senador" [135:144] | IND | LUIZ INÁCIO LULA DA SILVA | sim | …omparecer ao lançamento da campanha de seu filho, o senador Flávio Bolsonaro (PL), à Presidência da República… |
| 160-5 | "do ex-presidente" [148:164] | IND | FLAVIO NANTES BOLSONARO | sim | …ometeu alguma irregularidade ao utilizar um vídeo do ex-presidente Jair Bolsonaro (PL) produzido com inteligência ar… |
| 160-10 | "ele" [61:64] | IND | FLAVIO NANTES BOLSONARO | sim | …eira (26/7), a defesa de Jair Bolsonaro negou que ele tenha autorizado a produção e uso do vídeo exibid… |
| 160-11 | "O ex-presidente" [0:15] | IND | FLAVIO NANTES BOLSONARO | sim | O ex-presidente foi autorizado a cumprir pena em prisão domicilia… |
| 160-12 | "o ex-presidente" [86:101] | IND | FLAVIO NANTES BOLSONARO | sim | …o específico, a defesa disse, por outro lado, que o ex-presidente nunca se opôs ao uso de sua imagem pelos filhos. |
| 160-18 | "do senador" [220:230] | IND | FLAVIO NANTES BOLSONARO | não | …o para um público amplo nas redes sociais do PL e do senador. |
| 160-27 | "ele" [49:52] | IND | FLAVIO NANTES BOLSONARO | sim | Sem citar diretamente o vídeo de Jair Bolsonaro, ele disse no dia 27 de julho, ao jornal Estado de São… |
| 160-29 | "Antonio Carlos" [306:320] | DIR | ANTONIO CARLOS SILVA | sim | …s Toffoli), dois do Superior Tribunal de Justiça (Antonio Carlos Ferreira e Ricardo Villas Bôas Cueva) e dois oriu… |
| 160-31 | "Ele" [0:3] | IND | FLAVIO NANTES BOLSONARO | sim | Ele não vê, porém, elementos para abertura de um proc… |
| 160-33 | "Ele" [0:3] | IND | FLAVIO NANTES BOLSONARO | sim | Ele ressalta que o aviso inicial que o avatar faz no … |
| 160-35 | "dela" [90:94] | IND | FLAVIO NANTES BOLSONARO | sim | …gras inerentes à inteligência artificial e ao uso dela. E há uma regra que proíbe taxativamente o uso da… |
| 160-36 | "Ele" [97:100] | IND | FLAVIO NANTES BOLSONARO | sim | …e não houve qualquer ilegalidade no uso do vídeo. Ele afirma que, de fato, o uso desse tipo de gravação… |
| 175-2 | "ao ex-presidente" [127:143] | IND | FLAVIO NANTES BOLSONARO | sim | …o Rio. Antes dos discursos, o evento teve menções ao ex-presidente Jair Bolsonaro e pedidos de apoiadores por seu re… |

### Pares de teor errados pelo léxico, teor isolado (20)

| Parágrafo | Entidade | Referência | Previsto | Texto |
|---|---|---|---|---|
| 145-6 | LUIZ INÁCIO LULA DA SILVA | negativo | neutro | Ao tratar do tema da segurança pública, avaliou que o País perdeu a ‘soberania’ e fez críticas ao governo Lula (PT) que, segundo ele, briga com todo mundo, mas … |
| 159-1 | LUIZ INÁCIO LULA DA SILVA | negativo | neutro | O senador e candidato à Presidência, Flávio Bolsonaro (PL), associou os temas soberania e segurança pública em seu primeiro ato de campanha, realizado no Rio de… |
| 159-2 | LUIZ INÁCIO LULA DA SILVA | negativo | neutro | Flávio disse que o governo petista briga com um país a 10 mil quilômetros de distância, em referência aos EUA, mas que não briga com traficante. A soberania nac… |
| 159-10 | ALFREDO GASPAR DE MENDONÇA NETO | neutro | negativo | Flávio afirmou que Gaspar foi alvo da denúncia por causa de seu trabalho na CPMI do INSS, uma vez que ele estava investigando o filho do presidente Lula. Gaspar… |
| 159-10 | FLAVIO NANTES BOLSONARO | neutro | negativo | Flávio afirmou que Gaspar foi alvo da denúncia por causa de seu trabalho na CPMI do INSS, uma vez que ele estava investigando o filho do presidente Lula. Gaspar… |
| 159-10 | LUIZ INÁCIO LULA DA SILVA | neutro | negativo | Flávio afirmou que Gaspar foi alvo da denúncia por causa de seu trabalho na CPMI do INSS, uma vez que ele estava investigando o filho do presidente Lula. Gaspar… |
| 146-7 | FLAVIO NANTES BOLSONARO | negativo | neutro | O tom emocionado de lamentação pela ausência esteve presente nos discursos de todos os candidatos e teve auge quando Flávio interrompeu sua fala para que fosse … |
| 146-9 | RENAN ANTONIO FERREIRA DOS SANTOS | neutro | negativo | - RENAN SANTOS CRITICA FLÁVIO E LULA, FALA EM DESPERTAR BRASIL E MATAR “VAGABUNDOS”; |
| 146-10 | RONALDO RAMOS CAIADO | neutro | positivo | - CAIADO LANÇA CAMPANHA SEM KASSAB APÓS RUÍDO SOBRE APOIO DO CENTRÃO A LULA; |
| 146-10 | GILBERTO KASSAB | neutro | positivo | - CAIADO LANÇA CAMPANHA SEM KASSAB APÓS RUÍDO SOBRE APOIO DO CENTRÃO A LULA; |
| 146-10 | LUIZ INÁCIO LULA DA SILVA | neutro | positivo | - CAIADO LANÇA CAMPANHA SEM KASSAB APÓS RUÍDO SOBRE APOIO DO CENTRÃO A LULA; |
| 160-7 | FLAVIO NANTES BOLSONARO | positivo | neutro | Na gravação que será analisada pelo TSE, o avatar de Bolsonaro começa avisando que se trata de conteúdo artificial. Depois, faz críticas à sua prisão, diz ter e… |
| 160-18 | FLAVIO NANTES BOLSONARO | negativo | neutro | A federação liderada pelo PT também argumenta que ocorreu campanha eleitoral antecipada, já que o vídeo afirma que "o futuro é Flávio Bolsonaro Presidente" e fo… |
| 160-20 | FLAVIO NANTES BOLSONARO | negativo | neutro | Além disso, solicita a aplicação de uma multa contra a campanha de Flávio Bolsonaro por propaganda antecipada. Segundo a legislação eleitoral, essa punição deve… |
| 160-22 | FLAVIO NANTES BOLSONARO | neutro | negativo | Quanto à acusação de deep fake, sustentou que o vídeo não fere as restrições do TSE porque deixa claro sua natureza artificial. |
| 160-30 | FLAVIO NANTES BOLSONARO | negativo | neutro | Ouvido pela reportagem, o advogado eleitoral Guilherme Barcelos acredita que há elementos para condenar Flávio Bolsonaro por campanha antecipada e proibir a rep… |
| 175-1 | FLAVIO NANTES BOLSONARO | neutro | positivo | Em discurso, Pazuello direcionou um apelo ao eleitorado feminino, que classificou como decisivo para o avanço do movimento conservador. Flávio Bolsonaro era agu… |
| 175-5 | FLAVIO NANTES BOLSONARO | neutro | negativo | Flávio Bolsonaro (PL) afirmou que o governo Lula deixará um “legado” de “incompetência e corrupção”. A declaração foi feita neste domingo, durante o primeiro at… |
| 175-6 | LUIZ INÁCIO LULA DA SILVA | negativo | neutro | Ao criticar a atuação do governo na segurança, Flávio disse que a gestão federal “briga com país em outro continente”, mas não consegue combater crimes que afet… |
| 175-9 | FLAVIO NANTES BOLSONARO | neutro | negativo | Flávio Bolsonaro (PL) prometeu promover um “tesouraço” caso seja eleito presidente, com cortes de impostos, burocracia, corrupção e cargos que atribuiu ao PT. A… |

## Procedência

Entradas e código lidos sem gravação, com SHA-256 conferido antes e depois.

| Entrada | Caminho | SHA-256 |
|---|---|---|
| referencia | `experiments/results/piloto-referencia-final/referencia.jsonl` | `73c164be653b04ef4e08eae5ec57dbc0f4bd7ece9bddb9bd34e5fb9240ee3f78` |
| entities | `data/exports/target_entities.yaml` | `ff74cfb3c03cdee4889d85430007f14721360b0eb62f8ca747f18caa7595431e` |
| lexicon | `config/lexicon.yaml` | `8c660d06a88e56e9cdfa9d90b564230facccdda64674f2f544ec3a44fac81dd1` |
| evaluate_code | `experiments/evaluate.py` | `9d072ee4168730088e9f1e4dfe5cd6e0fb6979cfbd24825eb595027f8d204e04` |
| metrics_code | `experiments/metrics.py` | `97c1181e2a8501a42097e2862187c95e8795c94aeacfafeb469f12753bb70120` |
| mentions_code | `experiments/mentions.py` | `64bf84b9160baaf26bdb8c24dd416f7025800a6147e939f88af3e43d7c62d7c6` |
| teor_code | `experiments/teor.py` | `8ee9398d0f3e25fbb23a567d0d5a285060137033ae5a8a64262d1eb555a3ce9e` |
| consolidate_code | `experiments/consolidate.py` | `37e3bb7ca596706df85b831aaa7b98574af858906270027d9db1b670aea94667` |
| agreement_code | `experiments/agreement.py` | `7a78261bd622e4c9e52e6a1ce1a603ebeef8413688b9752cffae515f6ec89833` |
| entity_matcher_code | `src/entity_matcher.py` | `186ba54634dd1525d647f93d9c92fb9f205b1564e6d325df1585fa91ce91642e` |
| entities_store_code | `src/entities_store.py` | `6cbdead11ec4f07bf36450d110e8c9ba681d653c3c0de3a8d02dbf6b968dbb0a` |
| lexicon_code | `src/lexicon.py` | `b71fcde2b74a0b442163757fe4f4bd6c823281aff8995ddf731c8c224a57ff9f` |
| saída | `predicoes-matcher-lexico.jsonl` | `0a5710797088b672859acc8b467c8cdc163aa19a8d1becd0bf8a20a18554bd28` |
| saída | `predicoes-recency-lexico.jsonl` | `a490387ca1fb1e092d7fb5f4b69e092df9e3532a09ba1fb68cba7f330e3b12b0` |
| saída | `predicoes-lexico-pares-referencia.jsonl` | `96302629f8bbf260df46fe2f4e0e4b8a4696e1ef61bbd72e2b76e0e654e03676` |

```sh
.venv-experiments/bin/python experiments/evaluate.py
```
