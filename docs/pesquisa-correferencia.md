# Pesquisa — correferência de entidade (sem decisão ainda)

Investigação feita em 17/08/2026. Registro de pesquisa, não uma decisão — quando escolhido um caminho, vira ADR em `docs/adr/`.

## O problema

O `entity_matcher.py` só identifica entidade por nome/apelido (exato ou fuzzy) contra `config/entities.yaml`. Isso não cobre um padrão comum em notícia: o primeiro parágrafo cita o nome completo ("Lula"), os parágrafos seguintes se referem à mesma pessoa por termo genérico ("o presidente", "o candidato"), sem repetir o nome.

Não é um detalhe raro — é estrutural em texto jornalístico. Sem tratar isso, o dataset perde a maior parte do conteúdo real sobre cada entidade (o primeiro parágrafo costuma ser só apresentação; o desenvolvimento do assunto vem depois, sem repetir o nome).

**Tentativa descartada**: campo `cargo` por entidade (ex.: Lula → "presidente"), atribuindo menções genéricas por cargo à última entidade nomeada com aquele cargo. Não funciona para este projeto: como o objetivo é falar sobre **candidatos a eleição**, todos os políticos rastreados são chamados de "candidato" em algum momento — o termo de cargo não diferencia ninguém.

## Ferramentas de correferência em português — o que existe

Não existe hoje uma ferramenta de resolução de correferência em português madura, mantida e fácil de integrar.

- **CORP** (PUCRS, [página oficial](https://www.inf.pucrs.br/linatural/wordpress/recursos-e-ferramentas/corp-coreference-resolution-for-portuguese/)) — única ferramenta encontrada feita especificamente para correferência em português. Baseada em regras linguísticas (não é ML). Distribuída como `.jar` Java rodado por linha de comando — exigiria dependência de Java num projeto hoje 100% Python. Sem repositório no GitHub encontrado, sem confirmação de manutenção recente ou de qualidade em texto de notícia atual — não testado na prática.
- **Corpora acadêmicos** (Corref-PT, Summ-it++) — dados anotados pra treinar/avaliar sistema próprio de correferência. Usar isso abriria um subprojeto de ML à parte, do tamanho (ou maior) do classificador de sentimento em si.
- **Ferramentas multilíngues** (`crosslingual-coreference`, modelos com mBERT/XLM-RoBERTa) — não validadas especificamente para português, qualidade real desconhecida.
- **Ferramentas maduras** (neuralcoref, fastcoref, AllenNLP coref) — estado da arte, mas só em inglês.

## Alternativa proposta (não implementada)

Heurística clássica de correferência — "menção mais recente": dentro da mesma notícia, uma referência genérica ("presidente", "candidato", "ele") é atribuída à última entidade citada pelo nome antes daquele ponto do texto, resetando quando um nome novo aparece. Não depende de lista de cargos, resolve o caso do "candidato".

**Limitação conhecida, sem solução barata**: quando a notícia alterna entre duas entidades nomeadas sem repetir nome ("Lula defendeu X. Já Bolsonaro criticou Y. O candidato afirmou que..."), fica ambíguo a quem "o candidato" se refere — mesmo ferramenta profissional de correferência erra nesse padrão.

## Três caminhos possíveis

1. Heurística "menção mais recente" — barata, sem dependência nova, imperfeita.
2. Testar o CORP na prática antes de decidir — baixar, rodar numa amostra, avaliar qualidade e custo de manter dependência Java.
3. Aceitar a limitação por enquanto: só rotular/treinar com menção nominal explícita — dataset mais limpo, perde volume real.

## Impacto se não resolvido

Bloqueia a extração do CSV para rotulagem (`docs/protocolo-anotacao.md`) — gerar a lista de parágrafos para os amigos rotularem antes de decidir isso faz o dataset nascer incompleto/enviesado.
