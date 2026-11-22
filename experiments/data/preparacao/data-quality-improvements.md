# Qualidade dos dados: melhorias para próximas rodadas

## Decisão para a rodada atual

Bea decidiu manter a amostra atual como está. As limitações abaixo são aceitas para esta rodada: não corrigir textos, não excluir candidatas e não substituir notícias. A proposta permanece com `scope_review` pendente e ainda não é gabarito nem split final.

## Problemas registrados

- **Foco fora do escopo:** as notícias `445, 110, 325, 358, 354, 333, 390` têm foco principal em entidades que não estão na lista do experimento. Bea decidiu mantê-las nesta rodada.
- **Foco ambíguo:** o ID `306` tem foco incerto. Nos casos originais `408, 435, 406, 418, 457`, há mistura entre cobertura de entidades do experimento e assuntos estaduais. O ID `373` é sobre uma convenção do PT; PT está no escopo e esse caso é considerado dentro do escopo.
- **Duplicação:** o ID `178` contém bloco repetido junto do conteúdo associado ao ID `445`.
- **Texto interrompido:** o ID `139` tem trecho truncado e reiniciado.
- **Codificação:** os IDs `57` e `501` apresentam mojibake.
- **Boilerplate:** o ID `220` contém um bloco de “Mais lidas”.

## Melhorias para próximas coletas

1. Corrigir a codificação na origem da raspagem, preservando o texto original e registrando a transformação aplicada.
2. Detectar e remover boilerplate, blocos repetidos e textos interrompidos antes de montar a amostra. Guardar texto bruto, texto tratado, regra aplicada e referência aos offsets para manter rastreabilidade.
3. Definir antes da próxima coleta um filtro de foco que diga quando uma notícia sobre entidade fora da lista pode ser mantida por cobertura substantiva de uma entidade elegível.

Não alterar os textos desta rodada depois de gerar as planilhas: qualquer edição muda offsets e pode invalidar os trechos anotados. As correções acima são recomendações futuras, não tarefas de limpeza para a amostra atual.
