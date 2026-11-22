# Registro de decisões dos experimentos do artigo

Cada decisão de método tem data, o que foi escolhido, o motivo e o que ficou de fora. Serve de fonte para a seção de método e para as limitações do artigo. Decisão nova entra no fim; decisão revista ganha uma entrada nova apontando a antiga, sem apagar.

Plano completo: [`plano-implementacao-experimentos.md`](plano-implementacao-experimentos.md).

---

## D1. Anotação em planilha com validador (26/10/2026)

**Escolha:** cada anotador recebe uma planilha (.xlsx) com os parágrafos já segmentados, uma aba de menções (parágrafo, trecho, ocorrência, tipo, candidato) e uma aba de teor (parágrafo, candidato, teor). Um script localiza cada trecho no parágrafo, calcula os offsets e aponta os erros de cada anotador.

**Por quê:** a anotação começa em 27/10, e não havia tempo para montar e testar uma ferramenta hospedada. A planilha não exige infraestrutura nem treinamento, e as listas suspensas e o validador evitam o erro principal dela, que é digitar errado o trecho ou o candidato.

**Alternativa descartada:** Label Studio na VPS. Exporta offsets prontos e facilita marcar trechos, mas exigiria subir o serviço, criar acessos para seis pessoas e expor uma porta num servidor compartilhado com a produção, tudo em um dia.

**Para o artigo:** descrever a anotação como "planilha com validação automática dos trechos". Custo conhecido: o anotador digita o trecho em vez de selecioná-lo, então os limites do trecho dependem do protocolo (ver regras de limite).

## D2. REM: BERTimbau detecta, a ligação usa aliases e menção mais recente (26/10/2026)

**Escolha:** o BERTimbau de REM é um etiquetador de tokens (BIO) com duas etiquetas, `DIR` (menção direta) e `IND` (indireta). Ele detecta os trechos e não decide o candidato. Trechos `DIR` são ligados ao candidato pelos aliases, com o mesmo critério do matcher de produção. Trechos `IND` são ligados pela regra da menção mais recente, a mesma da baseline.

**Por quê:** um etiquetador BIO não tem como escolher entre 40 candidatos. Fazer a ligação com um modelo exigiria um segundo treino em CPU no período de 01 a 05/11, que já tem dois. Como a baseline de menção mais recente e o BERTimbau usam a mesma ligação, a diferença entre eles mede só a detecção, e o acerto da ligação é reportado à parte.

**Alternativa descartada (trabalho futuro):** classificador de pares (trecho marcado, candidato citado antes na notícia), treinado para responder se o trecho se refere ao candidato.

**Para o artigo:** o sistema C e o D medem o ganho de detectar menções indiretas, e não o de resolvê-las melhor que a heurística. A ligação dos indiretos herda a limitação da menção mais recente, que erra quando a notícia alterna entre dois candidatos.

## D3. Divisão 65/10/25 por notícia, com as compartilhadas no teste (26/10/2026)

**Escolha:** o gabarito é dividido por notícia, nunca por parágrafo: 65% treino, 10% validação, 25% teste. As 6 notícias anotadas por todos entram no teste. Todas as tabelas levam intervalo de confiança por bootstrap reamostrando notícias.

**Por quê:** com 70/15/15, o teste teria 9 notícias, cerca de 150 parágrafos (média medida no corpus: 17 parágrafos por notícia), e poucas dezenas de pares positivos e negativos. Diferenças pequenas de F1 entre sistemas não seriam interpretáveis. A validação só serve para escolher a época, porque o BERTimbau roda com a configuração-padrão, então pode encolher. O treino de teor ainda recebe os 1.054 pares da rodada 1. As notícias compartilhadas têm o rótulo mais confiável, porque passam pela resolução de divergências. O bootstrap é por notícia porque parágrafos da mesma notícia não são independentes.

**Alternativa descartada:** 70/15/15, como no documento de planejamento original.

**Para o artigo:** informar o tamanho do teste em notícias, parágrafos e pares, e apresentar os resultados com intervalo de confiança.

## D4. Lista de entidades congelada (26/10/2026)

**Escolha:** os experimentos usam um arquivo fixo com as 40 entidades (candidatos a presidente e vice e seus partidos) e os aliases delas, gerado por `scripts/export_target_entities.py`. O piloto usa o export de 29/08/2026; o gabarito final usa um export novo, feito antes de congelar o teste.

**Por quê:** a produção lê as entidades do banco (`entidade_matching`), que muda sem aviso. Se a lista mudar no meio do experimento, os resultados dos sistemas deixam de ser comparáveis.

**Para o artigo:** citar a data do export e o número de entidades e aliases.

## D5. Segmentação de produção (26/10/2026)

**Escolha:** o gabarito é segmentado com `src/segmentation.py`, sem mudança.

**Por quê:** o sistema A precisa ser idêntico ao que roda em produção, e os índices de parágrafo do gabarito precisam bater com os dele.

**Para o artigo:** limitação conhecida: itens de lista e linhas de tabela viram parágrafos soltos.

## D6. Regras técnicas do validador da planilha (26/10/2026)

Implementadas em `experiments/gold.py`. Não mudam o protocolo, só como a planilha vira gabarito.

- **Texto relido da fonte:** o validador ignora o texto da aba `paragrafos` e regenera os parágrafos a partir do CSV bruto com `segment()`. Motivo: o anotador pode alterar a aba sem querer, e o gabarito tem que bater com o que os sistemas leem.
- **Localização do trecho:** primeiro busca exata; só se não houver nenhuma ocorrência exata, busca ignorando maiúsculas e espaços duplicados, e isso gera aviso. Sem busca aproximada (fuzzy). Motivo: não corrigir o anotador quando o texto existe como ele digitou, e não aceitar trecho que não está no parágrafo. O trecho gravado é sempre o do parágrafo original. Limite conhecido: se o anotador digita "o documento" querendo "O documento", vale a ocorrência minúscula, sem aviso.
- **`ocorrencia` só é obrigatória quando o trecho se repete** no parágrafo. Motivo: reduzir trabalho do anotador no caso comum.
- **Linha com erro sai inteira do gabarito** e aparece no relatório; teor duplicado mantém a primeira linha e marca as outras como erro. Motivo: nada ambíguo entra no gabarito sem alguém decidir.
- **Split:** IDs ordenados antes de embaralhar (semente 42), cotas por `round()` (com 60 notícias: 39 treino, 6 validação, 15 teste). Motivo: o resultado não depende da ordem do arquivo de entrada e é reproduzível.

## D7. Notícias do piloto (26/10/2026)

**Escolha:** piloto com as notícias 145, 159, 146, 160 e 175 (92 parágrafos ao todo), escolhidas pelo Gustavo no banco `prisma-scrapping-dev`. Lista em `experiments/data/piloto_ids.txt`. As planilhas foram geradas a partir do CSV de 19/08/2026 (`data/raw/articles_202608191040.csv`).

**Por quê:** o piloto serve para ajustar o protocolo e medir o tempo por notícia, e fica fora do gabarito. A notícia 145 é da rodada 1, uma exceção à regra de usar só as reservadas. Ela foi mantida porque o piloto não entra em treino nem em teste, então não há vazamento.

**Cuidados:** as cinco notícias do piloto não podem entrar na amostra das 60. A 160 tem 39 parágrafos, quase três vezes as outras, então o tempo por notícia medido no piloto deve ser informado também por parágrafo. Pendente: confirmar que os IDs do banco dev são as mesmas notícias do CSV (títulos conferidos com o Gustavo).

## D8. Teor com quatro opções: volta o `indeterminado`, sai o `nao_relacionado` (26/10/2026)

**Escolha:** o teor aceita positivo, negativo, neutro e `indeterminado`. O `nao_relacionado` da rodada 1 não existe mais.

**Por quê:** na rodada 1, o sistema entregava o par (parágrafo, entidade) pronto, e o `nao_relacionado` servia para o anotador recusar um par errado. Agora quem decide se há menção é o próprio anotador; se não há, ele não anota. O `indeterminado` continua necessário como saída para casos ambíguos, para ninguém ser forçado a chutar uma classe.

**Para o artigo:** pares `indeterminado` ficam fora das métricas de teor (F1 por classe, F1 macro, fim a fim), e o número deles é informado. As métricas continuam com três classes.

## D9. Protocolo v2 e regras propostas para o piloto (26/10/2026)

**Escolha:** `docs/protocolo-anotacao-v2.md`. A parte de teor reaproveita as regras da rodada 1. A parte de menções é nova, e as regras abaixo são propostas, marcadas `[piloto]` no protocolo, para confirmar depois do piloto com o Cristovam e o Nicolas:

- Menção direta = só o nome ou a sigla, sem o cargo ("Lula" em "o presidente Lula"). Motivo: limite fácil de reproduzir entre anotadores e igual ao que o matcher encontra.
- Menção indireta descritiva = artigo + substantivo (+ adjetivo colado), sem complementos ("o candidato" em "o candidato do PL à Presidência"). Motivo: limites curtos dão mais concordância no acerto exato; o complemento muitas vezes contém outra menção direta, que é marcada separadamente.
- Pronomes marcados: só "ele", "ela", "dele", "dela". Possessivos e clíticos ("seu", "criticou-o") ficam fora. Motivo: são difíceis de delimitar e de ligar, e aumentariam o tempo de anotação; registrar como limitação.
- Sujeito oculto não é marcado como menção, mas o candidato recebe teor no parágrafo. Motivo: não há trecho para marcar; sem a linha de teor, o gabarito perderia pares reais. Consequência: esses pares são erro para todos os sistemas, o que é honesto e deve ser informado.
- Pronomes de primeira pessoa dentro de citação não são marcados. Motivo: simplificação; o nome do falante normalmente está no mesmo parágrafo.
- "O petista" e similares se referem à pessoa, não ao partido; o partido só é marcado com "o partido", "a legenda", "a sigla" ou o nome. Motivo: evitar duas leituras para o mesmo trecho.
- Jair Bolsonaro não está no escopo (não é candidato); "Bolsonaro" sozinho só é marcado quando é o Flávio. Motivo: a lista de entidades (D4) tem só os candidatos de 2026.

## D10. Condições para partidos e base da revisão do protocolo (02/11/2026)

**Escolha:** usar as planilhas de Anderson, Beatriz e Nicolas como referência para revisar os exemplos. Para partidos da lista congelada, considerar o nome completo; exigir a palavra "partido" antes de nomes que também sejam palavras comuns, como "Missão"; exigir artigo antes de siglas, aceitando contrações como "do PT", "ao PL" e "pelo PSB"; ignorar siglas entre parênteses. Em "o PT, Lula (PT)", contar uma menção direta a PT.

**Motivo:** regras definidas por Beatriz após o piloto. Esta decisão revisa as condições de partido de D9. A ocorrência ignorada não gera, por si só, teor para o partido. A escolha das três planilhas não exclui os demais anotadores nem estabelece consenso automático; as regras escritas prevalecem sobre anotações que ainda sigam a versão anterior.

**Atualização posterior:** a decisão D15, de 12/11/2026, resolveu a questão e revogou explicitamente a permissão de D9 para tratar "o partido", "a legenda" e "a sigla" como menções a partido. Consulte D15 para a regra vigente.

**Para o artigo:** descrever as exclusões ao definir o escopo das menções e reavaliar o piloto com a nova regra antes de usá-lo como exemplo. As planilhas revisadas receberam intervenções; a concordância independente usa as respostas originais, anteriores à resolução de divergências.

## D11. Pronomes ligados à entidade anterior mais próxima (02/11/2026)

**Escolha:** para os pronomes admitidos pelo protocolo, usar a entidade anterior mais próxima na mesma notícia, incluindo partidos. Não restringir a busca a pessoas. Não ampliar automaticamente a lista de pronomes de D9. Sem entidade anterior identificada, registrar a dúvida, sem inventar uma atribuição.

**Motivo:** convenção definida por Beatriz para julgar os casos pronominais. Revisa a orientação anterior de escolher o referente pelo contexto. Em "Lula conversou com o PT. Ele apresentou a proposta", "Ele" fica ligado a PT por proximidade.

**Para o artigo:** quando essa regra define o gabarito, a avaliação da ligação pronominal mede aderência à convenção. Uma heurística de menção mais recente avaliada contra esse gabarito não demonstra, sozinha, resolução contextual de correferência. A detecção dos trechos e os resultados fim a fim continuam sujeitos a erros e devem ser reportados separadamente.

## D12. Normalização auxiliar para reconhecer entidades (02/11/2026)

**Escolha:** no reconhecimento experimental, remover acentos e substituir pontuação por separadores, sem colar palavras; aplicar o mesmo processo aos aliases. "Flávio", "Flávio," e "Flavio" devem reconhecer o mesmo nome. Identificar siglas entre parênteses no original antes da normalização, para preservar a exclusão de D10. Manter o texto original e uma correspondência de posições para devolver trechos e offsets originais.

**Motivo:** esclarecimento de Beatriz de que a limpeza serve ao reconhecimento de entidades. Não é uma instrução para remover pontuação e acentos do texto usado na classificação de teor. O matcher de produção já possui tratamento de acentos e limites de palavra; a implementação experimental deve reaproveitar o que atender ao requisito, sem presumir um defeito de reconhecimento causado por vírgulas.

**Compatibilidade:** D5 e o contrato de offsets de D6 continuam referenciando o texto original. O sistema A permanece a produção sem mudanças. Acrescentar filtros ou normalização à sua entrada criaria uma variante, que não pode ser apresentada como a mesma baseline.

**Estado:** requisito documentado para implementação e testes em `experiments/`. Esta revisão não altera o matcher, o validador, a produção ou as planilhas. As diferenças entre a produção e o novo escopo do gabarito precisam ser descritas na interpretação dos resultados.

## D13. Snapshot de entidades de `prisma-dev` e ambiente isolado para TF-IDF (10/11/2026)

**Escolha:** por autorização de Bea, gerar o snapshot de entidades em modo somente leitura usando `prisma-dev` como banco de origem. Para instalar e executar dependências de ML, usar o ambiente isolado `.venv-experiments`, com as versões fixadas em `experiments/requirements-ml.lock.txt`. O ambiente principal `.venv` e os requisitos de produção permanecem sem dependências de ML.

**Snapshot gerado:** `experiments/data/entidades.yaml`, em `2026-11-10T19:49:31Z`; 40 entidades (26 pessoas e 14 partidos), 73 aliases. O conteúdo das entidades e aliases coincide com o snapshot do piloto de 29/08. A exportação não alterou `data/exports/target_entities.yaml`. `experiments/data/preparacao/snapshot-audit.json` registra origem, contagens, integridade e hash do snapshot.

**Motivo:** usar a fonte indicada por Bea para conferir o escopo atual e manter o trabalho com scikit-learn separado do ambiente principal do projeto. O uso de `prisma-dev` foi autorizado; a conexão foi somente leitura.

**Estado da amostra:** a seleção original continua baseada no snapshot de agosto; `metadata.json` e os arquivos do sorteio foram preservados. Uma revalidação separada com o snapshot novo encontrou correspondência direta para 49 das 60 notícias e cobertura de 13 entidades. As outras 11 notícias requerem revisão humana de escopo e estão listadas em `candidate-revalidation.json`; ausência de correspondência direta não foi tratada como prova de que estão fora do escopo. A amostra permanece provisória.

## D14. Marcador de alvo e fallback sem span no TF-IDF (10/11/2026)

**Escolha de implementação:** para o classificador TF-IDF, substituir no texto original os spans anotados da entidade-alvo pelo marcador `[ALVO]`. Se o par não tiver span dessa entidade, manter o texto original sem marcador e contabilizar o caso em `unmarked_pairs` nos metadados.

O treino usa somente registros com `split=train`, remove pares com teor `indeterminado` e ajusta `TfidfVectorizer` com regressão logística balanceada (`random_state=42`, `max_iter=1000`). A opção `pairs=gold` prevê teor sobre chaves do gabarito; `pairs=mentions` prevê sobre entidades das menções fornecidas. A CLI exige arquivos de entrada distintos dos arquivos de saída e não sobrescreve saídas existentes.

**Limite:** quando vários alvos não têm spans no parágrafo, eles recebem a mesma representação textual. Esse fallback documenta o comportamento técnico do classificador; não altera as regras de anotação humana.

**Estado:** implementação disponível em `experiments/teor.py` e `experiments/tfidf.py`. A frente ainda requer sua verificação final; não há treino nem avaliação sobre o gabarito definitivo ou o teste congelado.

## D15. Referências genéricas de partido não são anotadas (12/11/2026)

**Decisão de Bea:** expressões genéricas como "o partido", "a legenda" e "a sigla" não identificam um partido e não devem ser anotadas como PT nem como qualquer outro partido. Elas não constituem menção (DIR ou IND) e não geram uma linha de teor para partido, ainda que uma entidade partidária tenha sido mencionada antes.

**Regra vigente para menções de partido:** considerar nome completo; quando o nome também for palavra comum, exigir "partido" antes; para siglas, exigir artigo anterior, aceitando contrações, e ignorar siglas entre parênteses. A referência genérica não atende a nenhum desses critérios. Esta decisão posterior revoga somente a parte correspondente de D9; as demais decisões históricas de D9 permanecem registradas conforme as revisões posteriores.

**Para o artigo:** aplicar a regra vigente na preparação das planilhas definitivas e na consolidação do gabarito. Não alterar retroativamente as respostas originais do piloto.

## D16. Manter a amostra atual e registrar melhorias futuras de qualidade (12/11/2026)

**Decisão de Bea:** manter a amostra atual como está para esta rodada. Não excluir nem substituir notícias e não corrigir os textos de origem, mesmo nos casos com foco fora da lista ou problemas de integridade. As limitações estão aceitas para a rodada atual.

**Registro de qualidade:** sete notícias (`445, 110, 325, 358, 354, 333, 390`) têm foco principal fora do escopo e permanecem na amostra. O ID `306` é ambíguo. Os casos `408, 435, 406, 418, 457` têm foco misto; o ID `373` trata de convenção do PT, que está no escopo. Os problemas de integridade são: bloco repetido em `178` junto de `445`; texto truncado e reiniciado em `139`; mojibake em `57` e `501`; bloco “Mais lidas” em `220`.

**Melhorias futuras:** corrigir encoding na origem; limpar boilerplate, duplicações e truncamentos com rastreabilidade; definir filtro de foco para a próxima coleta. Não editar os textos desta rodada depois da geração das planilhas, pois isso altera offsets. Recomendações detalhadas estão em [`experiments/data/preparacao/data-quality-improvements.md`](../experiments/data/preparacao/data-quality-improvements.md).

**Próxima etapa:** gerar as planilhas de anotação por anotador com os 15 IDs listados em cada `ids_<nome>.txt`, usando `experiments/data/entidades.yaml` e `data/raw/articles_202608191040.csv`. `scope_review` permanece pendente e a anotação ainda não começou; não há gabarito consensual ou split final.

## D17. Artigo da disciplina usa só o piloto, com referência por voto da maioria (19/11/2026)

**Decisão de Bea:** com a entrega do artigo em 26/11/2026, não há tempo para anotar a amostra de 60 notícias. O artigo vira um estudo exploratório sobre o piloto (5 notícias, 92 parágrafos). A anotação da amostra definitiva, o split 39/6/15 e a comparação com modelos treinados (TF-IDF e BERTimbau; sistemas B, C e D) passam para trabalhos futuros. O artigo é a entrega da disciplina e não será publicado agora.

**O que o artigo passa a medir:** concordância entre anotadores (já calculada sobre os originais de `180337Z`), parcela de menções indiretas e desempenho das regras sem treino (matcher de produção, heurística de menção mais recente e léxico) contra uma referência consolidada do piloto.

**Como a referência é montada:** voto da maioria sobre as planilhas atuais revisadas de `experiments/data/anotacao/piloto/` (D10 já aplicada), com cinco votantes: Beatriz, Cristovam, Gustavo, Lucas e Nicolas. Anderson fica fora porque sua planilha recebeu edição manual de Bea antes do primeiro backup, o que contaria o critério dela duas vezes, e porque cinco votantes reduzem empates. Uma resposta entra na referência quando pelo menos 3 dos 5 concordam; quando não há maioria, Bea desempata e a decisão fica registrada. Referências genéricas de partido (D15) não entram.

**Limitações a declarar no artigo:** a referência não é um gabarito adjudicado nem vem de respostas totalmente independentes (as planilhas atuais passaram por revisão); as regras D10 a D12 foram formuladas olhando o piloto, o que tende a favorecer a heurística avaliada nele; o protocolo mudou depois do piloto (D15); cinco notícias não permitem generalização.

**Execução da referência (19/11/2026):** `experiments/consolidate.py consolidar` gerou `experiments/results/piloto-referencia/` sem alterar as planilhas (SHA-256 conferido). Entraram 83 menções (79 com 5/5 votos, 1 com 4/5, 3 com 3/5), das quais 14 indiretas (≈ 17%), e 73 pares de teor. Foram descartadas 19 menções e 11 pares de teor sem maioria; a maior parte das menções descartadas são descrições ("seu filho", "o senador", "o governo petista") marcadas por um ou dois votantes, então a referência tende a reter só as menções indiretas mais evidentes. A unanimidade alta reflete a revisão das planilhas atuais; a concordância reportada no artigo continua sendo a dos originais de `180337Z`.

**Decisões de Bea na consolidação:**
- `T001`, 160-16 / Flávio (negativo 2, neutro 1, sem rótulo 2): **fora**. A menção "seu filho" não teve maioria, então a referência não registra Flávio nesse parágrafo e um teor sem menção ficaria incoerente.
- 175-4 / PL (entity_id 22, neutro 5/5): **removido** com `aplicar --remover-teor 175-4:22`. A única referência ao PL no parágrafo é "A sigla", que pela D15 não gera teor.
- Os outros três alertas de teor sem menção (145-7, 160-22, 175-6) ficam, por serem compatíveis com sujeito oculto.

**Referência final:** `experiments/results/piloto-referencia-final/referencia.jsonl` (92 parágrafos, 83 menções, 72 pares de teor: 59 neutros, 12 negativos, 1 positivo), com as decisões em `decisoes-desempate.json`. Com um único positivo, F1 por classe e F1 macro de teor ficam instáveis; isso precisa ser declarado ao reportar a etapa de teor.

**Avaliação das regras (19/11/2026):** `experiments/evaluate.py` gerou `experiments/results/piloto-avaliacao/` contra a referência final, com o snapshot `data/exports/target_entities.yaml` (o mesmo do piloto) e `include_party_descriptions=False` (D15). Escolhas de implementação: "IND perdida" significa nenhuma previsão com interseção e a mesma entidade; acurácia não é reportada porque `teor_scores` não a calcula; o custo foi medido num Apple M4, não na VPS. Achado que limita os dois sistemas de menção: os aliases do snapshot não incluem formas curtas como "Flávio" (22 menções na referência), "Gaspar", "Caiado" e "Kassab", então nenhum dos dois passa de 41/69 de revocação em DIR. Os aliases não foram alterados, para não ajustar o sistema ao conjunto avaliado; a inclusão fica como recomendação para a produção.

**Nota de reprodutibilidade (19/11/2026):** o hash de `consolidate.py` registrado no `consolidar` difere do registrado no `aplicar` e no `evaluate.py` porque a opção `--remover-teor` foi acrescentada depois da consolidação. Rodar `consolidar` de novo com o código atual, numa pasta de rascunho, produziu `referencia-provisoria.jsonl` com o mesmo SHA-256 (`8e956897…`) do arquivo versionado, então a mudança não afetou a referência.
