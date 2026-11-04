# Frente R12-B: o achado chega sempre ao supervisor LLM e a resposta do atendente volta ao laço do LLM

Base: as 3 réguas da rodada 11 (`r12/reguas_r11.md`), Orchestration. Nada rodou ao vivo nesta frente; as medidas
citadas vêm dos `live_*.json` da rodada 11 do ensaio (só leitura) e os testes usam o cliente LLM falso.

## 1. Motor LLM: todo achado das tools chega ao modelo; a regra do domínio decide só o que o código faz
- **O quê:** `supervisor.collect_needs(result, ctx, engine)`. No motor de tabela (`engine="table"`, offline, queda do
  LLM, atalho de 1 passo) nada muda: com `needs_for` no domínio só entra o achado que a regra devolve, e o código
  insere o passo. No motor LLM (`engine="llm"`, os passos que `run_llm` roda, inclusive o antecipado) o passo leva
  tudo: o achado do próprio agente, o da regra e o `needs` cru das tools, juntos por agente pedido; é o que vai no
  tool_result. A regra continua decidindo o que o código faz no motor LLM: `_invoke` marca em `needs_ruled` os agentes
  que ela liga à pergunta, e só esses ganham a volta de lembrete. Achado fora da regra que o modelo leu e deixou de
  lado sai com `outcome: seen` (novo em `supervisor.NEED_OUTCOMES`; rótulo em `scripts/fill_readme.py`), sem
  lembrete. O contrato do domínio ganhou a nota em `domain/example.py` (achado que importa ao modelo mesmo fora da
  regra vai no `needs` da tool).
- **Por quê:** régua 2 (TOP8 #3) e régua 3 (TOP8 #3): "o achado `needs` só chega ao modelo se a regex `_SYMPTOM`
  casar"; régua 1 (TOP8 #4): "`needs` filtrado por regex de sintoma". Medido nos `live_*.json` da rodada 11 do
  ensaio (achado cru reconstruído pelos argumentos das tools e pelo CRM): de 91 passos do records em que as tools
  acharam algo, a regex barrou 43, inclusive sintoma real escrito de outro jeito (recusa em inglês, gíria, tela
  travada, mensagem de erro citada).
- **Por que o lembrete fica com a regra (e não com todo achado):** dos 43 achados barrados, a maior parte não muda a
  resposta (extrato pedido, terminais listados, seguimento de memória sobre o mesmo terminal). Com lembrete para
  todos, cada um custava uma volta a mais do supervisor ("Chame agora o especialista pedido"), empurrando o faq para
  perguntas que não o pedem, no p50 que a régua já cita (régua 1, TOP8 #3). Assim o modelo lê tudo e decide; o código
  só insiste onde a regra liga o achado à pergunta.
- **Prova:** `tests/test_supervisor_needs_budget.py::test_llm_engine_gets_the_finding_the_rule_left_out_and_decides`
  (mesmo achado sem palavra da regra: tabela sem achado; motor LLM com o achado no tool_result, sem lembrete, `seen`;
  e, se o modelo chama o faq, `called` e `records:need->faq`) e
  `::test_llm_engine_reminds_only_of_the_finding_the_rule_ties_to_the_question` (com a pergunta que a regra pede, o
  da regra e o cru juntos e a volta de lembrete). Os dois falham no código anterior (o modelo recebia `needs: []` ou só
  o da regra). O filtro da tabela segue em `::test_domain_filter_decides_no_symptom_no_faq`.

## 2. A resposta do atendente volta ao supervisor LLM numa réplica do laço
- **O quê:** `supervisor._continue_with_operator`. Resposta do atendente dentro da espera → passo `human`
  (`decided_by: operator`) e, com o supervisor LLM ligado e de pé no turno, UMA réplica do laço (`_after_human` →
  `run_llm(..., after_human=...)`): a 1ª mensagem traz o cabeçalho do turno, cada passo até o atendente com o
  resultado que o modelo lê dele e a resposta do atendente como resultado do passo `human` (evidência; a identidade do
  operador fica fora). O modelo roda os passos do plano que ficaram para depois do atendente, pode chamar outro
  especialista com o que ele disse (passo `decided_by: llm`, desvio `human-><agente> (plano: [...])`; o plano que
  continuou sai `human-><passos> (no mesmo turno)`) e redige a resposta final do turno. Tetos de sempre: MAX_STEPS da
  réplica, orçamento do turno (MAX_MODEL_CALLS, MAX_TURN_USD), ALLOWED a partir do início (`_allowed`: depois do
  passo human vale `ALLOWED[None]`); o humano não é chamado de novo (no_escalation por `resume_of`: a tool call de
  escalation volta `transição não permitida: human->escalation_agent`). Sem LLM, com o LLM caído antes no turno (motor
  `table`) ou queda na réplica: os passos pendentes no motor de tabela e a composição por template de antes
  (`_template_after_human`); orçamento esgotado na réplica: o que já rodou e o template. A retomada assíncrona
  (`resume.py`, resposta fora do prazo) não mudou.
- **Por quê:** régua 3 (TOP8 #3): "a resposta do operador volta fora do laço de tool use e é colada literalmente em
  template"; régua 1 (TOP8 #7): "nenhuma execução ao vivo mostra o plano seguindo com mais passos de agente depois da
  resposta humana: não há replan `human->…`"; régua 3 (TOP8 #8): o split hitl "não exercita 'o plano continua'".
  Antes, com o LLM ligado, a resposta do atendente ia colada no template e só passava pelo modelo quando havia passo
  pendente; um id que só ela trazia não chegava a passo nenhum.
- **Prova:** `tests/test_v54_hitl_sync.py::test_with_the_llm_the_operator_answer_returns_to_the_loop_and_feeds_a_step`
  (o atendente diz o pedido; o modelo chama o records com esse id; `human->records (plano: [])`; resposta final do
  modelo com o dado do records e o protocolo), `::test_with_the_llm_the_step_left_for_after_the_human_runs_in_the_loop`
  (faq pendente rodado pelo modelo na réplica), `::test_with_the_llm_the_model_may_only_write_and_cannot_call_the_human_again`
  e `::test_the_code_checks_the_written_answer_and_the_template_is_the_fallback`. Três deles falham no código anterior.
  Sem LLM o comportamento medido do split hitl é o mesmo: `tests/test_r11_hitl_eval.py` e os testes de espera de
  `tests/test_v54_hitl_sync.py` passam sem mudança.

## 3. Depois do atendente o código confere a redação do modelo, não corta frase dela
- **O quê:** `supervisor._written_after_human`: a redação da réplica vale inteira se não oferece nem nega o
  encaminhamento (`talks_handoff`, as mesmas frases de `without_handoff_talk`); sem o protocolo, a frase `CONSULTED`
  vem antes dela; com oferta ou negação, ou sem redação, vale o template. `without_handoff_talk` só corta texto na
  composição por template (texto dos especialistas, sem LLM). /metrics: `hitl_answer_total{by, why}`.
- **Por quê:** régua 2 (TOP8 #3) e régua 3 (TOP8 #3): regex pós-LLM reescrevendo a resposta final.
- **Prova:** `tests/test_v54_hitl_sync.py::test_the_code_checks_the_written_answer_and_the_template_is_the_fallback`
  (protocolo que faltou, oferta do atendente, LLM caído na réplica e orçamento esgotado).
