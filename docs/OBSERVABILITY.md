# Observabilidade

O que o código emite hoje, onde ler e qual pergunta de operação cada sinal responde. Os valores medidos (latência,
custo, taxa de escalonamento) não ficam aqui: saem de `/metrics` em produção e de `evals/results/` na avaliação
(bloco `trace` do README, gerado por `scripts/fill_readme.py`).

## 1. Rastreio de um turno (`trace_id`)

- Cada `POST /chat` ganha um `trace_id` (`src/app/observability.py`, `new_trace_id`), devolvido na resposta
  (`ChatResponse.trace_id`, `src/app/schemas.py`) e gravado em toda linha de log do turno.
- Cada etapa roda dentro de `span(nome, **campos)`: uma linha JSON no log com `span`, `ms` e os campos (agente,
  status, papel do modelo) e uma observação no histograma `span_latency_ms{span=...}`.
- Spans emitidos pelo motor: `guardrails`, `router`, `agent`, `tool`, `llm`, `live_data`, `parallel`,
  `hitl_sync_wait`, `resume`, `resume_plan`, `resume_live`, e `turn` (o turno inteiro respondido).
- Com `OTEL_EXPORTER=console|otlp` e o extra `[otel]` instalado, o mesmo `span()` abre um span OpenTelemetry com
  `app.trace_id`; sem o extra, segue só o log (nunca derruba a API).
- Para explicar um atendimento a um lojista: filtrar o log pelo `trace_id` e ler na ordem guardrail → router
  (intent, plano, `standalone`) → cada `agent` com status → `tool` (quais tools do CRM rodaram) → resposta.
  `GET /conversations/{id}` e `GET /audit` mostram a conversa e as ações de escrita com quem aprovou.

## 2. Métricas (`GET /metrics`, formato Prometheus)

Protegido por `Bearer METRICS_TOKEN` quando definido (exigido em produção, `src/app/api.py`).

| Pergunta | Métrica |
|---|---|
| Quantos turnos, por desfecho? | `chat_requests_total` |
| Onde está a latência? | `span_latency_ms_bucket{span=...}` (p95 por etapa no Prometheus) |
| Quanto custa? | `llm_tokens_total`, `llm_cost_usd_total`, `llm_unpriced_calls_total` |
| O provedor está falhando? | `llm_errors_total`, `supervisor_fallback_total`, `router_fallback_total` |
| O plano se adaptou ao resultado? | `replans_total`, `supervisor_handover_total`, `plan_resumed_total` |
| O humano está sendo chamado demais ou de menos? | `hitl_sync_total`, `handoff_notifications_total`, `handoff_resumed_total`, `sla_escalations_total` |
| A busca degradou? | `retriever_fallback_total`, `rerank_fallback_total`, `poisoned_docs_dropped_total` |
| As tools do CRM e de dado ao vivo estão sãs? | `tool_calls_total`, `tool_args_invalid_total`, `live_tool_calls_total`, `live_data_total` |
| Escrita segurada sem aprovação? | `writes_held_total`, `risk_flags_total` |
| O router reescreveu algo inventado? | `router_standalone_rejected_total`, `router_search_query_rejected_total`, `router_own_company_total` |
| Guardrail sem classificador? | `guardrail_llm_unavailable_total` |
| Limite de taxa? | `rate_limited_total`, `rate_limit_store_errors_total` |
| Memória usada / apagada (LGPD)? | `user_memory_used_total`, `privacy_deletions_total` |
| A réplica está pronta? | `ready_failures_total`; `GET /ready` devolve 503 com o motivo (índice, banco, LLM, orçamento) |

## 3. Painéis e alertas

- Prometheus: `ops/prometheus.yml` (perfil `observability` do `docker-compose.yml`); versão endurecida em
  `ops/prometheus.hardened.yml`.
- Grafana: `ops/grafana/dashboards/support.json` (latência p95 por etapa, turno p50/p95 × SLO, custo, escalonamento).
- Alertas: `ops/alerts.yml`. Cada regra tem `runbook_url` para o bloco de mesmo nome em `docs/RUNBOOK.md`;
  `tests/test_alerts.py` reprova regra sem bloco.

## 4. Qualidade (fora do caminho do turno)

- `GET /analytics` agrega intents, escalonamentos e feedback (`src/app/analytics.py`); `POST /feedback` registra
  a nota do lojista ligada ao `trace_id`.
- Avaliação offline e ao vivo: `python -m evals.run_evals --split <split>`; resultados em `evals/results/`.
- Versão de cada prompt usada no turno vai para o log (`record_prompt`, `prompt_versions`): uma regressão é
  ligada à mudança de prompt que a causou.
