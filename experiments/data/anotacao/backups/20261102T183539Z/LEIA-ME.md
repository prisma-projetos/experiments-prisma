# Aplicação de D10 a D12 ao piloto

Esta pasta guarda as seis planilhas imediatamente anteriores à aplicação de D10 a D12, em 02/11/2026. Os arquivos atualizados estão em `../../piloto/`.

Estas cópias já continham revisões. Para concordância independente, usar as respostas anteriores às intervenções: as cinco cópias em `../20261102T180337Z/` e uma versão independente de Anderson, que não foi preservada naquela rodada. Não calcular concordância independente sobre as planilhas revisadas ou sobre este novo backup.

Em cada planilha foram retiradas 17 menções diretas de siglas: 16 entre parênteses e PT em 160-15, precedido por "por", sem artigo. Foram retirados 14 pares de teor sustentados apenas por essas ocorrências. As menções aceitas restantes conservam sua numeração no texto original; em 160-5, por exemplo, a ocorrência 3 de PL permanece.

Nos seis arquivos, "ele" em "segundo ele", parágrafo 145-6, foi ligado a Lula. Após excluir `(PT)`, Lula é a entidade anterior mais próxima. O trecho continua sendo apenas "ele". O teor existente de Lula foi preservado como alvo da crítica. O de Flávio também foi mantido, pois o parágrafo continua tratando da fala dele, com sujeito contextual em "avaliou" e "fez críticas". Não houve transferência automática de rótulo nem criação de pares de teor.

Na planilha de Anderson, a menção direta "do PT" de 160-29 foi delimitada como "PT". A contração permanece no texto original e habilita a ocorrência. Sua aba `tempo` foi padronizada para o layout do validador, sem alterar os minutos informados.

`alteracoes.json` contém valores anteriores e finais por célula, motivos, linhas retiradas com observações e antecedentes usados na ligação pronominal. Observações humanas que descrevem a atribuição antiga foram mantidas na planilha; a atribuição revisada está registrada separadamente. `validacao.json` contém contagens e hashes.

As descrições de partidos, como "a legenda", "o partido" e "a sigla", foram preservadas porque sua inclusão continua pendente. Outras dúvidas anteriores de escopo ou teor também permanecem para adjudicação. A ligação pronominal por proximidade é uma convenção experimental, não uma demonstração de correferência contextual.

Os 92 parágrafos e seus textos, acentos e pontuação foram preservados byte a byte no componente correspondente de cada XLSX. A normalização auxiliar não foi aplicada à entrada do teor nem reescreveu trechos. Listas, estilos e demais componentes não afetados também foram preservados. Não houve mudança no código ou na produção.

| Anotador | Menções antes/depois | Teores antes/depois |
|---|---:|---:|
| Anderson | 106 / 89 | 88 / 74 |
| Lucas | 102 / 85 | 85 / 71 |
| Beatriz | 109 / 92 | 88 / 74 |
| Cristovam | 100 / 83 | 89 / 75 |
| Gustavo | 102 / 85 | 95 / 81 |
| Nicolas | 118 / 101 | 91 / 77 |

As seis planilhas passaram na validação de menções e teor sem erros. Continuam faltando três tempos de Beatriz e cinco de cada um de Cristovam e Nicolas; não foram estimados.
