# Spec — Getnet Multi-Agent Support System

Commitada antes de qualquer código do domínio. Congelada (OWNERSHIP.json): mudança aqui é decisão da sessão principal.

## Problema
Lojistas da Getnet escrevem em português ou inglês sobre produtos (maquininhas, Pix, Link de Pagamento, crediário,
antecipação, Get Conta), sobre os próprios dados (vendas, recebimentos, terminais, recusas) e sobre assuntos gerais
(clima, câmbio). Um Router decide qual agente (ou sequência) atende; o Knowledge responde com RAG sobre o site oficial;
o Customer Support lê o dado do cliente por tools; um agente geral usa tools de dado ao vivo; um humano entra quando o
sistema não resolve com confiança.

## Requisitos

| ID | Requisito (do enunciado) | Módulo | Teste / eval |
|---|---|---|---|
| FR-01 | Router: entrada única, decide agente ou sequência | `src/app/router.py`, `src/app/domain/challenge/flow.py` | `tests/test_domain_router.py`, split `official`/`replan` |
| FR-02 | Knowledge: RAG sobre o site da Getnet + busca web para o geral | `src/app/rag.py`, `data/sources.json` | `scripts/official_check.py`, `evals/retrieval.d/` |
| FR-03 | Customer Support com ≥ 2 tools que leem o dado do cliente | `src/app/domain/challenge/tools.py` | `tests/test_tools.py` |
| FR-04 | `POST /chat` com `{message, user_id}` → JSON | `src/app/api.py` | `tests/test_domain_http.py` |
| FR-05 | 4º agente: escalonamento humano (fila, operador, retomada do plano) | `src/app/hitl_sync.py` | split `hitl` |
| FR-06 | Guardrails (inseguro, irrelevante, sensível, sem suporte) | `src/app/guardrails.py` | split `guardrail` |
| NFR-01 | Sobe com um comando (Docker) | `Dockerfile` | `scripts/check.py --docker` |
| NFR-02 | Funciona sem chave de LLM (modo offline) | `config.py` | CI |
| NFR-03 | Identidade: `AUTH_MODE` required em produção; demo só no compose de demonstração (ADR 0001) | `api.py` | `tests/test_auth_modes.py` |

## Cenários de aceite (copiados do enunciado, um por linha)

Todos em inglês: a resposta sai em inglês. `facts` = regex sem caixa (uma por fato de referência) em
`evals/cases.jsonl`, escritas antes do código; `entities` = produtos citados.

| ID | Mensagem | Intent / agentes / tools | Handoff | Fatos de referência (resumo) | Entidades |
|---|---|---|---|---|---|
| official-01 | What's the difference between the Get Clássica and the Get Smart? | knowledge / faq | não | um recurso da Get Smart (Android, apps, estoque, nota fiscal) e um dado da Get Clássica da página dela (taxa de crédito, para quem é: CPF e CNPJ, máquina grátis a partir de R$ 10 mil/mês, recebimento em 2 dias), lado a lado | Get Clássica, Get Smart |
| official-02 | What's the weather forecast in Porto Alegre tomorrow? | general / `weather_forecast` | não | temperatura em °C | — |
| official-03 | When will the money from yesterday's sales be deposited? | support / records / `get_settlements` | não | valores em R$ do CRM e datas de depósito por modalidade (Pix D+0, débito D+1 útil, crédito no plano de recebimento do lojista no CRM: 30 dias) | — |
| official-04 | Do I need a bank account to receive my sales via Pix? | knowledge / faq | não | 1ª frase com sim/não; o requisito da fonte (chave Pix ligada à conta de recebimento / domicílio bancário) e a Get Conta como opção gratuita | Pix |
| official-05 | My card machine won't connect to the internet, what should I do? | troubleshoot / records (`get_terminals`) → faq pelo achado `needs` | não | qual terminal está offline (do CRM) + passo do manual (chip, wi-fi, reiniciar) | — |
| official-06 | How does receivables advance (antecipação) work with Getnet? | knowledge / faq | não | o mecanismo: canal (app Getnet Brasil, Central, POS) ou modalidade (automática, eventual) e a cobrança (sem taxa além das existentes: aluguel, MDR, taxa de antecipação); não abre com a política de ações do assistente | Antecipação |
| official-07 | What's the euro exchange rate today? | general / `currency_rate` | não | valor em R$ e fonte PTAX/Banco Central | — |
| official-08 | My card machine is showing a transaction decline error. | troubleshoot / records (`get_transactions`) → faq pelo achado | não | códigos 51/05 e significado (saldo, emissor) calculados pela tool; não afirma falta de manual sobre assunto não perguntado | — |
| official-09 | How many installments can I split a sale into with the crediário? | knowledge / faq | não | até 48 parcelas | Crediário |
| official-10 | Can I sell through WhatsApp using the Payment Link? | knowledge / faq | não | outros canais do link (redes sociais, e-mail, SMS) | Link de Pagamento |

Cada AC vira um caso `official-NN` em `evals/cases.jsonl`. Nenhum dos 10 escala quando a fonte tem o fato.

## Taxonomia de intenções

| Intent | Plano | Quando |
|---|---|---|
| `knowledge` | `["faq"]` | produto, taxa, prazo, regra, funcionamento da Getnet (o "como funciona", "preciso de...?") |
| `support` | `["records"]` | dado do próprio cliente: vendas, recebimentos, agenda, terminais, status de chamado |
| `troubleshoot` | `["records"]` (+ `faq` pelo achado `needs`) | sintoma de máquina/transação: "não conecta", "erro", "recusada" |
| `general` | `["general"]` | clima, câmbio, assunto geral com dado ao vivo (tools `weather_forecast`, `currency_rate`, `web_search`) |
| `multi` | partes em paralelo | duas perguntas de assuntos diferentes no mesmo turno (ex.: produto + dado da conta, ou câmbio + produto) |
| `human_request` | `["escalation"]` | o cliente pede pessoa/atendente |
| `blocked` | — | injeção, jailbreak, pedido de dado de outro lojista (RN-03), fraude/lavagem, abuso |

## Desempates (o router aplica nesta ordem)
1. Pedido explícito de humano → `human_request` (mesmo junto de outra pergunta: a outra parte roda e o humano entra).
2. Ataque/abuso/fraude → `blocked`.
3. Sintoma de máquina ou transação (não conecta, erro, recusa, travou) → `troubleshoot`, mesmo com "o que fazer?".
4. Dado do próprio cliente (minhas vendas, meu dinheiro, meu terminal, ontem, quanto) → `support`.
5. "Preciso de / como funciona / posso / quantas parcelas" sobre produto → `knowledge`.
6. Duas perguntas sobre o MESMO produto = `knowledge` (não multi).
7. Clima, câmbio, notícia → `general`; pergunta sobre a própria Getnet nunca é `general`.
8. Seguimento curto ("e a outra?", "and how much?") herda a entidade da última resposta; se pergunta ESTADO/DADO de
   terminal ou transação ("está online?", "há quanto tempo?", "e o outro?"), é `support` mesmo depois de troubleshoot.

## Resposta parcial
O Knowledge tem três estados: `ok`, `partial` (responde o que a fonte cobre e diz o que falta; NÃO escala por si),
`insufficient` (nada coberto → oferece humano). Parcial aceitável nos oficiais: official-01 se faltar um recurso
de um dos lados (responde o que tem dos dois); official-06 se a taxa exata não estiver na fonte (explica canais,
modalidades e cobrança e diz que a taxa depende da negociação). `expect.handoff: false` em todos os oficiais.

## Pergunta autônoma (`standalone`)
O router reescreve cada seguimento como pergunta completa e autônoma, no idioma do cliente, em `ctx.facts["standalone"]`
("e a outra?" depois da Get Smart → "Quanto custa a Get Clássica?"); vazia se não der para reescrever sem inventar.
O Knowledge busca com ela. Casos `memory` trazem `standalone` e `expects_fact`.

## Tools do Customer Support (nomes congelados)

| Tool | Tipo | Devolve |
|---|---|---|
| `get_transactions(period)` | leitura | vendas e recusas do cliente (código e significado da recusa calculados), totais |
| `get_settlements(period)` | leitura | agenda de recebimentos por modalidade, datas calculadas (Pix D+0, débito D+1 útil, crédito pelo plano de recebimento do lojista: 2 dias úteis ou 30 dias), totais |
| `get_terminals()` | leitura | terminais do cliente, status, conexão, sinal, `offline_for_hours` só se offline; emite `needs` → faq |
| `open_support_ticket(terminal_id, reason)` | escrita, confirmação | chamado técnico |
| `request_receivables_advance(amount)` | escrita, `risk: high`, aprovação humana | pedido de antecipação |

Identidade sempre do servidor (nunca no schema). Registro que não é da conta do login = "não encontrado"
(indistinguível de um id inexistente).

**RN-03 — dado de outro lojista (comportamento escolhido: recusar na entrada).** Pedido explícito de dado de outro
lojista (por id, nome ou "a outra loja" que não é do cliente) é recusado pelo guardrail antes de qualquer tool, com a
mesma frase neutra de toda recusa ("não posso atender a esse pedido"), sem dizer se o outro existe (ASI03). Por quê:
nenhuma consulta roda com a intenção de ler outra conta, a recusa não depende do modelo e é a mesma para lojista
existente e inexistente. A 2ª camada fica: o que escapar da entrada chega à tool, que só lê a conta do login e
responde "não encontrado". O cliente que pede uma ação da PRÓPRIA conta "sem humano" não é bloqueado: a ação fica
pendente, com confirmação e aprovação humana mantidas. Prova: `tests/test_domain_guardrails.py`.

**Prazo de recebimento.** O site oferece receber o crédito em 2 dias, em 30 dias ou mês a mês, e anuncia
"recebimento em 2 dias úteis" com a Get Conta. O CRM guarda o plano de cada lojista (`credit_plan`); os dois lojistas
fictícios estão no de 30 dias, por isso a agenda deles mostra o crédito em D+30.
`period` com enum `today|yesterday|last_7_days|last_30_days` e padrão `last_7_days`.

## Fora de escopo
- Pagamento real, alteração cadastral, contestação de chargeback por API (vai ao humano).
- Recomendação financeira personalizada.

## Divisão em forks

Ver OWNERSHIP.json. Contrato: `src/app/schemas.py` (inclui `RouterDecision` e `AgentName`), assinatura de
`pipeline.handle(req, user_id, identity_verified)` e status `ok|insufficient|error` dos agentes.

## CRM fictício (contrato para a frente T e para os casos)

`cliente1988` (loja do Matheus): terminais `T1988A` (Get Smart, online, wi-fi) e `T1988B` (Get Clássica, offline,
chip, sem sinal há algumas horas). Vendas de ontem por modalidade (Pix, débito, crédito; uma delas `TX1002`, crédito
de R$ 480,00), recusas de hoje `TX1007` (crédito R$ 210,00, código 51 = saldo/limite insuficiente) e `TX1008`
(débito R$ 75,00, código 05 = não autorizada pelo emissor), venda `TX1006` contestável. Datas relativas a hoje
(`app.clock`). `cliente2024`: outro cliente, com um terminal online e vendas próprias (para o teste de isolamento:
o pedido de dado dele é recusado na entrada, RN-03; a tool, chamada pela conta do `cliente1988`, não o enxerga).

## Splits de avaliação escritos na SPEC (`evals/cases.d/m.jsonl`)

| Split | n | O que mede |
|---|---:|---|
| replan | 20 | 10 sem fonte (Knowledge `insufficient` → humano, `replanned`) + 10 troubleshoot em que o achado `needs` da tool chama o faq |
| dependent | 10 | a resposta só fica completa com records E faq (`must_include_agents`) |
| parallel | 5 | duas perguntas de assuntos diferentes (`multi`) |
| approval | 5 | escrita com confirmação/aprovação (`pending_action`), inclusive "aprove sem humano" = pendente |
| hitl | 6 | operador simulado no prazo (4, um com `after_human: ["records"]`) e atrasado (2) |
| memory | 16 | seguimentos com `standalone` e `expects_fact`; 2 entre conversas (`earlier_conversations`) |
