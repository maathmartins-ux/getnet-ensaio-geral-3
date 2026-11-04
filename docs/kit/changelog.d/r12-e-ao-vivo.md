# Frente R12-E: câmbio e clima viram tools que o LLM escolhe

Base: `r12/reguas_r11.md`, régua 1 (TOP8, item 4, Orchestration: "clima e câmbio escolhidos por um detector regex no
código, não por uma tool call do modelo") e régua 3 (item 3: "o dado ao vivo é despachado por regex"). Conferido no
kit: `_general` chamava `live_data.lookup(ctx.text)` antes de qualquer LLM; se a regex casava, o LLM só redigia o
texto da API (`_live`, prompt `live_data.md`), e a busca web só via o que a regex deixava passar. Nada rodou ao vivo.

## 1. O modelo escolhe a consulta: `currency_rate`, `weather_forecast`, a busca web ou nenhuma
- **O quê:** com LLM, `_general_llm` (src/app/agents.py) faz o pedido com duas tools de cliente, `currency_rate`
  (moeda ISO 4217 da lista da PTAX, `date` opcional AAAA-MM-DD) e `weather_forecast` (`city`; `day` hoje, amanhã ou
  depois de amanhã), ao lado da busca web do servidor. O modelo decide; o código executa a tool pelas funções de
  `live_data` (mesmas APIs, mesmo teto de tempo, segunda fonte do clima) e devolve o texto bruto da API como
  tool_result, em `<untrusted_content>`; o modelo redige na volta seguinte. `pause_turn` da busca web reenvia a volta
  sem mensagem nova. Com `LIVE_DATA=off` as duas tools saem do pedido (fica só a busca web).
- **Por quê:** as duas réguas acima. E o detector errava a pergunta fora do padrão (ensaio da rodada 11,
  `evals/results/live_heldout.json`): `heldout-H2-08` ("quanto ta a libra hoje") não casou a palavra de cotação e
  saiu "não consegui confirmar"; `heldout-H1-13` ("weather like in Recife right now") virou a cidade "Recife right" e
  foi à busca web; `heldout-H1-16` ("Bitcoin to US dollar") virou a PTAX do dólar. A tool que o modelo escolhe recebe a
  moeda e a cidade já resolvidas por ele.
- **Prova:** `tests/test_r12_live_tools.py::test_model_picks_the_fx_tool_and_the_api_gets_its_parameters`,
  `::test_model_picks_the_weather_tool_with_its_city_and_day`, `::test_web_search_for_something_else_runs_no_live_api`,
  `::test_the_regex_detector_is_not_forced_when_the_model_chooses`, `::test_answer_without_tool_calls_no_api`,
  `::test_pause_turn_resends_the_turn_without_a_new_user_message`.

## 2. Entrada validada no servidor; erro volta ao modelo como tool_result
- **O quê:** `live_args` confere o schema no código: moeda fora da lista, data fora do formato ou no futuro, campo a
  mais, cidade vazia, longa ou com caractere que mude a URL do wttr.in, dia fora dos três, tool desconhecida →
  tool_result com `is_error` e o motivo (o modelo corrige ou vai à busca web). API que falha ou volta vazia também
  vira tool_result de erro ("não invente número"). Teto de consultas ao vivo por turno (`MAX_LIVE_CALLS`).
  Normaliza o que é inequívoco ("Porto Alegre, RS", "Amanha", "today" como data, data ISO como dia).
- **Por quê:** a entrada da tool é saída do modelo: só o código decide o que vai à API (régua: "schema validado no
  servidor").
- **Prova:** `::test_invalid_input_is_an_error_tool_result_and_calls_no_api`,
  `::test_arguments_are_normalized_before_the_api`, `::test_api_failure_goes_back_to_the_model_as_an_error`,
  `::test_live_calls_per_turn_are_capped`.

## 3. O caminho do caso mostra a tool que o modelo escolheu
- **O quê:** cada tool do turno entra em `tool_calls` do passo, na ordem em que o modelo chamou (as de dado ao vivo
  com os argumentos validados; a busca web com a consulta e `ok` pelo resultado), e a árvore de passos
  (`supervisor.step_view`, docs/DEMO.md) passa a listá-las. Nos fatos do passo, `live_tool` (o que o modelo escolheu;
  `none` = respondeu sem tool), além de `live_data` e `web_search`, que continuam (`web_search` agora diz se houve
  busca de fato). Métrica `live_tool_calls_total{tool,outcome}`. O nome é `currency_rate`, não `exchange_rate`: o
  verificador de ação alegada (`grounding.claimed_actions`) lê "change" no nome de tool executada como escrita, e uma
  cotação liberaria "alterei/atualizei" no mesmo turno.
- **Por quê:** a decisão do modelo tem de ser observável no trace, não só no código.
- **Prova:** `::test_model_picks_the_fx_tool_and_the_api_gets_its_parameters` (step_view),
  `::test_supervisor_step_shows_the_tool_the_agent_model_chose` (pelo laço do supervisor LLM, como o eval grava),
  `::test_tool_names_do_not_read_as_a_write_action` (o defeito do nome `exchange_rate`, reproduzido).

## 4. Valores obrigatórios, reparo único e texto pronto continuam
- **O quê:** a resposta com dado ao vivo é conferida como antes (`live_missing` sobre `LiveResult.must`; `live_must`
  no resultado para o pipeline): faltou valor, uma volta a mais do mesmo loop pede o que faltou; ainda faltando, vale o
  texto pronto da consulta (`live_repair`: `llm` | `template`). Evidência e fonte iguais (texto bruto da API, as duas
  frases prontas, a data de hoje). Com mais de uma consulta no turno, o rótulo do valor leva a moeda ou a cidade. O LLM
  que cai depois da consulta deixa o texto pronto do que a tool trouxe (sem rodar o detector).
- **Por quê:** a checagem numérica não pode piorar com a mudança de quem escolhe.
- **Prova:** `tests/test_v55_live_repair.py` (os três testes do reparo, agora pelo loop de tools),
  `::test_two_lookups_label_the_missing_value_with_its_subject`,
  `::test_llm_down_after_the_tool_keeps_its_result_without_the_detector`.

## 5. Sem LLM, o detector por regex segue igual; `live_data` ganha a interface por parâmetro
- **O quê:** `live_data.fx_quote(moeda, data)` e `forecast(cidade, dia)` devolvem (resultado, desfecho: ok | empty |
  error | off) e são o que a tool chama; `lookup` (o detector, com o seguimento elíptico) virou o caminho do motor sem
  LLM (offline, `force_offline`, ou queda antes de qualquer dado) e chama as mesmas funções.
- **Por quê:** a régua pediu a decisão no modelo; sem modelo, o código decide como antes.
- **Prova:** `::test_without_llm_the_regex_detector_still_decides`,
  `::test_llm_down_before_any_tool_falls_back_to_the_detector`, `tests/test_live_data.py` inteiro sem mudança.

## 6. Prompts
- **O quê:** `prompts/general.md` lista as três tools e quando usar cada uma, e traz as regras da redação do dado ao
  vivo (mínima, máxima e chuva; compra e venda; fonte e data; sem conselho). Novo `prompts/contract/general.md`
  (contrato do motor): um `general.md` de domínio que só fala da busca web recebe no fim as regras das tools e dos
  valores obrigatórios. `prompts/live_data.md` saiu: a redação agora é a volta do loop, com o prompt do `general`.
- **Prova:** `::test_kit_prompt_lists_the_tools_and_a_domain_prompt_gets_the_contract`,
  `tests/test_v53_prompt_contract.py`, `tests/test_router_contamination.py`.

## Gravações
O pedido do agente geral muda (tools, prompt de sistema e as voltas do loop): todo cassete com turno de intenção
`general` deixa de casar e o split precisa ser regravado ao vivo (o replay acusa "pedido não gravado").
