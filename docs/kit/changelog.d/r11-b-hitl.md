# Frente R11-B: humano no laço — resposta sem contradição e split `hitl` medido no eval

Base: avaliação cega da rodada 10 (r10_problemas.md, §4 item a e §18). Nenhuma chamada ao vivo nesta frente; os
números ao vivo do split novo saem da bateria do ensaio.

## 1. Resposta com o atendente: só o CONSULTED diz se houve encaminhamento
- **O quê:** `supervisor.without_human_offer` virou `without_handoff_talk`: além da OFERTA do atendente (agora também
  "quer que eu encaminhe?", "posso encaminhar seu caso", "se quiser, abro um caso"), tira a NEGAÇÃO do encaminhamento
  ou da abertura do caso ("ele não foi encaminhado por mim", "não tenho ferramenta para abrir esse caso", "I can't
  escalate this", "o caso não foi aberto"). Negação a até 4 palavras do verbo e sem pontuação no meio; o imperativo
  ("encaminhe o terminal para a assistência") e o "caso" conjunção ("Caso o chamado não seja aberto") ficam. Ficam
  também "a decisão é de um atendente humano", a ação pendente ("o chamado ainda não foi aberto"), o "Encaminhei" e as
  negações de outra coisa ("não tenho ferramenta para cancelar o contrato").
- **Por quê:** as 3 réguas cortaram ponto na transcrição de vitrine (turno 3): "ele não foi encaminhado por mim" e, logo
  abaixo, "Consultei um atendente humano (protocolo T-dbea38c6)" (§4 a). O filtro só tirava a oferta.
- **Prova:** `tests/test_r11_hitl_eval.py::test_denial_of_the_handoff_leaves_the_answer_and_the_rest_stays` (frase
  literal da vitrine + frases a manter) e `::test_operator_turn_answer_says_once_that_the_case_went_to_the_human`
  (records com a negação → escalation → operadora no prazo, no supervisor). Conferido nas respostas ao vivo do
  ensaio (rodada 10, todos os `live_*.json`): nenhuma frase real casa com a negação; as 8 ofertas novas que o
  filtro pega são ofertas mesmo.

## 2. Resposta do operador antes de o turno começar a esperar: chega uma vez só
- **O quê:** `hitl_sync._wait` lê o caso antes de gravar o prazo; se ele já foi respondido, a retomada assíncrona já o
  levou (não havia prazo gravado quando a resposta chegou) e o turno não o leva de novo.
- **Por quê:** achado ao montar o split: o operador que responde entre a abertura do caso e o começo da espera (ao vivo,
  durante a redação final do supervisor LLM, ~2 s; na vitrine a operadora respondia 0,3 s depois de ver o caso) saía
  no turno E numa mensagem retomada (reproduzido: 1 mensagem `resumed` + a resposta no turno).
- **Prova:** `tests/test_r11_hitl_eval.py::test_answer_before_the_wait_starts_reaches_the_customer_once` (falha sem a
  correção: o turno também levava a resposta).

## 3. Split `hitl` no eval com operadora simulada e número publicado
- **O quê:** caso com `"operator": {"answer", "after_s"}` e `"wait_s"`. `evals/operator_sim.py` é a operadora comum do
  eval e da vitrine (`scripts/demo_md.py` usa a mesma, pelo console com chave pessoal; o eval, pela função do console
  depois da autenticação). A thread dela roda com `contextvars.copy_context()` (banco do caso, escopo do cassete); o
  relógio dela conta do começo da espera do turno (`sync_wait`), então `after_s < wait_s` é no turno e
  `after_s > wait_s` é atrasado. A espera vale só para o caso: `hitl_sync.override` (ContextVar, padrão None = vale o
  env), e a transcrição deixou de trocar `HITL_SYNC_WAIT_S`/`HITL_SYNC_POLL_S` do processo. Depois do turno, o
  `run_case` espera a resposta dela e lê na conversa o que a retomada entregou. Checagens novas `human_in_turn`
  (algum passo com `answered_live`, contra o
  `expect`) e `human_once` (a resposta dela chega uma vez: no turno sem retomada, ou só pela retomada); `facts` lê a
  resposta do turno + a retomada; `resolved` (sem humano) não se aplica ao caso com operadora; `not_contains` já
  existia (`no_leak`). As duas checagens entram no summarize e no bloco por split. Placar: alvo `hitl_in_turn` (casos
  que esperam a resposta no turno e a tiveram) na manchete e no "como"; no bloco `since`, ele troca o
  `resolved_fraction` (turnos SEM humano, o contrário do que a linha prova). Um caso de exemplo na fixture do kit.
  Caso mal escrito (`operator` sem `answer`, segundos que não são número) quebra na carga, antes de gastar.
- **Por quê:** régua 2: "HITL não exercitado nos evals (espera síncrona desligada, operador roteirizado)" (§18). No
  eval não havia operador nenhum, e o placar não tinha alvo de HITL.
- **Prova:** `tests/test_r11_hitl_eval.py`: no prazo → `human_in_turn_acc` 100 e o fato da operadora na resposta, sem
  retomada; atrasado → uma mensagem retomada e o fato lido dela; dois casos em paralelo → só o que tem `wait_s`
  espera; caso sem escalada → a operadora não responde; placar conta só os casos que esperam o turno.
