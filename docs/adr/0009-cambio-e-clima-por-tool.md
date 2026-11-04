# ADR 0009 — Câmbio e clima: o modelo escolhe a tool; o detector por regex só sem LLM

Status: aceito no kit v5.5.3 (04/11/2026). Complementa o ADR 0005 (a decisão de cada passo fica com o modelo e
aparece no trace).

**Contexto.** A pergunta geral com dado ao vivo (câmbio, clima) passava por um detector por regex no código
(`live_data.lookup`) antes de qualquer LLM: se a regex casava, a API era consultada e o modelo só redigia o texto dela;
se não casava, a pergunta ia à busca web. A decisão de consultar a API não aparecia no trace como tool call, e o
detector errava paráfrases (bateria ao vivo do kit v5.5.2): a pergunta sem a palavra de cotação ia à busca web e saía
sem o dado; a cidade era lida junto com a palavra seguinte; uma cotação de Bitcoin virou a PTAX do dólar.

**Decisão.**
- Com LLM, o agente geral (`agents._general_llm`) faz o pedido com duas tools de cliente ao lado da busca web do
  servidor: `currency_rate` (PTAX do Banco Central; moeda ISO 4217 da lista da PTAX e data opcional) e
  `weather_forecast` (Open-Meteo, com o wttr.in de segunda fonte; cidade e dia). O modelo escolhe uma delas, a busca
  web ou nenhuma.
- O código valida a entrada (`agents.live_args`: moeda fora da lista, data no futuro, campo a mais, cidade com
  caractere que mude a URL, dia fora dos três) e devolve o erro como tool_result de erro, para o modelo corrigir ou ir
  à busca web; consulta a API (`live_data.fx_quote`, `live_data.forecast`, as mesmas que o detector chama), com teto
  de consultas por turno (`MAX_LIVE_CALLS`), e devolve o texto bruto da API como tool_result, em `<untrusted_content>`.
- A resposta com dado ao vivo segue conferida em código: faltou um valor obrigatório (mínima, máxima e chuva; compra e
  venda), uma volta a mais pede o que faltou; ainda faltando, vale o texto pronto da consulta (`live_repair`).
- Sem LLM (offline, ou queda antes de qualquer dado), o detector por regex escolhe a consulta, como antes.

**Alternativas.**
- *Detector antes do LLM* (como era): uma chamada de modelo a menos, mas a decisão fica fora do trace e erra a
  pergunta fora do padrão.
- *Só a busca web*: o corpo das páginas vem cifrado e só as citações são conferíveis; a cotação ou a previsão que a
  citação não traz fica como número sem base na checagem numérica.

**Consequências.**
- Uma chamada de modelo a mais por pergunta de câmbio ou clima: uma volta escolhe a tool, a seguinte redige.
- A decisão aparece na árvore de passos: cada tool chamada, na ordem, com os argumentos validados (`tool_calls`), e o
  fato `live_tool` do passo; `/metrics` conta `live_tool_calls_total` por tool e desfecho.
- A escolha é do modelo: pergunta de câmbio ou clima respondida sem tool fica sem dado ao vivo, e a checagem numérica
  marca o número sem base.
- `LIVE_DATA=off` (APIs bloqueadas na rede) tira as duas tools do pedido; fica a busca web.
- O nome é `currency_rate`, não `exchange_rate`: o verificador de ação alegada (`grounding.claimed_actions`) lê
  "change" no nome de tool executada como escrita, e uma cotação liberaria "alterei"/"atualizei" no mesmo turno.
- O pedido do agente geral mudou (tools, prompt e voltas do laço): as gravações de turno de intenção `general` precisam
  ser regravadas antes de medir.

**Números.** Não ficam escritos aqui: a checagem numérica (`numbers_acc`) e o custo por split saem dos blocos gerados
do `docs/RESULTS.md`. Prova por teste:
`tests/test_r12_live_tools.py::test_model_picks_the_fx_tool_and_the_api_gets_its_parameters`,
`tests/test_r12_live_tools.py::test_invalid_input_is_an_error_tool_result_and_calls_no_api`,
`tests/test_r12_live_tools.py::test_supervisor_step_shows_the_tool_the_agent_model_chose`,
`tests/test_r12_live_tools.py::test_tool_names_do_not_read_as_a_write_action`,
`tests/test_r12_live_tools.py::test_without_llm_the_regex_detector_still_decides` e o reparo dos valores obrigatórios,
`tests/test_v55_live_repair.py::test_incomplete_answer_is_redone_once_with_what_was_missing`.
