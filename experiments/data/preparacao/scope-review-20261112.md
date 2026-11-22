# Revisão de foco das 60 candidatas

Registro de 12/11/2026, após Bea determinar a substituição do ID 129 e das notícias voltadas a entidades ausentes da lista do experimento. A autorização foi aplicada ao conteúdo das notícias; Bea não aprovou individualmente os demais IDs desta revisão.

Foram examinados os títulos das 60 candidatas e os textos integrais dos 11 casos do [relatório anterior](scope-review.md), além de 20 casos adicionais ou duvidosos. A classificação usa o [CSV bruto](../../../data/raw/articles_202608191040.csv), o [snapshot de entidades](../entidades.yaml), a [lista de candidatas](candidate_ids.txt) e as [atribuições atuais](assignments.csv). Trata-se de revisão realizada pelo assistente, ainda sem confirmação independente pela equipe; não verifica a veracidade factual das notícias.

Resultado: 20 IDs com foco fora do escopo para substituição; seis com foco misto aguardando decisão; 34 mantidos nesta revisão. A existência de menção direta no matcher não basta para decidir o foco. Identificações partidárias, referências incidentais e chamadas de outras matérias podem produzir correspondências sem tornar uma entidade da lista o assunto da notícia.

Os CSVs, listas de atribuição e metadados históricos permanecem como estavam. O arquivo [substituicoes-solicitadas-20261112.txt](substituicoes-solicitadas-20261112.txt) contém somente os 20 IDs classificados para substituição, na ordem em que aparecem na amostra. A seleção das substitutas e a transformação dos arquivos ainda dependem de execução por Bea.

## Substituições abrangidas pela decisão de Bea

“Exclusiva 1”, por exemplo, indica a primeira notícia exclusiva daquele anotador, depois das seis compartilhadas. As referências ao conteúdo abaixo são paráfrases, salvo trechos entre aspas.

| ID | Posição atual | Evidência de foco fora do snapshot |
|---:|---|---|
| 438 | Compartilhada 2 | Meta deve identificar financiadores de ataques a Tarcísio. PT aparece perto do fim, identificando deputados envolvidos em outros processos. |
| 129 | Compartilhada 5 | Candidatura de Michelle ao Senado e apoio a Celina. Flávio aparece incidentalmente. Substituição explicitamente solicitada por Bea; o texto também contém mojibake. |
| 297 | Anderson, exclusiva 1 | Patrimônio de Haddad e comparação com patrimônio de Tarcísio. |
| 530 | Lucas, exclusiva 1 | Pesquisa sobre governo do DF e Senado, com Michelle e Celina. A ocorrência “o PL confirmar sua candidatura” identifica o partido de Michelle; o foco são as disputas locais. |
| 364 | Beatriz, exclusiva 2 | Haddad questiona a abordagem da PM ao motorista; o texto acompanha a disputa estadual. |
| 154 | Beatriz, exclusiva 3 | “O impacto da prisão de Jair Bolsonaro na campanha de Michelle”. A última frase menciona a campanha de Flávio, mas o assunto é a disponibilidade de Michelle para fazer campanha. |
| 351 | Lucas, exclusiva 3 | Haddad denuncia intimidação ao motorista e cobra Tarcísio. “Candidato do PT” identifica Haddad, sem discussão partidária própria. |
| 490 | Nicolas, exclusiva 3 | O texto curto resume acusações entre candidatos ao governo mineiro; só uma frase menciona apoio de Cleitinho a Flávio. O objeto é o debate estadual. |
| 528 | Lucas, exclusiva 4 | Registro de candidatura e patrimônio de Michelle; apresentação do suplente Diego Torres. |
| 538 | Anderson, exclusiva 5 | Michelle mobiliza apoiadores para Celina no DF. |
| 117 | Nicolas, exclusiva 5 | Disputa entre Roosevelt Vilela e Eduardo Torres pelo número 22.222 na eleição distrital. Flávio aparece para explicar a associação do número; o PL organiza candidaturas, mas o foco é o conflito entre candidatos externos ao snapshot. |
| 107 | Beatriz, exclusiva 6 | “Michelle Bolsonaro declara R$ 4,48 milhões ao TSE”. Flávio surge em dois parágrafos de contexto sobre desentendimentos familiares. |
| 394 | Gustavo, exclusiva 6 | Tarcísio comenta investigação envolvendo o motorista de Haddad. |
| 341 | Lucas, exclusiva 6 | Tarcísio, Haddad e a investigação da suposta perseguição pela PM. |
| 423 | Anderson, exclusiva 7 | Apoio de prefeitos à reeleição de Tarcísio. |
| 323 | Nicolas, exclusiva 7 | Haddad acusa comandante da PM e critica Tarcísio; segurança pública paulista. “Candidato do PT” fornece uma referência ao partido, mas identifica Haddad. |
| 395 | Gustavo, exclusiva 8 | Campanha de Tarcísio e propostas estaduais para mulheres. |
| 407 | Nicolas, exclusiva 8 | Propostas estaduais de Tarcísio para menopausa e saúde. |
| 290 | Lucas, exclusiva 9 | Nunes defende a reeleição de Tarcísio contra Haddad. |
| 327 | Nicolas, exclusiva 9 | Investigação da suposta perseguição ao motorista de Haddad. Chamadas de outras matérias, inseridas no texto extraído, citam Lula, Alckmin e Flávio; essas chamadas não constituem o assunto central. |

As substituições ocupam duas vagas compartilhadas e 18 exclusivas: Anderson 3, Beatriz 3, Cristovam 0, Gustavo 2, Lucas 5 e Nicolas 5. Preservar cada posição mantém a carga planejada de seis compartilhadas e nove exclusivas por anotador.

## Casos mistos aguardando decisão

Estes seis IDs não integram o arquivo de substituições. As recomendações da tabela dependem de como a equipe definir o foco suficiente para elegibilidade.

| ID | Posição atual | Evidência e entidades | Encaminhamento |
|---:|---|---|---|
| 408 | Compartilhada 4 | Título e lead tratam da confirmação da candidatura de Tarcísio à reeleição. O corpo dedica vários parágrafos ao apoio a Flávio, à ausência de Kassab e à candidatura de Caiado. Flávio, Kassab, Caiado, Lula e partidos citados constam do snapshot; Tarcísio e Haddad não. | Recomenda-se substituir se prevalecer o foco principal do evento estadual, registrando a presença de cobertura presidencial substancial. |
| 435 | Nicolas, exclusiva 2 | Sabatina com Tarcísio sobre segurança, Sabesp, impostos e empresas dos filhos. Há seção própria sobre Flávio e avaliações de Lula; ambos constam do snapshot, assim como PT. | Recomenda-se substituir se prevalecer o entrevistado e o assunto principal estadual. Há trechos relevantes para teor sobre presidenciáveis. |
| 406 | Gustavo, exclusiva 1 | Aval da Fazenda a empréstimo para SP após ação de Tarcísio. O corpo aborda críticas de Flávio e a resposta do governo Lula; os dois estão no snapshot. Tarcísio, Haddad e Dario Durigan estão fora. | Revisar se a disputa entre administração estadual e governo Lula oferece foco suficiente em entidade elegível. |
| 418 | Nicolas, exclusiva 6 | Mesmo empréstimo: o lead diz que a gestão paulista acusava o governo Lula de demora. Há críticas de Flávio e resposta federal. Lula, Flávio e PT constam da lista; Tarcísio e Haddad não. O texto tem mojibake. | Mesma decisão de foco necessária para 406. Não há autorização geral para excluir automaticamente todo texto com mojibake. |
| 373 | Gustavo, exclusiva 3 | Convenção do PT que lança Haddad, com discurso de Lula, críticas a Flávio e trajetória de Haddad. PT organiza o evento e é entidade do snapshot; Lula, Alckmin e Flávio também estão na lista. Haddad está fora. | Recomenda-se manter se ações dos partidos listados forem elegíveis mesmo quando envolvem eleição estadual. A exclusão apenas pelo nome de Haddad descartaria também cobertura central do PT. |
| 457 | Anderson, exclusiva 6 | Título e primeiros parágrafos tratam do apoio de Cleitinho a Flávio. A maior parte do restante resume propostas e conflitos do debate estadual mineiro. Flávio e PL constam da lista; Cleitinho, Roscoe, Simões, Kalil e Gabriel Azevedo não. | Definir se um assunto central no título/lead é suficiente ou se prevalece o conteúdo predominante do corpo. |

## Mantidas nesta revisão

Os 34 IDs abaixo apresentam foco ou cofoco defensável em entidades do snapshot. A classificação não substitui a anotação completa nem certifica a qualidade da extração de todos os textos.

`5, 498, 73, 183, 95, 344, 219, 63, 52, 91, 6, 240, 163, 221, 16, 10, 506, 81, 235, 510, 142, 82, 458, 455, 281, 72, 118, 8, 244, 155, 431, 280, 58, 97`.

Alguns casos com pessoas externas ao snapshot foram mantidos pela participação central de entidades elegíveis:

- 344 tem Haddad no título, mas o corpo trata sobretudo da trajetória, gestão e campanha de Lula, elogiadas por Haddad.
- 431 trata da rejeição de Flávio e das agendas conjuntas com Tarcísio; Flávio é objeto central da cobertura.
- 458 é predominantemente sobre apoio a Flávio; o relato estadual é breve.
- 10 trata da estratégia do PT e da associação com o governo Lula.
- 221 trata de articulação do PSB com participação de Alckmin.

## Aplicação da revisão

Para preservar o sorteio, recomenda-se continuar a mesma permutação do pool histórico de 314 notícias, semente 42, a partir da posição 61. As novas candidatas devem ser revisadas na ordem sorteada, com registro dos aceites e recusas. Não selecionar substitutas pela facilidade de reconhecimento, pelo teor ou pelo desempenho de qualquer sistema.

Cada notícia aceita deve ocupar a posição da removida. A conferência posterior deve abranger 60 IDs únicos, seis notícias compartilhadas, nove exclusivas por anotador, 90 atribuições, ausência dos IDs removidos e de coincidências com rodada 1, piloto ou duplicatas por URL/texto. Guardar a seleção anterior e registrar hashes das entradas, saídas e decisões de revisão.

Esta etapa não executou scripts ou testes nem produziu uma amostra substituta. Conforme instrução de Bea, a execução será feita por ela a partir de um comando fornecido pelo assistente; os resultados deverão ser conferidos em seguida.
