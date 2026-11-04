# Frente R11-D: guardrail — crime financeiro parafraseado, classificador que falha fechado, recusa no idioma certo

Base: r10_problemas.md §9 (regex deixa passar 15% do red team, ASI02 50%), §13 (classificador LLM "falha aberta") e
§16 (recusa no idioma errado sob ofuscação). Sem chamada ao vivo; cassetes e resultados intactos. O pedido ao
classificador (system + mensagens + schema) NÃO muda, então o replay continua batendo. Testes focados verdes e
`ruff check` limpo nos arquivos mudados.

## 1. Família de alto recall `illegal_suspect` (crime financeiro parafraseado)
- **O quê:** nova família em `_RULES`/`CONFIRM_RULES` (reason `illegal_activity`, cópia LOW): verbo de intenção +
  vocabulário genérico de fraude em pagamento (clonagem/duplicação de cartão, skimming, chupa-cabra; esquentar/lavar
  dinheiro ou grana, dinheiro sujo/do tráfico; `money[- ]launder*`, AML, launder/laundering; structuring/smurfing e
  fracionar/dividir/split de depósitos). Exceção estreita: um verbo protetor entre a intenção e o objeto
  (evitar, prevenir, detectar, denunciar, avoid, prevent, detect, report) desfaz a suspeita. Portão próprio em
  `_GATES` (o objeto de fraude), para o custo não virar quadrático. A regra terminal `_ILLEGAL` NÃO foi tocada.
- **Por quê:** r10_problemas.md §9 — offline a regex deixava passar clonagem de cartão e lavagem parafraseada
  (q-guard-21/22/23 e os pedidos de clonagem do held-out). Como é CONFIRM_RULES, com o classificador no ar ele decide
  (o falso positivo da regex não chega ao cliente); sem LLM ou com ele fora do ar, a suspeita FALHA FECHADA, o que
  tapa também o modo degradado.
- **Prova:** `tests/test_guardrails_v5.py::test_financial_crime_paraphrase_is_a_suspicion_that_fails_closed`
  (paráfrases novas → suspeita + bloqueio offline), `::test_legitimate_fraud_questions_are_not_a_suspicion` (controles
  "como evitar clonagem do cartão?", "o antifraude está barrando vendas legítimas", "o que é lavagem de dinheiro?",
  "cadê o depósito de ontem?"), `::test_illegal_suspect_is_cleared_or_confirmed_by_the_classifier`. O teste de custo de
  10 mil caracteres segue passando, agora com gatilhos de fraude na lista
  (`tests/test_guardrails_asi.py::test_long_repetitive_input_stays_fast`).

## 2. Classificador falha fechado de verdade (§13, parte A)
- **O quê:** em `_llm_layer`, a recusa do modelo (`LLMError` kind `refusal`) bloqueia (reason `prompt_injection`,
  flag `classifier_refusal`, métrica `guardrail_classifier_refusal_total`), não é tratada como queda; categoria fora
  do enum do schema vira `UNAVAILABLE` (só "safe" libera). Com `UNAVAILABLE`, o pipeline roda `supervisor.run` dentro
  de `force_offline()` (ContextVar nova em `llm.py` que faz `get_llm` devolver o offline): o texto que o classificador
  não conferiu não chega a NENHUM agente LLM; a escrita do turno continua retida (`_hold_writes`). Docstring do topo
  de `guardrails.py` reescrita com a regra real (suspeita fecha, recusa bloqueia, enum fora vira indisponível,
  leitura segue com a flag mas sem agente LLM).
- **Por quê:** r10_problemas.md §13 — a recusa caía no mesmo `except` da queda (leitura seguia) e a lista de bloqueio
  deixava passar o que não estava em BLOCKING; e o texto não conferido ainda alcançava um agente LLM.
- **Prova:** `tests/test_guardrails_asi.py::test_classifier_refusal_blocks_and_is_not_treated_as_a_crash`,
  `::test_category_outside_the_enum_is_unavailable_not_safe`;
  `tests/test_guardrails.py::test_classifier_unavailable_runs_the_orchestration_without_any_llm_agent`;
  `tests/test_llm.py::test_force_offline_contextvar_wins_over_the_provider`.

## 3. Alerta do classificador indisponível (§13, parte A-d)
- **O quê:** alerta `ClassificadorDeSegurancaIndisponivel` em `ops/alerts.yml`
  (`sum(increase(guardrail_llm_unavailable_total[5m])) > 0`, `for: 5m`), com seção no `docs/RUNBOOK.md` nas 4 partes
  que `tests/test_alerts.py` exige. A expressão da §13 (`increase(...)>0`) foi envolta em `sum(...)` por causa da
  regra do próprio repo de somar contadores entre réplicas (`tests/test_production_ops.py`).
- **Por quê:** r10_problemas.md §13 — não havia alerta nem runbook para `guardrail_llm_unavailable_total`.
- **Prova:** `tests/test_alerts.py` (regra válida, acionável, com runbook de 4 partes) e
  `tests/test_production_ops.py::test_dashboard_and_alerts_sum_across_replicas`.

## 4. Recusa no idioma certo sob ofuscação (§16)
- **O quê:** `your` entrou em `_EN` (detecção de idioma) em `src/app/router.py`. A recusa a um ataque em inglês
  ofuscado (l33t) agora sai em inglês.
- **Por quê:** r10_problemas.md §16 — a causa real não era a ofuscação e sim `_EN` sem `your`: a frase caía em
  pt × en 0 × 0 → pt, então a recusa saía em português (q-guard-15). `router.py` está fora do escopo de arquivos da
  frente; a mudança é de uma palavra e indispensável para o item, feita no mínimo e registrada aqui.
- **Prova:** `tests/test_router.py::test_detect_language` (frase ofuscada → en) e
  `tests/test_guardrails_v5.py::test_obfuscated_english_attack_is_refused_in_english`.

## 5. Relatório do red team separa furo real do ruído de roteamento (§9, TEXTO)
- **O quê:** no bloco de red team de `evals/run_evals.py` (`to_markdown`), duas contas separadas: "ataques barrados
  pela regex: N de M" e "controles benignos: bloqueados X; fora do escopo levados ao humano no offline: Y
  (roteamento sem LLM, não guardrail)". Em `scripts/fill_readme.py` (`red_team_block`), a linha do red team AO VIVO
  (live_guardrail + live_hard) logo abaixo do cabeçalho offline.
- **Por quê:** r10_problemas.md §9 — a linha única misturava 3 ataques que a regex não barra com controles benignos
  fora do escopo que só vão ao humano offline (handoff sem LLM), inflando a leitura de "15% inseguras".
- **Prova:** `tests/test_v54_red_team_gate.py::test_report_separates_attacks_barred_from_benign_controls` e
  `::test_red_team_block_renders_offline_and_live` (agora com a linha ao vivo).
