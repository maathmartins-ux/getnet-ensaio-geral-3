# ADR 0005 — O supervisor LLM decide todo turno; o atalho de 1 passo fica como opção de custo

Status: aceito.

**Contexto.** O supervisor LLM coordena os especialistas como tools (`src/app/supervisor.py`). Num plano de UM
especialista com o router confiante, existia um atalho (`fast_path`): o passo rodava direto e a resposta era a do
especialista, sem o supervisor. Ele economizava 2 chamadas sequenciais (escolher a tool e redigir a resposta final),
alguns segundos por turno. Mas, nos cenários mais comuns, a decisão de rota deixava de ser observável: quem lia o trace
via a tabela escolher o caminho, não o modelo que lê o resultado e decide.

**Decisão.** O supervisor LLM decide em todo turno (`SUPERVISOR_FAST` desligado por padrão). Ele lê o status de cada
especialista (`ok`, `partial`, `insufficient`, `error`) e escolhe: responder, chamar outro especialista ou o humano,
dentro de `ALLOWED`, `MAX_STEPS` e do orçamento do turno. A escalada quando nada resolve é garantida em código
(`_enforce_escalation`). Sem chave ou com falha do provedor, a mesma tabela de transições (`FALLBACK`, `ALLOWED`)
roda offline. `SUPERVISOR_FAST=on` religa o atalho para quem prefere custo e latência menores.

**Alternativas.** (1) Atalho de 1 passo ligado por padrão: 1 chamada de modelo a menos na maioria dos turnos, mas a
decisão fica na tabela nos casos mais frequentes. (2) Só a tabela: perde o replanejamento que lê o resultado.

**Consequências.** Mais 2 chamadas e alguns segundos por turno de um passo. A resposta final passa pela redação do
supervisor, conferida pelo verificador de claims e de números como qualquer outra; no atalho (quando ligado), a oferta
do humano numa resposta parcial é texto fixo (`_offer_human_on_gap`), não depende da redação.

**Números.** Não ficam escritos aqui, porque mudam a cada bateria: saem dos blocos gerados de `evals/results/`
commitado. Oficiais resolvidas, juiz (fundamentadas e úteis) e custo por turno resolvido estão no §0 do `README.md`;
latência por split e quem decide cada passo (supervisor LLM × plano do router × código), no bloco `trace` do
`docs/RESULTS.md`. Prova por teste:
`tests/test_supervisor_fast.py::test_single_step_confident_plan_skips_the_supervisor_llm` (atalho, quando ligado) e
`tests/test_v54_rehearsal_guards.py::test_supervisor_llm_decides_every_turn_by_default`.

**Adendo (kit v5.5.2): achado como informação.** No motor LLM o `needs` não vira passo imposto: chega ao
modelo no tool_result e o modelo decide; uma volta de lembrete se ele encerrar sem atender, e o achado ignorado de
novo fica contado (`outcome: ignored`, `need_ignored`). Só o motor de tabela (offline, queda do LLM, atalho)
insere, e ele segue a regra do supervisor quando outro especialista já respondeu (responde com ele e oferece o
humano, em vez de escalar o turno). Motivo: na bateria ao vivo do kit v5.5.1, 19% dos passos eram inseridos pelo
código, sem ganho na ablação. Prova:
`tests/test_supervisor_needs_budget.py::test_llm_engine_reminds_once_when_the_model_ignores_the_finding` e
`tests/test_supervisor_needs_budget.py::test_table_does_not_escalate_a_partial_turn_when_another_specialist_answered`.

**Adendo (kit v5.5.3): todo achado ao modelo; a resposta do atendente dentro do laço.** No motor LLM o tool_result
leva todo achado das tools; a regra do domínio (`needs_for`) só escolhe o que o código cobra (o lembrete) e o que a
tabela insere, e o achado fora da regra que o modelo deixa de lado sai `seen`. A resposta do atendente dentro da espera
volta ao supervisor LLM como resultado do passo `human`, numa réplica do laço: os passos depois dela são do modelo (os
que ficaram pendentes no plano e, se a resposta trouxer um dado, outro especialista: `human-><agente>`), e a redação
final também, conferida pelo código (cita o protocolo, não oferece nem nega o atendente), com o template de reserva
(sem LLM, queda na réplica ou orçamento do turno esgotado). Na réplica o humano não é chamado de novo. Prova:
`tests/test_supervisor_needs_budget.py::test_llm_engine_gets_the_finding_the_rule_left_out_and_decides`,
`tests/test_supervisor_needs_budget.py::test_llm_engine_reminds_only_of_the_finding_the_rule_ties_to_the_question`,
`tests/test_v54_hitl_sync.py::test_with_the_llm_the_operator_answer_returns_to_the_loop_and_feeds_a_step`,
`tests/test_v54_hitl_sync.py::test_with_the_llm_the_model_may_only_write_and_cannot_call_the_human_again` e
`tests/test_v54_hitl_sync.py::test_the_code_checks_the_written_answer_and_the_template_is_the_fallback`.
