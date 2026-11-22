# Protocolo de anotação v2: menções e teor

Protocolo iniciado em 26/10/2026, revisado após o piloto e atualizado em 12/11/2026. As regras vigentes para partidos, pronomes e normalização estão em D10 a D12 e D15 de [`decisoes-experimentos.md`](decisoes-experimentos.md). D15 revoga explicitamente a antiga permissão de D9 para descrições genéricas de partido. Os demais pontos marcados com **[piloto]** continuam como propostas.

O protocolo da rodada 1 continua em [`protocolo-anotacao.md`](protocolo-anotacao.md). As regras de teor abaixo vêm dele.

As planilhas de Anderson, Beatriz e Nicolas são a referência escolhida para revisar exemplos. As regras escritas prevalecem quando uma dessas planilhas ainda segue a orientação anterior. A escolha não exclui os demais anotadores nem estabelece consenso entre as três planilhas. Para medir concordância independente, usar as respostas anteriores às correções e à resolução de divergências.

## O que você vai fazer

Cada notícia está dividida em parágrafos, na aba `paragrafos` da sua planilha. Leia a notícia inteira, em ordem, e para cada parágrafo:

1. **Menções:** marque cada trecho que se refere a um candidato ou partido da lista e diga a quem ele se refere.
2. **Teor:** para cada candidato ou partido tratado no parágrafo, diga se o texto fala bem, mal ou de forma neutra dele.

Leia a notícia em ordem porque um "ele" no parágrafo 5 pode se referir a alguém citado no parágrafo 2.

## Quem conta

Só quem está na lista suspensa da coluna `candidato`: os candidatos a presidente e a vice e os partidos deles. Qualquer outra pessoa (ministros, juízes, governadores que não são candidatos, políticos de outros países) não é anotada.

Cuidado: Jair Bolsonaro não é candidato, mas o filho dele, Flávio Bolsonaro, é. "Bolsonaro" sozinho só é marcado quando o contexto mostra que é o Flávio. "O ex-presidente" quase sempre é o Jair e não é marcado.

### Partidos

Para partidos da lista, aplicar estas condições às ocorrências do texto original:

- **Nome completo:** considerar a menção ao partido.
- **Nome que também é palavra comum**, como "Missão": considerar somente quando a palavra "partido" vier antes. A palavra isolada não basta.
- **Sigla:** considerar somente com artigo antes. Contrações com artigo contam: "do PT", "ao PL" e "pelo PSB" são aceitas.
- **Sigla entre parênteses:** ignorar a ocorrência, mesmo que o partido esteja na lista.
- **Referência genérica:** não marcar expressões como "o partido", "a legenda" ou "a sigla" como menção a PT ou a qualquer outro partido. Essas expressões, por si só, também não geram linha de teor para um partido.

Em "o PT, Lula (PT)", há uma menção direta a PT: a primeira. Marque apenas "PT", sem o artigo. A segunda ocorrência não entra na anotação. Uma sigla ignorada não gera, por si só, uma linha de teor para o partido.

## Parte 1: menções

### Os dois tipos

| Tipo | O que é | Exemplos |
|---|---|---|
| `DIR` (direta) | nome, sobrenome, apelido ou sigla que satisfaça as condições de partidos acima | "Lula", "Flávio Bolsonaro", "Flávio", "Zema", "PT" em "o PT", "Partido Novo" |
| `IND` (indireta) | pronome admitido ou descrição de uma entidade da lista | "ele", "ela", "dele", "dela", "o presidente", "o candidato", "a candidata", "o petista", "o senador" |

### O que marcar exatamente

- **Direta:** só o nome ou a sigla, sem o cargo. Em "o presidente Lula", marque "Lula".
- **Indireta (descrição):** o artigo e o substantivo, juntos com o adjetivo colado, se houver. Marque "o presidente", "o ex-governador", "a candidata". Não inclua o que vem depois: em "o candidato do PL à Presidência", marque "o candidato" (IND, Flávio) e "PL" (DIR, partido) separadamente. Expressões genéricas de partido como "o partido", "a legenda" e "a sigla" não são descrições anotáveis de nenhuma entidade partidária. **[piloto]**
- **Indireta (pronome):** só "ele", "ela", "dele" e "dela". Não marque "seu", "sua", "o", "a" e "lhe" ("criticou-o", "seu governo"). **[piloto]**
- **Cada ocorrência aceita conta.** Se "Lula" aparece duas vezes no parágrafo, são duas linhas, a segunda com `ocorrencia` = 2. Para partidos, excluir primeiro as ocorrências que não atendem às condições acima. A numeração de `ocorrencia` continua seguindo a posição do trecho no texto original, inclusive quando outra ocorrência igual foi ignorada.

### A quem atribuir o pronome

Atribua cada pronome admitido à entidade anterior mais próxima na mesma notícia. Considere qualquer entidade do escopo já identificada, inclusive partido; não filtre apenas pessoas. Percorra os parágrafos em ordem e não use uma entidade que só apareça depois do pronome.

Em "Lula conversou com o PT. Ele apresentou a proposta", a regra liga "Ele" a PT, porque é a entidade anterior mais próxima. Se não houver entidade anterior identificada, não atribua um candidato por suposição; registre a dúvida em `obs`.

Essa é uma convenção do experimento. Ela pode produzir uma ligação diferente da leitura contextual. Por isso, o acerto de ligação dos pronomes mede a aderência à regra de proximidade e não comprova, sozinho, resolução contextual de correferência.

### Não marque

- **Sujeito oculto:** em "Afirmou que vai recorrer", não há trecho para marcar. Mas, se o parágrafo fala do candidato, ele ganha uma linha de teor (Parte 2). **[piloto]**
- **Pronomes dentro de aspas** que se referem a quem está falando ("eu", "nós"). Em "'Eu vou vencer', disse Lula", marque só "Lula".
- **Apoiadores e grupos:** "os bolsonaristas", "os petistas", "a militância" falam de outras pessoas, não do candidato nem do partido.
- **Expressões que não são o partido:** "Washington, DC", "PL 2630" (projeto de lei), "Go Up". Marque só quando a sigla é o partido.
- **Siglas de partido entre parênteses ou sem artigo anterior**, observadas as contrações aceitas na seção Partidos.

### Casos difíceis

- **"O petista", "o pessebista":** é uma pessoa, então é o candidato a quem se refere, e não o partido. As condições para partidos estão na seção Partidos. **[piloto]**
- **Candidato de passagem** (lista de presença, uma menção rápida): marque a menção mesmo assim. O teor fica neutro se não houver avaliação.
- **Pronome com leitura contextual ambígua:** aplique a entidade anterior mais próxima e explique a dúvida em `obs`, sem trocar silenciosamente a regra por uma interpretação contextual.

### Pontuação e acentos no reconhecimento

O reconhecimento de entidades deve usar uma representação auxiliar sem acentos e com a pontuação substituída por separadores, sem juntar palavras. Aplicar a mesma normalização aos aliases. Assim, "Flávio", "Flávio," e "Flavio" podem ser reconhecidos como o mesmo nome.

Identifique primeiro, no texto original, as siglas entre parênteses que serão ignoradas. Só depois normalize para o reconhecimento. Preserve a correspondência entre posições da representação auxiliar e do original para devolver os trechos com a grafia e os offsets corretos.

Na planilha, continue copiando o trecho do texto original, com seus acentos. Essa regra é um requisito para o reconhecimento experimental, ainda não implementado por esta revisão documental. Ela não manda limpar o texto usado para interpretar ou classificar o teor.

## Parte 2: teor

### Quando preencher

Uma linha na aba `teor` para cada candidato ou partido que o parágrafo trata, mesmo que só por menção indireta ou sujeito oculto. Se marcou uma menção a alguém na Parte 1, ele precisa de uma linha de teor naquele parágrafo. Uma referência genérica como "o partido", "a legenda" ou "a sigla", sem uma menção elegível que identifique o partido, não gera linha de teor para partido.

### As quatro opções

| Teor | Quando | Exemplo |
|---|---|---|
| `positivo` | o texto fala bem dele | "Economistas elogiaram a reforma de Lula." |
| `negativo` | o texto fala mal dele | "Lula foi criticado pela oposição." |
| `neutro` | o texto só informa, sem avaliar | "Lula participou do evento." |
| `indeterminado` | não dá para decidir: o trecho é ambíguo ou fala bem e mal ao mesmo tempo | use pouco, e explique em `obs` |

O teor é **por candidato**. O mesmo parágrafo pode ser positivo para um e negativo para outro: em "Lula foi aplaudido e Flávio foi vaiado", é positivo para o Lula e negativo para o Flávio.

### Regras

1. **A avaliação tem que estar escrita.** Um fato que você acha bom ou ruim é neutro. "O governo reabriu 40 fábricas" é neutro. "A política econômica foi um fracasso" é negativo.
2. **Negação inverte.** "Não apoiou a medida" não é positivo por causa de "apoiou".
3. **Ironia vale pelo sentido real.** "Genial, mais um escândalo do governo" é negativo.
4. **Falar bem de si mesmo é neutro.** Só conta quando alguém de fora avalia. "O candidato citou as obras da gestão dele" é neutro.
5. **Fala de terceiros conta.** "Para o economista, a gestão de Zema foi um fracasso" é negativo para o Zema.
6. **Quem critica não é criticado.** Em "Renan Santos criticou Flávio", é negativo para o Flávio e neutro para o Renan.
7. **Aplauso e vaia contam como avaliação.** "Foi aplaudido de pé" é positivo; "foi vaiado" é negativo.
8. **Vítima não é avaliação.** "O candidato foi alvo de ataques" é neutro, a menos que o parágrafo também avalie ele.
9. **Crítica à medida conta para o autor.** "O projeto do senador foi criticado" é negativo para ele. Se ele só participou da discussão, é neutro.
10. **Sigla de partido entre parênteses:** em "Flávio Bolsonaro (PL) foi criticado", é negativo para Flávio. Não criar menção nem teor para PL com base apenas em "(PL)". Outra referência aceita ao partido no mesmo parágrafo pode justificar uma linha própria de teor.
11. **Resultado de investigação sem julgamento é neutro.** Só muda se alguém criticar ou elogiar o resultado.
12. **Comparação com figura muito admirada é elogio.** "Joga como o Pelé" é positivo.

## Como preencher a planilha

| Aba | O que fazer |
|---|---|
| `paragrafos` | só leitura: os parágrafos de cada notícia, em ordem |
| `mencoes` | uma linha por menção: `paragraph_id`, `trecho` (copiado do parágrafo, igual), `ocorrencia` (só quando o trecho aparece mais de uma vez no parágrafo; 1 = primeira), `tipo`, `candidato`, `obs` |
| `teor` | uma linha por candidato tratado no parágrafo: `paragraph_id`, `candidato`, `teor`, `obs` |
| `tempo` | quantos minutos você levou em cada notícia |

Copie o trecho do texto do parágrafo, não digite de cabeça. Se o trecho não for encontrado, o script de validação aponta a linha para você corrigir.

### Exemplo

Parágrafo inventado `159-3`: "Lula discursou em Recife. O presidente foi aplaudido e disse que Flávio Bolsonaro não tem propostas. Ele também criticou o PL."

Aba `mencoes`:

| paragraph_id | trecho | ocorrencia | tipo | candidato |
|---|---|---|---|---|
| 159-3 | Lula | | DIR | LUIZ INÁCIO LULA DA SILVA |
| 159-3 | O presidente | | IND | LUIZ INÁCIO LULA DA SILVA |
| 159-3 | Flávio Bolsonaro | | DIR | FLAVIO NANTES BOLSONARO |
| 159-3 | Ele | | IND | FLAVIO NANTES BOLSONARO |
| 159-3 | PL | | DIR | PARTIDO LIBERAL |

Aba `teor`:

| paragraph_id | candidato | teor | por quê |
|---|---|---|---|
| 159-3 | LUIZ INÁCIO LULA DA SILVA | positivo | foi aplaudido (regra 7); quem critica não é criticado (regra 6) |
| 159-3 | FLAVIO NANTES BOLSONARO | negativo | Lula diz que ele não tem propostas (regra 5) |
| 159-3 | PARTIDO LIBERAL | negativo | alvo da crítica na última frase (regra 5) |

"Ele" foi ligado a Flávio pela regra de entidade anterior mais próxima. O exemplo mostra a convenção de anotação; não afirma que essa seja a única leitura contextual possível.

## Na dúvida

Não trave. Escolha a opção mais provável, escreva a dúvida em `obs` e siga. As dúvidas do piloto viram regras novas neste documento.
