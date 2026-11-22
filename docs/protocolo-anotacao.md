# Protocolo de anotação — classificação de teor por entidade

Guia para quem for rotular parágrafos manualmente, usado para gerar o conjunto de treino/validação/teste do Classifier (LSTM, fase 2). Baseado nas definições já estabelecidas em `context.md` (raiz), seções 2, 3, 5, 9, 10, 11 e 14 — este documento não inventa critério novo, só operacionaliza o que já foi decidido para quem nunca leu o `context.md`.

## O que você está classificando

Para cada linha que você for anotar, você recebe:

- um **parágrafo** de uma notícia;
- o **nome do político ou partido** que o sistema identificou nesse parágrafo (a entidade-alvo).

Sua tarefa: decidir se **aquele parágrafo, especificamente em relação àquele político/partido**, é:

- **neutro**
- **negativo**
- **positivo**

## O que NÃO estamos classificando

- **Não é viés político.** Não estamos avaliando se o político é de esquerda, direita, centro, nem se a notícia "parece" tendenciosa ideologicamente. Ignore sua opinião pessoal sobre o político — a tarefa é só: o texto fala bem, mal, ou de forma neutra sobre ele?
- **Não é se a acusação é verdadeira.** Se o parágrafo diz "o prefeito foi acusado de corrupção", isso é **negativo** independente de a acusação ser verdadeira ou não. Você está classificando o que o texto diz, não julgando os fatos.
- **Não é sobre o assunto/política em si.** Se o parágrafo fala mal de uma lei sem ligar isso ao político especificamente, pode não ser negativo para a pessoa (ver regra 5 abaixo).

## As 3 categorias, com exemplo

### Neutro
Informa ou descreve, sem elogio nem crítica clara à pessoa/partido.

> "O senador Carlos participará da sessão de votação marcada para quinta-feira."

> "A prefeita visitou a obra do novo hospital na manhã de terça."

### Negativo
Critica, acusa, reprova, ou associa a pessoa/partido a algo desfavorável.

> "A deputada foi duramente criticada por especialistas após o discurso."

> "O partido é investigado por suspeita de irregularidade no uso de verba de campanha."

### Positivo
Elogia, aprova, ou associa a pessoa/partido a algo favorável.

> "O governador foi elogiado pela rapidez na resposta à enchente."

> "A proposta do vereador teve ampla aprovação entre os moradores do bairro."

## Casos difíceis — leia com atenção, é aqui que a maioria dos erros acontece

### 1. Negação inverte o sentido
"O governo **não** apoiou a medida" não é positivo só porque tem a palavra "apoiou". Leia a frase inteira, não palavra por palavra.

### 2. Ironia/sarcasmo — classifique o sentido real, não o literal
> "Genial, mais um escândalo do governo."
Isso é sarcasmo — classifique como **negativo**, mesmo que "genial" pareça uma palavra positiva.

### 3. Julgamento precisa ser explícito — não vale o que você, leitor, acha que é bom ou ruim
Só classifique **positivo**/**negativo** quando houver uma palavra ou frase de avaliação real no texto: elogio, crítica, "fracasso", "sucesso", "escândalo", "medíocre", "não conseguiu provar isso quando governou". Um fato que você, como leitor, interpreta como bom ou ruim por conta própria não conta — isso é viés seu, não o texto falando.

> "A política econômica do governo foi um fracasso." → negativo ("fracasso" é o julgamento explícito, está escrito)

> "O governo reabriu 40 fábricas durante a gestão." → neutro. Você pode achar isso positivo, mas o parágrafo só descreve um fato — ninguém ali está avaliando isso como bom. Pode existir gente que não ache isso positivo. Não infira a avaliação: exija que ela esteja no texto.

Essa é a regra-base por trás de vários casos difíceis abaixo — releia esta seção sempre que ficar em dúvida se algo é "só um fato" ou "um julgamento".

### 4. Autocitação não é elogio de terceiro
Se a própria entidade fala bem de si mesma — lista conquistas, cita obras da própria gestão, descreve a própria ação/fala — sem que ninguém de fora avalie isso, é **neutro**. Só vira positivo/negativo quando alguém DE FORA avalia explicitamente (ver regra 3 acima).

> "O vice-governador citou as fábricas reabertas durante sua gestão." → neutro. Ele está falando de coisas boas que fez, mas quem fala é ele mesmo — não há ninguém de fora elogiando.

> "Os moradores elogiaram o vice-governador pelas fábricas reabertas durante sua gestão." → positivo. Agora quem avalia é um terceiro ("os moradores"), não a própria entidade.

### 5. Crítica à medida/decisão vs. crítica à pessoa vs. crítica ao partido dela
- Se o político é claramente o autor/responsável pela medida criticada → **negativo** para ele.
  > "O projeto de lei do senador foi amplamente criticado por juristas." → negativo (o projeto é dele, a crítica recai sobre ele)
- Se o político só é citado de passagem perto de uma discussão sobre política pública, sem ligação direta de autoria → normalmente **neutro**.
  > "O senador participou da audiência sobre a nova lei de trânsito, que divide opiniões." → neutro (ele não é o autor, só participou)
- Se a entidade da linha é um **partido** citado só como sigla entre parênteses ao lado do nome de uma pessoa, e a crítica/elogio do parágrafo é claramente dirigida à pessoa — não ao partido como instituição — classifique **neutro** para a linha do partido, mesmo que a sigla apareça tecnicamente no texto.
  > "Renan Santos criticou duramente o senador Flávio Bolsonaro (PL) durante o evento." → negativo para Flávio Bolsonaro; **neutro para o PL** — o "(PL)" ali é só a filiação partidária entre parênteses, quem está sendo criticado é a pessoa.

### 6. Vítima de um evento negativo ≠ avaliação negativa da pessoa
> "O prefeito foi alvo de um atentado na última semana."
Isso é sobre algo ruim que **aconteceu com** ele, não uma crítica **a** ele. Classifique como **neutro** (a menos que o parágrafo também inclua uma avaliação, positiva ou negativa, sobre ele).

### 7. Fala de terceiros também conta
Se o parágrafo cita a opinião de outra pessoa sobre o político, classifique pelo que está sendo dito sobre a entidade no parágrafo — não importa se é a opinião do jornalista ou de alguém citado.
> "Para o economista Fulano, a política econômica do governador foi um fracasso." → negativo (o parágrafo carrega uma crítica ao governador, ainda que atribuída a outra pessoa)

### 8. Reação de plateia/público também é avaliação de terceiro
Aplausos, vaias, ser "contestado aos gritos", uma torcida cantando o nome de alguém — tudo isso conta como avaliação de terceiro, mesmo sem uma frase explícita do tipo "Fulano foi elogiado/criticado por X".

> "O prefeito foi aplaudido de pé ao anunciar a medida." → positivo (o aplauso é a avaliação de terceiro, mesmo sem ninguém "dizer" que ele foi bem)

> "O deputado foi vaiado e contestado aos gritos pela plateia durante o discurso." → negativo

### 9. Comparação metafórica explícita com figura amplamente positiva conta como elogio
Se o parágrafo compara a entidade a uma figura reconhecidamente positiva, isso é elogio de terceiro — mesmo vindo com ressalva ou humildade no meio ("é difícil comparar, mas...").

> "É difícil comparar qualquer um ao Pelé, mas o pai jogava desse jeito" — dito por um filho sobre o pai político. → positivo para o pai. A ressalva não anula a comparação, ela é só humildade de quem fala; a comparação com uma figura amplamente celebrada é o elogio.

### 10. Resultado de apuração/investigação sem julgamento explícito é neutro
Relatar o resultado factual de uma apuração, investigação ou perícia — mesmo que ele contradiga uma versão anterior dos fatos — é **neutro**, a menos que alguém critique ou elogie expressamente esse resultado (regra 3). Contradizer uma versão não é o mesmo que avaliar negativamente.

> "A apuração não identificou indícios de procedimento irregular por parte do policial." → neutro (resultado factual, sem julgamento)

> "A perícia encontrou divergências entre o relato da vítima e as imagens do circuito interno." → neutro, mesmo contradizendo o relato anterior — ninguém no parágrafo está avaliando isso como bom ou ruim para a entidade.

> "Especialistas criticaram a demora da apuração em concluir o caso." → negativo — aqui há julgamento explícito ("criticaram").

### 11. Duas entidades no mesmo parágrafo
Você pode receber o mesmo parágrafo duas vezes, uma para cada político citado nele. Classifique cada linha considerando **só a entidade indicada naquela linha**, mesmo que o parágrafo fale de outra pessoa também.
> "Enquanto o deputado João defendeu o projeto, a senadora Ana o classificou como um retrocesso."
> - Linha para João → positivo
> - Linha para Ana → não é sobre Ana ser criticada, é sobre a opinião DELA sobre o projeto — aqui não há avaliação sobre Ana em si, então neutro para Ana (ela não foi elogiada nem criticada, ela é quem está criticando)

## Quando você não souber

Não force uma categoria. Se o parágrafo for genuinamente ambíguo, contraditório (fala bem e mal ao mesmo tempo sobre a mesma pessoa) ou você não conseguir decidir com confiança, marque **"indeterminado"** em vez de chutar. Isso é mais útil pra gente do que um rótulo errado — vamos analisar depois quantos casos caíram aqui pra decidir se vira uma categoria de verdade ou é só ruído a descartar.

Se o parágrafo, na verdade, não fala nada de relevante sobre a entidade indicada (o sistema identificou o nome por engano, ou é uma menção incidental tipo lista de presença), marque **"não relacionado"** — isso nos ajuda a melhorar a identificação de entidade também, é um sinal útil.

## Intensidade (opcional, experimental)

Além do `label`, se você tiver segurança pra isso, preencha também `intensity`: uma nota de 1 a 5 pra quão forte é o sentimento, não uma categoria nova.

- **1** = levemente negativo · **2** = moderadamente negativo · **3** = fortemente negativo
- Espelhado pro lado positivo: quanto mais perto de 1, mais leve; quanto mais perto de 5 (dentro da mesma direção do `label`), mais forte/inequívoco.

Isso é **só coleta de dado pra decidir depois** se vale a pena o produto usar uma escala assim no lugar de (ou junto com) as 3 categorias — não é o rótulo que o sistema usa hoje. Regras:

- Só preencha `intensity` quando `label` for `negativo` ou `positivo`. Deixe em branco para `neutro`, `indeterminado` e `nao_relacionado` — intensidade de neutro não tem sentido.
- Se estiver em dúvida sobre a intensidade, deixe em branco em vez de chutar — assim como no `label`, um campo vazio é mais útil pra gente do que um número arbitrário.
- Não deixe a dúvida sobre intensidade atrasar ou travar sua decisão do `label` — o `label` é o que importa primeiro.

## Como preencher

Planilha com uma linha por (parágrafo, entidade). Colunas:

| Coluna | O que colocar |
|---|---|
| `paragraph_id` | já preenchido, não mexer |
| `entity_name` | já preenchido — é a entidade que você está avaliando nessa linha |
| `paragraph_text` | já preenchido — o texto a ler |
| `label` | `neutro` / `negativo` / `positivo` / `indeterminado` / `nao_relacionado` |
| `intensity` (opcional) | 1 a 5, só quando `label` for `negativo` ou `positivo` — ver seção "Intensidade" acima |
| `notes` (opcional) | qualquer dúvida ou justificativa que ache importante registrar |

## Antes de começar

Leia este documento inteiro uma vez. Se tiver dúvida em algum caso enquanto anota, marque `notes` explicando a dúvida em vez de travar — a gente revisa os casos com nota depois, em conjunto.
