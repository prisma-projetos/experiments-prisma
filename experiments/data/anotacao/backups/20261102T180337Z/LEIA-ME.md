# Revisão das planilhas do piloto

Esta pasta guarda cópias byte a byte das cinco planilhas antes da revisão de 02/11/2026. Os arquivos revisados estão em `../../piloto/`. A planilha de Anderson não foi alterada.

Para medir concordância entre anotadores, use as respostas originais preservadas aqui, junto da versão independente de Anderson. As planilhas revisadas receberam intervenções automáticas e não representam mais anotações independentes. Guarde a concordância anterior à adjudicação separada do consenso final.

`alteracoes.json` registra arquivo, célula, valor anterior, valor final e motivo. Em `archived_rows` estão as linhas retiradas da tabela, com suas observações originais. Algumas posições vazias foram reutilizadas para menções verificadas no texto; o registro permite distinguir a anotação anterior da nova. `validacao.json` contém hashes e contagens finais.

## O que foi ajustado

- Limites de trechos, tipos diretos, ocorrências repetidas e menções explícitas omitidas, conferidas no CSV do piloto.
- Teores de pares omitidos e casos previstos no protocolo, como autoelogio e informação factual. A atribuição explícita de corrupção ao PT em 175-9 foi registrada como negativa.
- Retirada da atribuição de PcdoB ao PCB, da duplicata de teor de Flávio em 145-4 e dos verbos usados como menção de sujeito oculto. O teor foi preservado quando aplicável. Em 145-8, a descrição explícita "o único candidato" substituiu o verbo ou a oração inteira.
- Linhas sem campos de anotação foram retiradas das tabelas. Seus textos e observações continuam no registro e nas cópias originais. Isso não comprova que o parágrafo não tenha entidades; as omissões explícitas identificadas foram preenchidas, e as dúvidas de escopo continuam abaixo.
- Ordem das colunas de `paragrafos` da Beatriz restaurada. Aba `tempo` padronizada para `article_id`, `titulo`, `minutos`, `obs`, com títulos e durações existentes preservados. Cristovam e Nicolas receberam a aba com durações vazias. Os títulos ganharam quebra de linha e altura para leitura.

Os 92 parágrafos e seus textos foram preservados. Também foram preservadas listas de entidades, proteções, abas ocultas, validações e formatação fora dos ajustes de layout descritos. A exportação do Artifact Tool foi combinada com os componentes originais do XLSX, pois uma exportação simples removia a proteção de `paragrafos` e tornava `listas` visível.

## Pendências para a equipe

As decisões abaixo foram preservadas, sem impor uma interpretação comum:

- Contrações em "do senador": escolher um limite único de trecho e aplicá-lo a todos.
- Descrições iniciadas por possessivo, como "seu filho", "seu vice" e "seu principal adversário"; a exclusão do pronome isolado não define claramente a descrição completa.
- Cargo junto de nome e expressões coordenadas, como "O senador e candidato"; decidir se há uma indireta separada além da direta.
- Referências a governo, gestão e campanha; decidir quando se ligam à pessoa e quando ficam apenas no teor contextual.
- Metáfora "o filho do Pelé", predicativo "o partido" e referência coletiva "desses partidos".
- Na planilha de Nicolas, revisar "ameaça bolsonarista" em 145-10 e "argumentos petistas" em 160-21: não está estabelecido que esses grupos/expressões devam ser ligados à pessoa ou partido. As atribuições e os teores originais foram preservados para discussão.
- Elogio de avatar produzido pela própria campanha em 160-7: definir se conta como avaliação externa. Revisar também o teor do PL em 160-18 e demais divergências de teor antes de formar consenso.
- Rever os teores contextuais sem nome explícito, inclusive 159-3 e 160-31 a 160-38. Uma validação técnica sem erros não resolve essas decisões semânticas.

Faltam 13 durações: Beatriz nos artigos 146, 160 e 175; Cristovam e Nicolas nos cinco artigos. Manter vazio se o tempo não foi medido, sem estimá-lo retroativamente como se fosse observado.

## Resultado da validação

| Planilha revisada | Menções | Pares de teor | Erros técnicos | Durações ausentes |
|---|---:|---:|---:|---:|
| Lucas | 102 | 85 | 0 | 0 |
| Beatriz | 109 | 88 | 0 | 3 |
| Cristovam | 100 | 89 | 0 | 5 |
| Gustavo | 102 | 95 | 0 | 0 |
| Nicolas | 118 | 91 | 0 | 5 |

O piloto continua fora do treino e do teste. Após resolver as pendências, registrar as regras acordadas no protocolo antes de iniciar a anotação definitiva.
