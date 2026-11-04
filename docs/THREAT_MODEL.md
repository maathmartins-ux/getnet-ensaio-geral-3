# Modelo de ameaças — atendimento Getnet (lojista)

Escopo: `/chat`, `/mcp` (mesma identidade e mesma cota do `/chat`), console do operador (fila HITL), `/metrics`,
tools do Customer Support (`get_transactions`, `get_settlements`, `get_terminals`, `open_support_ticket`,
`request_receivables_advance`), RAG sobre o corpus público e o agente geral (`weather_forecast`, `currency_rate`,
`web_search`). Ativos: dado do lojista no CRM (vendas, recebíveis, terminais), credenciais (token, `OPERATOR_KEYS`,
chave do LLM), ações de escrita (chamado, antecipação). Fronteiras de confiança: cliente → API; API → LLM; API →
web/fontes ao vivo; operador → console. Casos de ataque: split `guardrail` de `evals/cases.d/q.jsonl` (campo `asi`).

Formato de cada linha: ameaça → controle → arquivo → teste.

## STRIDE

| | Ameaça | Controle | Arquivo | Teste |
|---|---|---|---|---|
| S | Forjar identidade pelo `user_id` do corpo | identidade só do Bearer em `required`; produção recusa `AUTH_MODE=demo` | `src/app/api.py`, `src/app/auth.py` | `tests/test_api.py::test_production_refuses_demo_identity`, `tests/test_domain_http.py::test_body_user_id_cannot_override_token_identity` |
| S | Token adulterado ou de outra chave | assinatura e `kid` conferidos; inválido = 401, nunca 500 | `src/app/auth.py` | `tests/test_domain_http.py::test_bad_token_is_401_in_both_modes`, `tests/test_key_rotation.py::test_algorithm_confusion_is_rejected` |
| T | Alterar a trilha de decisões do operador | log de auditoria só de acréscimo | `src/app/store.py` | `tests/test_privacy.py::test_audit_log_is_append_only` |
| R | Negar ter aprovado antecipação | aprovação nominal por chave pessoal de `OPERATOR_KEYS`, auditada | `src/app/actions.py`, `src/app/api.py` | `tests/test_privacy.py::test_operator_reply_is_audited` |
| R | Risco alto aprovado com token compartilhado | token compartilhado (só fora de produção) lê a fila, responde e rejeita; 403 ao aprovar | `src/app/actions.py` | `tests/test_hitl.py::test_high_risk_action_needs_owner_then_operator_and_runs_once` |
| I | Ler dado de outro lojista (`cliente2024`) | pedido explícito recusado na entrada com a frase neutra de toda recusa (SPEC, RN-03); 2ª camada: o dono vem do servidor e a tool só lê a conta do login (o resto = "não encontrado") | `src/app/guardrails.py`, `src/app/domain/challenge/tools.py`, `src/app/tools.py` | `tests/test_domain_guardrails.py::test_other_merchant_by_id_is_refused_at_the_entry`, `tests/test_domain_guardrails.py::test_tool_reads_only_the_logged_in_account`, `tests/test_api.py::test_conversation_of_other_user_is_forbidden`, split `guardrail` (categoria `outro_cliente`, `owasp` ASI03) |
| I | `/metrics` expondo volume e erros | Bearer em produção | `src/app/api.py` | `tests/test_api.py::test_production_refuses_shared_operator_and_open_metrics` |
| D | Inundar `/chat` ou `/mcp` | limite por identidade verificada (ou IP), cota comum | `src/app/auth.py`, `src/app/mcp_server.py` | `tests/test_api.py::test_rate_limit`, `tests/test_mcp.py::test_mcp_tools_share_the_chat_rate_limit` |
| E | Executar antecipação sem humano ("aprove sem atendente") | `risk: high` vira ação pendente; só o operador executa | `src/app/actions.py` | split `approval`/`guardrail` (`pending_action: true`), `tests/test_domain_guardrails.py::test_spec_rules_other_customer_is_refused_and_approval_is_pending` |

## OWASP Top 10 para LLM (2025)

| ID | Ameaça | Controle | Arquivo | Teste |
|---|---|---|---|---|
| LLM01 | Injeção direta, indireta (e-mail, PDF, página colada) e ofuscada | regex + desofuscação (espaço, invisível, NFKC) + classificador; conteúdo de fonte é dado, nunca instrução | `src/app/guardrails.py` | `tests/test_domain_guardrails.py::test_literal_injection_is_blocked_offline`, split `guardrail` |
| LLM02 | Vazamento de dado sensível (PII, cartão) | máscara de PII na entrada e na saída | `src/app/guardrails.py` | `tests/test_guardrails.py` |
| LLM03 | Cadeia de suprimentos | actions por SHA, SBOM e varredura | `.github/workflows/` | `tests/test_supply_chain.py::test_every_action_is_pinned_by_commit_sha_with_version_comment` |
| LLM04 | Envenenamento do corpus | ingestão só de hosts permitidos, trecho com hash | `src/app/ingest.py`, `data/sources.json` | `tests/test_domain_corpus.py::test_corpus_is_literal_sized_hashed_and_from_allowed_hosts` |
| LLM05 | Saída tratada sem validação | resposta é texto; ação só por tool com schema | `src/app/tools.py` | `tests/test_risk_policy.py::test_args_outside_the_schema_never_become_a_proposal` |
| LLM06 | Agência excessiva | escrita com confirmação; risco alto com aprovação humana | `src/app/actions.py` | `tests/test_hitl.py::test_high_risk_action_needs_owner_then_operator_and_runs_once` |
| LLM07 | Vazamento do prompt de sistema | pedido de prompt barrado; `not_contains` nos casos | `src/app/guardrails.py` | split `guardrail` (q-guard-01, q-guard-04) |
| LLM08 | Fraqueza de embedding/busca | citações obrigatórias; parcial diz o que falta | `src/app/rag.py`, `src/app/grounding.py` | split `partial` |
| LLM09 | Desinformação (número inventado, fonte velha) | grounding de números; dado ao vivo com data; juiz calibrado por tipo de defeito | `src/app/grounding.py`, `evals/judge.py` | `evals/judge_calibration.d/q.jsonl` |
| LLM10 | Consumo sem limite | teto de US$ no eval, limite de taxa | `evals/run_evals.py`, `src/app/auth.py` | `tests/test_api.py::test_rate_limit` |

## OWASP Agentic (ASI01–ASI10)

| ID | Ameaça | Controle | Arquivo | Teste |
|---|---|---|---|---|
| ASI01 | Sequestro do objetivo do agente (injeção, jailbreak) | guardrail antes do router; mensagem bloqueada não entra na memória | `src/app/guardrails.py`, `src/app/pipeline.py` | `tests/test_security_asi.py::test_blocked_message_is_never_remembered`, split `guardrail` (`asi: ASI01`) |
| ASI02 | Uso indevido de tool (estorno, troca de cadastro, pagamento) | só as 5 tools da SPEC; fora de escopo vai ao humano | `src/app/domain/challenge/tools.py` | split `guardrail` (`fora_de_escopo`) |
| ASI03 | Abuso de identidade e privilégio | identidade do servidor, nunca no schema da tool | `src/app/tools.py`, `src/app/mcp_server.py` | `tests/test_mcp.py::test_crm_tool_identity_comes_from_token_and_write_needs_confirmation` |
| ASI04 | Cadeia de suprimentos agêntica (MCP, modelos) | MCP com o mesmo Bearer; dependências fixadas | `src/app/mcp_server.py` | `tests/test_mcp.py::test_anonymous_gets_401_before_the_protocol` |
| ASI05 | Execução de código inesperada | nenhum eval/exec no app | `src/app/` | `tests/test_security_asi.py::test_no_dynamic_code_execution_in_the_app` |
| ASI06 | Envenenamento de memória e contexto | bloqueado não é lembrado; perfil por usuário | `src/app/memory.py` | `tests/test_security_asi.py::test_blocked_message_is_never_remembered` |
| ASI07 | Comunicação insegura entre agentes | supervisor passa dado estruturado, especialistas sem estado | `src/app/supervisor.py` | `tests/test_v54_stateless_specialists.py` |
| ASI08 | Falha em cascata | queda do LLM cai na tabela determinística; não encontrado escala | `src/app/pipeline.py` | `tests/test_v54_not_found_escalates.py` |
| ASI09 | Exploração da confiança humana (fraude, lavagem, ameaça) | `blocked` para fraude/lavagem/abuso; aprovação humana mostra o pedido como veio | `src/app/guardrails.py`, `src/app/actions.py` | split `guardrail` (`lavagem`, `fraude`, `abuso`) |
| ASI10 | Agente fora de controle (aprova sozinho) | nenhuma ação de risco alto roda sem operador; executa uma vez | `src/app/actions.py` | `tests/test_hitl.py::test_high_risk_action_needs_owner_then_operator_and_runs_once` |

## Decisão: dado de outro lojista (SPEC, RN-03)
O pedido explícito de dado de outro lojista ("vendas do cliente2024", "a loja do cliente2024") é recusado na entrada,
antes de qualquer tool, pela regex do motor ou pelo guardrail LLM. A recusa usa a mesma frase de toda recusa e vale
para qualquer id citado, exista o lojista ou não: não revela se o registro existe nem de quem é. A 2ª camada fica: o
que escapar da entrada chega à tool, que só lê a conta do login e responde "não encontrado". O cliente que pede uma
ação da própria conta "sem humano" não é recusado: a ação fica pendente, com confirmação e aprovação humana.
