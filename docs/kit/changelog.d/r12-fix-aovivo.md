# Frente R12-fix-aovivo: teto, data, detector e repetição nas tools de câmbio e clima

Base: revisão adversarial da rodada 12 sobre a frente R12-E (área ao vivo), quatro achados confirmados por um cético
com sondas sem rede nem LLM (LLM falso de `tests/fakes.py`, `live_data._get_json` trocado). Conferido no código do
ramo `r12/int` (`agents._live_tool_result`, `live_args`, `_general`; `live_data.weather`). Nada rodou ao vivo.

## 1. O teto de consultas ao vivo conta só as que foram à API
- **O quê:** `_Turn.live` conta as consultas que passaram por `live_args` e foram a `live_data`; o teto
  `MAX_LIVE_CALLS` olha esse número. Entrada recusada e consulta repetida ficam no caminho do caso (`tool_calls`) e
  fora do teto. A recusa do teto diz "Sem consulta: o limite ... já foi usado" (antes, "Entrada inválida"), com
  `live_tool_calls_total{outcome="limit"}`.
- **Por quê:** o teto somava toda ToolCall do turno, inclusive as recusadas e as próprias recusas do teto. "Dólar,
  euro e libra em 30/10" com a data no formato errado na 1ª volta saía com 0 consultas à PTAX e a resposta sem o
  dado; com 1 data errada, a libra era recusada depois de 2 consultas reais.
- **Prova:** `tests/test_r12_live_tools.py::test_refused_inputs_do_not_use_up_the_live_call_cap` (3 e 1 datas
  erradas, depois as 3 moedas: 3 consultas, 6 valores obrigatórios), `::test_live_calls_per_turn_are_capped`.

## 2. Data AAAA-MM-DD no `day` do clima vale como data, conferida no fuso da cidade
- **O quê:** `live_args` não converte mais a data em "hoje/amanhã/depois de amanhã" contra o dia do negócio: a data
  segue nos argumentos (só sai a que nenhum fuso aceita, a mais de 1 dia da janela). `live_data.forecast(cidade,
  on=data)` leva a data até `weather`, que, depois do geocoding, confere a janela contra o "hoje" no fuso da CIDADE e
  pede à API esse dia; fora dos três dias da cidade, sem dado ("não trouxe o dia pedido"). O wttr.in escolhe o dia
  pela data, não pela posição. Pedida por data, a frase pronta traz só a data ("em 05/11/2026"), sem o "hoje" da
  cidade, que pode ser o "amanhã" do cliente.
- **Por quê:** a data virava deslocamento contra `clock.today()` (São Paulo) e o clima somava esse deslocamento ao
  "hoje" da cidade: às 14h de SP (02h do dia seguinte em Tóquio), "2026-11-05" trazia a previsão de 06/11; Los Angeles
  de madrugada em SP trazia o dia anterior.
- **Prova:** `::test_iso_day_is_the_date_asked_in_the_city_timezone` (Tóquio, Los Angeles e Porto Alegre com o
  relógio fixo), `::test_iso_day_outside_the_city_window_calls_no_forecast`,
  `::test_second_weather_source_picks_the_day_by_date`, `::test_arguments_are_normalized_before_the_api`.

## 3. O detector por regex não responde por cima do modelo
- **O quê:** com LLM, o detector (`live_data.lookup`) só roda se o LLM caiu antes de o modelo chamar qualquer tool.
  Se o modelo já escolheu (tool recusada, busca web) ou o LLM seguia no ar (voltas esgotadas, texto vazio), o turno
  sem dado sai com a resposta honesta, as tools do turno em `tool_calls`, os fatos do turno (`web_search`,
  `live_tool`) e o que a busca trouxe na evidência (`agents._general_no_data`).
- **Por quê:** bastava não haver dado no fim do loop para o detector rodar. "Bitcoin to US dollar": o modelo pedia BTC
  (recusado), ia à busca web, o LLM caía, e o detector respondia a PTAX do dólar, com `web_search` False e as tools
  do modelo fora do caminho do caso (o heldout-H1-16 da rodada 11 de volta, pelo caminho de queda).
- **Prova:** `::test_the_detector_does_not_answer_over_the_model` (BTC recusado → busca web → queda; voltas esgotadas;
  texto vazio), `::test_llm_down_before_any_tool_falls_back_to_the_detector` (o caminho de queda que fica).

## 4. Consulta repetida entra uma vez
- **O quê:** `_Turn.seen` guarda o tool_result por (tool, argumentos validados); a mesma consulta de novo no turno
  devolve o mesmo resultado, sem ir à API e sem entrar de novo em `got` (texto pronto e valores obrigatórios). O
  caminho do caso mostra a repetição; `live_tool_calls_total{outcome="repeat"}`.
- **Por quê:** o modelo repetia na volta do reparo a mesma consulta e ela entrava duas vezes: o texto pronto saía com
  a frase em dobro e os valores obrigatórios com rótulos repetidos.
- **Prova:** `::test_a_repeated_lookup_enters_the_turn_once`, `::test_a_repeated_lookup_does_not_use_up_the_cap`.

## Gravações
O pedido ao LLM não muda no caminho comum (tools, prompt e tool_result iguais). Muda só nos caminhos dos achados: a
recusa do teto tem outro texto, a consulta repetida volta igual à primeira e a frase pronta do clima pedido por data
traz só a data. Não há cassete do agente geral no kit.
