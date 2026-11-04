# Frente R11-A: o achado (`needs`) vira informação para o supervisor LLM, não passo imposto

Base: `r10_problemas.md` §3 (as 3 réguas cortaram Orchestration: parte dos passos ao vivo era inserida pelo código,
o faq inserido já estava no plano do router, o filtro de sintoma do domínio não valia e a ablação não mostrou ganho).
Nada rodou ao vivo; as medidas citadas estão nos comentários do código e nos testes, com a origem.

## 1. Motor LLM: o achado é informação, com uma volta de lembrete
- **O quê:** `supervisor.run_llm` não insere mais o passo pedido por um achado (nem depois do passo antecipado nem no
  laço). O `needs` chega ao modelo no tool_result e fica pendente (`_note_needs`) até o modelo chamar o agente
  pedido. Se o modelo encerrar com achado pendente, UMA volta de lembrete (`_need_reminder`, o padrão do `nudged` do
  records) diz qual achado ficou sem resposta; ignorado de novo, o passo que trouxe o achado sai com
  `outcome: ignored` na árvore de passos, o log ganha `need_ignored` e /metrics `needs_ignored_total`, e o turno
  segue. O passo que o modelo chama depois do achado é dele (`decided_by: llm`). O motor de tabela (offline, queda do
  LLM, atalho de 1 passo) continua inserindo, como antes (`decided_by: code`, `why: needs`). O prompt e as tools do
  supervisor não mudaram.
- **Por quê:** §3, régua 1/2/3 ("replanejamento imposto pelo código"; nos oficiais todo desvio do plano vinha do
  código e o supervisor LLM só confirmava).
- **Prova:** `tests/test_supervisor_needs_budget.py::test_llm_engine_the_model_decides_on_the_finding`,
  `::test_llm_engine_reminds_once_when_the_model_ignores_the_finding`,
  `::test_llm_engine_ignored_finding_is_counted_and_the_turn_goes_on`,
  `::test_finding_of_the_step_run_before_the_model_is_also_the_model_to_decide`,
  `::test_table_engine_keeps_inserting_when_the_llm_is_down`.

## 2. Passo que já estava no plano do router não é replanejamento
- **O quê:** nos dois motores, o agente pedido pelo achado que já estava no plano do router roda sem entrar em
  `replans`; fora do plano, o desvio entra como `<de>:need-><para>` (decidido pelo modelo ou pela tabela). Na tabela,
  o passo planejado passa a receber a dica do achado como sub-pergunta (sem trocar a que já tinha): sem ela, o faq
  planejado depois do records ficava sem fonte e o turno escalava.
- **Por quê:** §3, evidência 2 (o faq do troubleshoot, já planejado, contava como "replanejou").
- **Prova:** `tests/test_supervisor_needs_budget.py::test_step_already_in_the_router_plan_is_not_a_replan`.

## 3. `collect_needs`: o filtro do domínio vale e achados do mesmo agente se juntam
- **O quê:** com `needs_for` no domínio, o `needs` cru das tools só entra pelo que o filtro devolver (sem
  `needs_for`, o cru continua valendo). Dois achados para o mesmo agente juntam `why` e `hint` (parte igual uma vez
  só), em vez de descartar o 2º.
- **Por quê:** §3, evidências 3 (o filtro de sintoma era código morto: achado em mensagem sem sintoma) e 4 (no
  official-08 a dica de recusa caiu e o faq trouxe o manual do chip).
- **Prova:** `tests/test_supervisor_needs_budget.py::test_domain_filter_decides_no_symptom_no_faq`,
  `::test_raw_tool_need_counts_when_the_domain_has_no_filter`,
  `::test_two_findings_for_the_same_agent_join_why_and_hint`.

## 4. O destino de cada achado fica no trace (contável)
- **O quê:** `supervisor.step_view` grava `needs` no passo que trouxe o achado: agente pedido, motivo curto
  (mascarado) e `outcome` (`supervisor.NEED_OUTCOMES`: inserted, called, reminded, ignored, planned, ran, hidden,
  blocked; sem marca, sem o campo). A marca não vai ao modelo nem ao contexto dos agentes.
- **Por quê:** §3 pede contar quantas vezes o modelo ignora o achado e onde o achado disparou (a ablação precisa).
- **Prova:** `tests/test_decided_by.py::test_who_decides_count_follows_the_engine_on_a_finding`,
  `::test_the_mark_reaches_neither_the_model_nor_the_agents_context`,
  `::test_step_a_finding_asks_for_is_the_code_in_the_table_and_the_llm_in_the_llm_engine`.

## 5. Ablação `no_needs` com semântica nova e linha do README honesta
- **O quê:** `SUPERVISOR_REPLAN=no_needs` (e `run_evals --ablate-replan --mode no_needs`) agora tira o achado do
  turno: o modelo não o recebe (`_for_model`), não há lembrete e a tabela não insere; a falha segue replanejando.
  `scripts/fill_readme.py::_needs_ablation` avisa quando os braços vieram de commits diferentes (e se os prompts eram
  os mesmos), dá o p50 também só nos casos em que o achado disparou no braço com `needs` e conta o destino dos
  achados desse braço.
- **Por quê:** §3, evidências 5 e 6 (no braço antigo o modelo ainda lia o achado; os braços eram de commits
  diferentes e o texto dizia "mesmo commit"; o p50 do split inteiro misturava casos de mesmo caminho).
- **Prova:** `tests/test_supervisor_needs_budget.py::test_llm_engine_no_needs_mode_hides_the_finding_and_does_not_remind`,
  `tests/test_cassette.py::test_needs_ablation_warns_when_the_arms_come_from_different_commits`,
  `::test_needs_ablation_gives_the_p50_where_the_finding_fired_and_what_happened_to_it`,
  `tests/test_eval_completion.py` (o braço offline continua medindo a conclusão sem o achado).
