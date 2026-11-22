# ADR 0002 — System DB compartilhado; notificação ao Analyser via outbox

**Status**: Aceito (17/08/2026), validado por análise de arquitetura

## Contexto

O `context.md` raiz (seção 7.5/7.7/7.8) já previa um `System DB` único, compartilhado entre `Classifier` (grava resultado individual), `Analyser` (grava análise agregada) e `API` (só lê). Isso pareceu, à primeira vista, contradizer a regra da seção 19.2 do mesmo documento ("nenhum componente deve acessar diretamente o banco... de outro") — a mesma regra que motivou a decisão da ADR 0001 (Scraper/Classifier via RabbitMQ, nunca banco direto).

Diferença resolvida por análise de arquitetura: o caso do Scraper era acoplamento entre bancos de serviços com motivos de mudança diferentes (fronteira externa, dados brutos). O System DB é, por desenho, um repositório interno pensado desde o início para ser compartilhado entre estágios do mesmo pipeline — a própria API já foi desenhada pra ler direto dele. Dividir o banco do Classifier sozinho não resolveria esse acoplamento, porque API e Analyser já dependem de um repositório compartilhado.

Essa distinção foi registrada como exceção explícita na seção 19.2 do `context.md` raiz.

## Decisão

- System DB compartilhado, como já previa a arquitetura original — mantido, não alterado.
- Este repositório (Classifier) cria e é dono das migrations do System DB por enquanto, por ser o primeiro a precisar. Quem herda essa responsabilidade quando o Analyser existir fica em aberto — não inventar solução para um serviço que ainda não existe.
- Tabelas de resultado tratadas como superfície estável e intencional (nomes claros, migrations comentadas) — não misturar com estado interno/transitório do Classifier.
- Ack da mensagem RabbitMQ só depois de persistir o resultado E gravar a notificação pendente para o Analyser, na mesma transação — evita perder a notificação se o ack acontecer antes de tudo commitado.
- Notificação Classifier→Analyser via RabbitMQ, mesmo padrão outbox do `scrapping-prisma` (ver ADR 0001): grava "precisa notificar" na mesma transação do resultado; publisher separado drena com retry (`attempts`/`max_attempts`); nunca publica inline logo após salvar. Nome da fila/exchange ainda não confirmado com o DevOps — placeholder configurável via env.
- Não implementar circuit breaker mais sofisticado, backoff exponencial ou retry além do padrão já existente — reaproveitar, não melhorar especulativamente.

## Consequências

- Pendente: confirmar com o DevOps o nome da fila/exchange da notificação ao Analyser antes de produção.
- Pendente: decidir dono das migrations do System DB quando o Analyser for implementado.
