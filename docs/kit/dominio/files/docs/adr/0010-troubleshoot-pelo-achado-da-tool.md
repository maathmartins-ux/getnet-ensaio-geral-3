# ADR 0010 — Troubleshoot começa no dado do lojista; o manual entra pelo achado `needs` da tool

Status: aceito (desafio Getnet).

**Contexto.** "Minha maquininha não conecta" (official-05) e "a transação foi recusada" (official-08) pedem duas
coisas: o estado real do terminal ou da transação no CRM e o passo do manual no site. Qual terminal está offline
(`T1988B`, chip, sem sinal) só a tool sabe; o que fazer só a base sabe.

**Decisão.** A intent `troubleshoot` tem plano `["records"]`. Quando a tool encontra o problema, ela emite `needs`
(ex.: `get_terminals` com terminal offline pede o manual de conexão) e o supervisor agenda o Knowledge com a
pista do achado (`supervisor.collect_needs`, `accept_need`, `_hint_to`). O plano se adapta ao resultado em vez de
ser fixo.

**Alternativa descartada.** Plano fixo `["records", "faq"]` para todo troubleshoot: chama o Knowledge mesmo quando
o terminal está online e o problema é outro, e a busca vai sem a pista do achado (pergunta genérica "não conecta"
em vez de "terminal com chip sem sinal"). O que decide entre as duas é o split `replan` (10 casos de troubleshoot
com `needs`) e o `dependent`: resultado em `evals/results/` (bloco `replan` do README).

**Consequências.** O Knowledge só roda quando o dado pede; o trace mostra o motivo (`needs` no span do `records`).
Se a tool não emitir `needs`, a resposta fica só com o dado: o teste `tests/test_domain_supervisor.py` cobre o caso.
