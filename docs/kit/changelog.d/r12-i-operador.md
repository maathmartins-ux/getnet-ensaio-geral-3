# Frente R12-I: aprovação de risco alto só com chave pessoal

- **O quê:** `POST /actions/{id}/approve` recusa (403, auditado) o token compartilhado de operador, que só existe fora
  de produção: ele lê a fila, responde e rejeita, mas a escrita de risco alto (quatro olhos) só executa com chave
  pessoal (`OPERATOR_KEYS`), com o nome de quem aprovou na auditoria.
- **Por quê:** uma régua da rodada 11 citou que, no dev, o `OPERATOR_TOKEN` compartilhado vale como "admin"
  (src/app/auth.py:244-249) — com ele se aprovava estorno sem dono.
- **Prova:** `tests/test_hitl.py::test_high_risk_action_needs_owner_then_operator_and_runs_once` e
  `tests/test_risk_policy.py::test_limit_itself_is_owner_only_and_above_goes_to_four_eyes` (o compartilhado leva 403
  e a ação segue aguardando; a chave pessoal aprova e executa uma vez).
