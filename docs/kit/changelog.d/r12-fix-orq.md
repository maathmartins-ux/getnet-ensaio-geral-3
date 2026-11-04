# Frente R12-fix-orq: a réplica depois do atendente herda o estado do turno; orçamento sem escalada diz "->stop"

Base: os 2 achados confirmados da revisão adversarial da área orquestração do r12/int
(`r12/fix/orquestracao.md`, itens 1 e 2), cada um com reprodução do revisor e do cético. Nada rodou ao vivo; os
testes usam o cliente LLM falso e a operadora simulada.

## 1. A réplica do laço depois do atendente herda a rota e os achados pendentes do turno
- **O quê:** `supervisor.Outcome` ganhou `ran_before` (a rota do turno até o passo "human") e `pending_needs` (os
  achados que o laço do supervisor LLM deixou sem o agente pedido; é o mesmo dict `pending` do laço). `_after_human`
  passa o turno à réplica (`run_llm(..., before=out)`): `_note_needs` marca "ran" o achado de um agente que rodou
  antes do atendente e `_open_needs` não o cobra; o `pending` da réplica começa com os achados de antes, então o
  modelo que chama o agente pedido marca o passo de antes do atendente "called" (ou "reminded") e o desvio sai
  "<de>:need-><agente>". O achado que o laço já decidiu ("seen"/"ignored") sai do `pending` e não é herdado; o que já
  levou lembrete não leva outro (o lembrete continua um por laço, nunca dois para o mesmo achado). MAX_STEPS segue
  contado na rota da réplica. Se o LLM cai na réplica, as marcas que ela deu aos passos de antes do atendente voltam
  ao que eram (o passo dela não fica no turno).
- **Por quê:** a réplica começava com `Outcome` e `pending` novos. (a) Plano ['faq'], "Quando chega meu pedido?": o
  faq rodou antes do atendente e, na réplica, o records(1002) trouxe o achado pedindo o faq; a 6ª chamada levava
  "records_agent pediu faq_agent ... que não foi chamado" (a 1ª mensagem da réplica mostrava o faq rodado) e o passo
  saía "ignored", somando em `needs_ignored_total`. (b) Plano ['records']: o achado de antes do atendente que o modelo
  atendeu na réplica ficava "blocked" (como se a regra do turno o tivesse barrado) e o desvio saía
  "human->faq (plano: [])".
- **Prova:** `tests/test_v54_hitl_sync.py::test_the_replica_knows_the_step_that_ran_before_the_human` ("ran", 5
  chamadas, sem lembrete nem ignorado), `::test_the_replica_inherits_the_finding_left_open_before_the_human`
  ("called" e "records:need->faq"; com o faq no plano, "called" e "human->faq (no mesmo turno)"; LLM caído na
  réplica, "blocked" de volta) e `::test_the_replica_reminds_of_the_finding_left_open_before_the_human` (achado
  herdado da regra ganha a volta de lembrete na réplica e sai "reminded"; já lembrado antes do atendente, sai
  "ignored" sem 2º lembrete). Os três falham no código anterior.

## 2. Orçamento esgotado sem escalada: o replano diz "budget:<teto>->stop"
- **O quê:** `supervisor._exhaust` decide antes de escrever: escala só se o turno ainda não escalou e a intenção
  permite (`no_escalation`); senão o replano sai "budget:<teto>->stop". `_continue_with_operator` leva o teto que
  parou a réplica a `out.budget`.
- **Por quê:** com MAX_MODEL_CALLS=2 o turno gastava as duas chamadas antes do atendente e a réplica parava no
  orçamento; os replanos diziam "budget:model_calls->escalation" sem escalada nenhuma (a réplica tem resume_of), a
  transcrição de vitrine (`scripts/demo_md.py`) imprimia a escalada que não houve e `out.budget` ficava None. O mesmo
  rótulo falso saía em intenção de NO_ESCALATION.
- **Prova:** `tests/test_v54_hitl_sync.py::test_budget_spent_before_the_replica_reports_no_escalation` (replanos
  exatos, `out.budget == "model_calls"`, uma escalada só; falha no código anterior) e a asserção nova em
  `tests/test_supervisor_needs_budget.py::test_budget_without_escalation_for_no_escalation_intents`. Os casos que
  escalam seguem com "budget:<teto>->escalation" (`test_model_call_budget_delivers_the_answered_part_and_hands_off_the_rest`,
  `test_hitl_resume_plan.py::test_operator_reply_runs_the_pending_knowledge_step`).
