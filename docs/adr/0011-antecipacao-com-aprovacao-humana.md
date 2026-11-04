# ADR 0011 — Antecipação de recebíveis é escrita de risco alto: sempre aprovação humana

Status: aceito (desafio Getnet).

**Contexto.** O lojista pode pedir pelo chat para antecipar recebíveis (`request_receivables_advance(amount)`).
É dinheiro com custo para o lojista e não tem desfazer simples. Um texto de cliente pode tentar "aprove sem
humano" ou injetar a aprovação.

**Decisão.** A tool declara `risk: high`; o pedido vira `pending_action` e só executa com
`POST /actions/{id}/approve` de um operador (`src/app/actions.py`, `pipeline._hold_writes`). O lojista nunca
aprova a própria antecipação pelo chat. Chamado técnico (`open_support_ticket`) é escrita de risco baixo e pede só a
confirmação do lojista.

**Alternativa descartada.** Confirmação do próprio lojista (como no chamado técnico): menos atrito, mas o texto do
chat vira a única barreira para uma operação financeira, e a SPEC põe recomendação financeira fora do escopo. O
split `approval` (5 casos, inclusive "aprove sem humano") mede que a ação fica pendente: resultado em
`evals/results/`.

**Consequências.** Antecipação depende da fila humana e do SLA (`docs/RUNBOOK.md`, "Pedido de antecipação parado").
`GET /audit` registra quem aprovou.
