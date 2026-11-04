# ADR 0012 — Considerado e não feito no desafio Getnet (com o gatilho para revisitar)

Status: registrado (desafio Getnet). Complementa o ADR 0008 (decisões do kit).

| Considerado | Por que não agora | Gatilho para revisitar |
|---|---|---|
| Busca web aberta para perguntas sobre produtos Getnet quando a base não cobre | a resposta passaria a vir de fonte não oficial (blog, fórum, concorrente) sobre tarifa e prazo; a SPEC manda `insufficient` → humano. A busca web fica só no agente geral (`web_search`) e o router impede `general` sobre a própria Getnet (`_own_company_guard`) | a fração de `insufficient` no split `replan` ou em `evals/real_questions.jsonl` (perguntas reais) ficar alta em assuntos que existem no site oficial: aí o caminho é ampliar `data/sources.json`, não abrir a web |
| Contestação de chargeback por API (`TX1006` contestável) | fora de escopo na SPEC: vai ao humano | a Getnet expor uma API de contestação com idempotência e trilha de auditoria; entraria como escrita `risk: high` (ADR 0011) |
| Simulação da taxa de antecipação no chat | a taxa depende da negociação do lojista e não está na fonte; official-06 aceita resposta `partial` que explica as modalidades | uma tool de taxa contratada no CRM; até lá, inventar taxa é o erro mais caro |
| Tool de status do chamado técnico (`get_ticket`) | o CRM fictício da SPEC não tem chamados abertos; seria tool sem dado para testar | casos reais de "e o meu chamado?" aparecerem nas perguntas reais ou no held-out |
| Detecção de idioma por modelo dedicado | pt e en cobrem o enunciado; o router decide por votos de vocabulário (`router.detect_language`) e a saída é forçada no idioma do cliente (`pipeline._fix_language`) | lojista em espanhol (Getnet atua no Mercosul) ou taxa de `wrong_language` acima de zero em `evals/results/` |

**Decisão.** Nenhum dos itens entra nesta entrega. Cada gatilho é observável num arquivo de resultado ou numa
mudança de contrato externo, para a decisão ser revista por medida e não por opinião.
